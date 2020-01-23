from pydantic import BaseModel

class APIResponse(BaseModel):
  status: str = 200
  message: str = None
  # error: str = None
  detail: dict = None