from enum import Enum

from pydantic import Field

from models.base_models import ArangoDocument, ArangoEdge, FlexModel

class Tag(ArangoDocument):
  """
  collection: Tag
  """
  name: str = Field(
    ...,
    description="Display name of the tag, shown in the UI.",
    examples=["Urgent"],
  )
  description: str | None = Field(
    None,
    description="Optional description of what this tag represents or when it should be used.",
    examples=["Flag items that require immediate attention."],
  )
  color: str | None = Field(
    None,
    description="CSS colour value used to visually distinguish this tag in the UI (e.g. hex or named colour).",
    examples=["#E53935"],
  )

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
  type: TagAssignmentUpdateType = Field(
    ...,
    description="Whether to add or remove this tag connection.",
    examples=["add"],
  )
  tag_key: str = Field(
    ...,
    description="ArangoDB `_key` of the `Tag` document to connect or disconnect.",
    examples=["tag_urgent"],
  )
  context: TagAssignmentContext = Field(
    ...,
    description="Entity type that the tag is being connected to or disconnected from.",
    examples=["product"],
  )
  context_key: str = Field(
    ...,
    description="ArangoDB `_key` of the entity instance (e.g. a specific Product) being tagged.",
    examples=["prod_abc"],
  )
