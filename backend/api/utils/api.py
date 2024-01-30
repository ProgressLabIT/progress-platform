from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
  status: int = 200
  message: str | None = None
  # error: str | None = None
  detail: T = None
