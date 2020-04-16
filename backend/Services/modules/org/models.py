from pydantic import Field

from utils.base_models import FlexModel


class Department(FlexModel):
  id: str = Field(None, alias="_id")
  name: str
  code: str = None
  description: str = None  