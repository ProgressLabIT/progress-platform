from typing import Union, List

from pydantic import BaseModel

class APIResponse(BaseModel):
  status: int = 200
  message: str = None
  # error: str = None
  detail: Union[int, str, dict, list] = None