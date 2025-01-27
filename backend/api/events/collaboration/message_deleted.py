from events.collaboration.base_collaboration import BaseCollaboration, BaseCollaborationModel
from models.collaboration import Message, MessageUpdate
from events.event_model import EventModel
from events.event_type import EventType
class MessageDeletedModel(BaseCollaborationModel):
  event_type: str = EventType.MESSAGE_DELETED.name
  message_data: MessageUpdate | None = None

class MessageDeleted(BaseCollaboration):
  event_data: MessageDeletedModel

  def set_model(self, base_model: EventModel):
    self.event_data = MessageDeletedModel(**base_model.model_dump())

  def apply(self):
      self.event_data.message_data.content = '[deleted]'
      self.event_data.message_data.deleted = self.event_data.timestamp
      message_record = self.event_data.message_data.dict(by_alias=True)
      db_resp = self.tx.collection('message').update(message_record, return_new=True)
      self.set_response(dict(
        message="Message deleted correctly",
      ))
