from events.collaboration.base_collaboration import BaseCollaboration
from models.event import EventInfoModel, EventType

class MessageDeletedEvent(BaseCollaboration):
  class InfoModel(EventInfoModel):
    message_key: str

  @classmethod
  def get_event_type(cls) -> EventType:
    return EventType.MESSAGE_DELETED

  def apply(self):
    message_update = dict(
      _key = self.info.message_key,
      content = '[deleted]',
      deleted = self.info.timestamp
    )
    self.tx.collection('message').update(message_update)
    self.response = dict(
      message=f"Message {self.info.message_key} deleted correctly",
    )

