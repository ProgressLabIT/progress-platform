import asyncio
import json
import logging

import nats

from config import get_config
from tcp_sender import encode_zpl, decode_pdf, send_tcp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("print-service")

_nats_connected = False


async def handle_job(job: dict, config) -> dict:
    printer_host = job["printer_host"]
    printer_port = job.get("printer_port", 9100)
    fmt = job["format"]
    data_str = job["data"]
    copies = job.get("copies", 1)
    timeout = job.get("timeout_seconds", 5.0)

    logger.info(f"Job: {fmt} -> {printer_host}:{printer_port} (copies={copies})")

    try:
        if fmt == "zpl":
            data_bytes = encode_zpl(data_str, mode=config.non_ascii)
        elif fmt == "pdf":
            data_bytes = decode_pdf(data_str)
        else:
            return {"ok": False, "error": "send_error", "detail": f"Unknown format: {fmt}"}
    except ValueError as e:
        return {"ok": False, "error": "send_error", "detail": str(e)}

    if fmt == "pdf" and copies > 1:
        for i in range(copies):
            result = await send_tcp(printer_host, printer_port, data_bytes, timeout)
            if not result["ok"]:
                break
    else:
        result = await send_tcp(printer_host, printer_port, data_bytes, timeout)

    status = "OK" if result["ok"] else f"FAILED ({result.get('error', 'unknown')})"
    logger.info(f"Job result: {status}")
    return result


async def subscribe_loop() -> None:
    global _nats_connected
    config = get_config()

    subject = f"progress.print.jobs.{config.printer_key}" if config.printer_key else "progress.print.jobs.*"
    logger.info(f"Print service starting — NATS: {config.nats_url}, subject: {subject}")

    while True:
        try:
            async def _disconnected():
                logger.warning("NATS disconnected")

            async def _reconnected():
                logger.warning("NATS reconnected")

            nc = await nats.connect(
                config.nats_url,
                reconnect_time_wait=config.reconnect_delay,
                max_reconnect_attempts=-1,
                disconnected_cb=_disconnected,
                reconnected_cb=_reconnected,
            )
            _nats_connected = True
            logger.info(f"Connected to NATS, subscribing to {subject}")

            sub = await nc.subscribe(subject)
            async for msg in sub.messages:
                try:
                    job = json.loads(msg.data)
                    result = await handle_job(job, config)
                except Exception as e:
                    logger.error(f"Error handling job: {e}")
                    result = {"ok": False, "error": "internal", "detail": str(e)}
                await msg.respond(json.dumps(result).encode())

        except Exception as e:
            _nats_connected = False
            logger.error(f"NATS error: {e} — reconnecting in {config.reconnect_delay}s")
            await asyncio.sleep(config.reconnect_delay)


async def health_server() -> None:
    """Minimal HTTP health endpoint for ops monitoring."""

    async def handle_health(reader, writer):
        await reader.read(4096)
        body = json.dumps({"status": "ok", "nats_connected": _nats_connected})
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
