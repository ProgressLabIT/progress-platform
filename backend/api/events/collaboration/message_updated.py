from events.collaboration.base_collaboration import BaseCollaboration
from models.collaboration import Message, MessageUpdate
from utils.dt import timestamp
from models.event import EventType, EventInfoModel

class MessageUpdatedEvent(BaseCollaboration):

  class InfoModel(EventInfoModel):
    message_key: str
    content: str

  @classmethod
  def get_event_type(cls) -> EventType:
    return EventType.MESSAGE_UPDATED

  def apply(self):
    message_update = dict(
      _key = self.info.message_key,
      content = self.info.content,
      updated = self.info.timestamp
    )
    new = self.tx.collection('message').update(message_update, return_new=True)['new']
    self.response = dict(
      message=f"Message {self.info.message_key} updated correctly",
      new_content=new['content']
    )
