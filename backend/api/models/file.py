from models.base_models import ArangoDocument
from datetime import datetime


class File(ArangoDocument):
  name: str
  size: int
  type: str | None = None
  url: str | None = None
  public: bool = True
  uploaded_by: str | None = None
  uploaded_at: datetime | None = None
