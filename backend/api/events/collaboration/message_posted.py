from pydantic import Field

from events.collaboration.base_collaboration import BaseCollaboration
from models.collaboration import Message
from models.event import EventType, EventInfoModel

class MessagePostedEvent(BaseCollaboration):

  class InfoModel(EventInfoModel):
    sender: str = Field(..., serialization_alias='_from')
    recipient: str = Field(..., serialization_alias='_to')
    content: str

  @classmethod
  def get_event_type(cls) -> EventType:
    return EventType.MESSAGE_POSTED

  def apply(self):
    issue_key = self.info.recipient.split('/')[1]
    self.info.issue_data = dict(_key=issue_key)
    self.message_data = self.tx.collection('message').insert(self.info.model_dump(by_alias=True), return_new=True)['new']
    self.response = dict(
      message=f"Message posted correctly to issue {issue_key}",
      message_key=self.message_data['_key']
    )

