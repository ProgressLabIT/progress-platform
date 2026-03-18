"""
Unit tests for tcp_sender.py — encode_zpl, decode_pdf, send_tcp
Run with: python -m pytest test_tcp_sender.py -v
"""
import asyncio
import base64
import socket

import pytest
import pytest_asyncio

from tcp_sender import decode_pdf, encode_zpl, send_tcp


# ---------------------------------------------------------------------------
# encode_zpl tests
# ---------------------------------------------------------------------------


def test_encode_zpl_ascii_only_returns_same_bytes():
    """encode_zpl with ASCII-only string returns the same bytes."""
    zpl = "^XA^FO50,50^ADN,36,20^FD Hello World ^FS^XZ"
    result = encode_zpl(zpl)
    assert result == zpl.encode("ascii")


def test_encode_zpl_non_ascii_replace_mode_substitutes_question_mark():
    """encode_zpl with non-ASCII in 'replace' mode replaces with '?'."""
    zpl = "Hello \u00e9 World"  # é is U+00E9
    result = encode_zpl(zpl, mode="replace")
    assert b"?" in result
    assert b"Hello " in result
    assert b" World" in result
    # The non-ASCII character must have been replaced
    assert "\u00e9".encode("ascii", errors="replace") == b"?"


def test_encode_zpl_non_ascii_error_mode_raises_value_error():
    """encode_zpl with non-ASCII in 'error' mode raises ValueError with position info."""
    zpl = "Hello \u00e9"  # é at position 6
    with pytest.raises(ValueError) as exc_info:
        encode_zpl(zpl, mode="error")
    error_msg = str(exc_info.value)
    assert "6" in error_msg  # position
    assert "Non-ASCII" in error_msg


# ---------------------------------------------------------------------------
# decode_pdf tests
# ---------------------------------------------------------------------------


def test_decode_pdf_valid_base64_returns_decoded_bytes():
    """decode_pdf with valid base64 returns the decoded bytes."""
    original = b"PDF binary content \x00\x01\x02"
    encoded = base64.b64encode(original).decode("ascii")
    result = decode_pdf(encoded)
    assert result == original


def test_decode_pdf_invalid_base64_raises_error():
    """decode_pdf with invalid base64 raises an error."""
    with pytest.raises(Exception):
        decode_pdf("not-valid-base64!!!!")


# ---------------------------------------------------------------------------
# send_tcp tests
# ---------------------------------------------------------------------------


def _get_free_port() -> int:
    """Find a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.asyncio
async def test_send_tcp_success():
    """send_tcp to a listening port succeeds and returns {"ok": True}."""
    received_data = []

    async def handle_client(reader, writer):
        data = await reader.read(4096)
        received_data.append(data)
        writer.close()
        await writer.wait_closed()

    port = _get_free_port()
    server = await asyncio.start_server(handle_client, "127.0.0.1", port)

    async with server:
        result = await send_tcp("127.0.0.1", port, b"test data")
        # Yield control so the server's handle_client callback can complete
        await asyncio.sleep(0.05)

    assert result == {"ok": True}
    assert received_data == [b"test data"]


@pytest.mark.asyncio
async def test_send_tcp_connection_refused():
    """send_tcp to a non-listening port returns {"ok": False, "error": "connection_refused"}."""
    port = _get_free_port()
    # Don't start a server — port is free but nothing is listening
    result = await send_tcp("127.0.0.1", port, b"test data")
    assert result["ok"] is False
    assert result["error"] == "connection_refused"


@pytest.mark.asyncio
async def test_send_tcp_timeout():
    """send_tcp to a non-routable address with short timeout returns timeout error."""
    # 192.0.2.1 is TEST-NET (RFC 5737) — non-routable, connections will time out
    result = await send_tcp("192.0.2.1", 9100, b"test data", timeout=0.1)
    assert result["ok"] is False
    assert result["error"] == "timeout"
