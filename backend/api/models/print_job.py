from enum import Enum
from pydantic import BaseModel


class PrintFormat(str, Enum):
    ZPL = "zpl"
    PDF = "pdf"


class PrintJobRequest(BaseModel):
    printer_host: str
    printer_port: int = 9100
    format: PrintFormat
    data: str  # ZPL text or base64-encoded PDF
    copies: int = 1
    timeout_seconds: float = 5.0
    printer_key: str  # Required — identifies target printer for SSE routing


class PrintJobResult(BaseModel):
    ok: bool
    error: str | None = None  # connection_refused | timeout | send_error
    detail: str | None = None
