from pydantic import BaseModel

class FlexModel(BaseModel):
  class Config:
    allow_population_by_field_name = True


class TargetActualData(FlexModel):
  target: float = None
  actual: float = None