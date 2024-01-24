from typing import Any

from pydantic import BaseModel

class APIResponse(BaseModel):
  status: int = 200
  message: str | None = None
  # error: str | None = None
  detail: Any | None = None
