from pydantic import BaseModel, Field

class FlexModel(BaseModel):
  class Config:
    allow_population_by_field_name = True


class TargetActualData(FlexModel):
  target: float = None
  actual: float = None




class ArangoDocument(FlexModel):
  id: str = Field(None, alias="_id")
  key: str = Field(None, alias="_key")
  rev: str = Field(None, alias="_rev")

class ArangoEdge(ArangoDocument):
  from_doc: str = Field(None, alias="_from")
  to_doc: str = Field(None, alias="_to")