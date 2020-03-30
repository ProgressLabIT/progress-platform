from utils.base_models import FlexModel
from pydantic import Field


class Department(FlexModel):
  id: str = Field(None, alias="_id")
  name: str
  code: str = None
  description: str = None  