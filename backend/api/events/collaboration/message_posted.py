from datetime import datetime

from pydantic import Field

from events.collaboration.base_message import BaseMessageEvent
from models.collaboration import Message
from models.event import EventType, EventInfoModel
from utils.dt import timestamp

class MessagePostedEvent(BaseMessageEvent):

  class InfoModel(EventInfoModel):
    sender: str
    recipient: str
    content: str
    message_key: str | None = None

  @classmethod
  def get_event_type(cls) -> EventType:
    return EventType.MESSAGE_POSTED

  def apply(self):
    issue_key = self.info.recipient.split('/')[1]
    self.info.issue_data = dict(_key=issue_key)
    message_data = Message(**self.info.model_dump(), created=self.info.timestamp)
    new_message = self.tx.collection('message').insert(message_data, return_new=True)['new']
    self.info.message_key = new_message['_key']
    self.response = dict(
      message=f"Message posted correctly",
      message_key=self.info.message_key
    )
