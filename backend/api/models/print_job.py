from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from models.base_models import ArangoDocument


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


class PrintJobRecord(ArangoDocument):
    status: str = "pending"  # pending | sent | failed
    printer_host: str
    printer_port: int
    format: PrintFormat
    copies: int
    timeout_seconds: float
    created_at: str | None = None  # ISO datetime string
    completed_at: str | None = None
    error: str | None = None
    error_detail: str | None = None


class PrintJobResult(BaseModel):
    ok: bool
    error: str | None = None  # connection_refused | timeout | send_error
    detail: str | None = None
