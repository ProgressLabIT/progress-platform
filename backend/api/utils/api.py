from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
  status: int = 200
  message: str | None = None
  # error: str | None = None
  detail: T = None


class AuthAPIResponse(APIResponse):
  access_token: str | None = None
  token_type: str | None = None

