from utils.base_models import ArangoDocument

class Tag(ArangoDocument):
  """
  collection: Tag
  """
  name: str
  description: str | None = None
  color: str | None = None
