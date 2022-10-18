from datetime import datetime, timezone

from utils.base_models import ArangoDocument


class TaskType(ArangoDocument):
  name: str
  description: str = None
  icon_path: str = None
  default: bool = False


class Task(ArangoDocument):
  title: str
  description: str = None
  task_type: TaskType


class IssueType(ArangoDocument):
  name: str
  description: str = None
  icon_path: str = None
  default: bool = False


class Issue(ArangoDocument):
  title: str
  description: str = None
  issue_type: IssueType


class Message(ArangoDocument):
  """
  Messages can be sent by users and third party software.
  """
  from: str = Field(..., alias="_from")
  to: str = Field(..., alias="_to")
  content: str
  timestamp: datetime = datetime.now(timezone.utc)
