import asyncio
import json
import logging
from urllib.parse import quote

import httpx
from httpx_sse import aconnect_sse

from config import get_config
from tcp_sender import encode_zpl, decode_pdf, send_tcp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("print-service")

# Track SSE connection status for /health
_sse_connected = False


async def authenticate(client: httpx.AsyncClient, config) -> str:
    resp = await client.post(
        f"{config.api_url}/auth",
        data={"username": config.username, "password": config.api_password},
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    logger.info("Authenticated with API")
    return token


async def handle_job(client: httpx.AsyncClient, config, job: dict, token: str) -> None:
    job_id = job["job_id"]
    printer_host = job["printer_host"]
    printer_port = job.get("printer_port", 9100)
    fmt = job["format"]
    data_str = job["data"]
    copies = job.get("copies", 1)
    timeout = job.get("timeout_seconds", 5.0)

    logger.info(f"Job {job_id}: {fmt} -> {printer_host}:{printer_port} (copies={copies})")

    # Encode data to bytes
    try:
        if fmt == "zpl":
            data_bytes = encode_zpl(data_str, mode=config.non_ascii)
        elif fmt == "pdf":
            data_bytes = decode_pdf(data_str)
        else:
            result = {"ok": False, "error": "send_error", "detail": f"Unknown format: {fmt}"}
            await report_result(client, config, job_id, result, token)
            return
    except ValueError as e:
        result = {"ok": False, "error": "send_error", "detail": str(e)}
        await report_result(client, config, job_id, result, token)
        return

    # Send to printer — repeat for copies (ZPL ^PQ is handled by generateZpl,
    # but PDF copies need separate TCP sends)
    if fmt == "pdf" and copies > 1:
        for i in range(copies):
            result = await send_tcp(printer_host, printer_port, data_bytes, timeout)
            if not result["ok"]:
                break
    else:
        result = await send_tcp(printer_host, printer_port, data_bytes, timeout)

    await report_result(client, config, job_id, result, token)


async def report_result(
    client: httpx.AsyncClient, config, job_id: str, result: dict, token: str
) -> None:
    url = f"{config.api_url}/print-jobs/{job_id}/result"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = await client.post(url, json=result, headers=headers)
        if resp.status_code != 200:
            logger.error(f"Result callback failed for job {job_id}: {resp.status_code} {resp.text}")
        else:
            status = "OK" if result["ok"] else f"FAILED ({result.get('error', 'unknown')})"
            logger.info(f"Job {job_id}: {status}")
    except httpx.HTTPError as e:
        logger.error(f"Result callback error for job {job_id}: {e}")


async def subscribe_loop() -> None:
    global _sse_connected
    config = get_config()
    stream_url = f"{config.api_url}/print-jobs/stream"
    if config.printer_key:
        stream_url = f"{stream_url}?printer_key={quote(config.printer_key, safe='')}"

    if config.printer_key:
        logger.info(f"Print service starting — API: {config.api_url}, printer_key: {config.printer_key}")
    else:
        logger.info(f"Print service starting — API: {config.api_url} (wildcard — all jobs)")

    while True:
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                token = await authenticate(client, config)
                headers = {"Authorization": f"Bearer {token}"}
                logger.info(f"Connecting to SSE stream: {stream_url}")
                async with aconnect_sse(
                    client, "GET", stream_url, headers=headers
                ) as event_source:
                    _sse_connected = True
                    logger.info("Connected to SSE stream")
                    async for sse in event_source.aiter_sse():
                        try:
                            job = json.loads(sse.data)
                            await handle_job(client, config, job, token)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid SSE data: {e}")
                        except Exception as e:
                            logger.error(f"Error handling job: {e}")
        except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError) as e:
            _sse_connected = False
            logger.warning(f"SSE disconnected: {e} — reconnecting in {config.reconnect_delay}s")
            await asyncio.sleep(config.reconnect_delay)
        except Exception as e:
            _sse_connected = False
            logger.error(f"Unexpected error: {e} — reconnecting in {config.reconnect_delay * 2}s")
            await asyncio.sleep(config.reconnect_delay * 2)


async def health_server() -> None:
    """Minimal HTTP health endpoint for ops monitoring."""

    async def handle_health(reader, writer):
        # Read the request (ignore content)
        await reader.read(4096)
        body = json.dumps({"status": "ok", "sse_connected": _sse_connected})
        response = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"\r\n"
            f"{body}"
        )
        writer.write(response.encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_health, "0.0.0.0", 8200)
    logger.info("Health endpoint listening on :8200")
    async with server:
        await server.serve_forever()


async def main() -> None:
    await asyncio.gather(
        subscribe_loop(),
        health_server(),
    )


if __name__ == "__main__":
    asyncio.run(main())
