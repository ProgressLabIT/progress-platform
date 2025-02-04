from events.collaboration.base_collaboration import BaseCollaboration, BaseCollaborationModel
from models.collaboration import Message
from models.event import EventModel
from models.event import EventType

class MessagePostedModel(BaseCollaborationModel):
  event_type: str = EventType.MESSAGE_POSTED.name
  message_data: Message | None = None

class MessagePosted(BaseCollaboration):
  event_data: MessagePostedModel

  def set_model(self, base_model: EventModel):
    self.info = MessagePostedModel(**base_model.model_dump())

  def apply(self):
      issue_key = self.info.message_data.recipient.split('/')[1]
      self.info.issue_data = dict(_key=issue_key)
      message_data = self.info.message_data.dict(by_alias=True, exclude={'_key', '_id', '_rev'})
      self.message_data = self.tx.collection('message').insert(message_data, return_new=True)['new']
      self.set_response(dict(
        message="Message posted correctly to issue "+issue_key,
        message_key=self.message_data['_key']
      ))
