import asyncio
import base64


def encode_zpl(zpl_string: str, mode: str = "replace") -> bytes:
    if mode == "error":
        try:
            return zpl_string.encode("ascii", errors="strict")
        except UnicodeEncodeError as e:
            raise ValueError(
                f"Non-ASCII character at position {e.start}: {repr(zpl_string[e.start])}"
            )
    else:
        return zpl_string.encode("ascii", errors="replace")


def decode_pdf(data_b64: str) -> bytes:
    return base64.b64decode(data_b64)


async def send_tcp(
    host: str, port: int, data: bytes, timeout: float = 5.0
) -> dict:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        writer.write(data)
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return {"ok": True}
    except asyncio.TimeoutError:
        return {
            "ok": False,
            "error": "timeout",
            "detail": f"Connection to {host}:{port} timed out after {timeout}s",
        }
    except ConnectionRefusedError:
        return {
            "ok": False,
            "error": "connection_refused",
            "detail": f"Connection refused at {host}:{port}",
        }
    except OSError as e:
        return {
            "ok": False,
            "error": "send_error",
            "detail": str(e),
        }
