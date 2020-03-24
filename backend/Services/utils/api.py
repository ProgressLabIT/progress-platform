from pydantic import BaseModel
from typing import Union, List

class APIResponse(BaseModel):
  status: str = 200
  message: str = None
  # error: str = None
  detail: Union[int, str, dict, list] = None