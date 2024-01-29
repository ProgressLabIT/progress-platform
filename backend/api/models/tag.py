from enum import Enum

from utils.base_models import ArangoDocument, ArangoEdge, FlexModel

class Tag(ArangoDocument):
  """
  collection: Tag
  """
  name: str
  description: str | None = None
  color: str | None = None

class TagConnection(ArangoEdge):
  """
  collection: has_tag
  from: * (any collection)
  to: Tag
  """
  pass

class TagAssignmentContext(str, Enum):
  PRODUCT = 'product'

class TagAssignmentUpdateType(str, Enum):
  ADD = 'add'
  REMOVE = 'remove'

class TagConnectionUpdate(FlexModel):
  type: TagAssignmentUpdateType
  tag_key: str
  context: TagAssignmentContext
  context_key: str
