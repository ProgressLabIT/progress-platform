from pydantic import BaseModel, Field, ConfigDict

class FlexModel(BaseModel):
  model_config = ConfigDict(
    populate_by_name=True
  )


class TargetActualData(FlexModel):
  target: float | None = None
  actual: float | None = None




class ArangoDocument(FlexModel):
  id: str | None = Field(None, alias="_id")
  key: str | None = Field(None, alias="_key")
  rev: str | None = Field(None, alias="_rev")

class ArangoEdge(ArangoDocument):
  from_doc: str | None = Field(None, alias="_from")
  to_doc: str | None = Field(None, alias="_to")
