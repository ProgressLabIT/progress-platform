from events.collaboration.base_collaboration import BaseCollaboration, BaseCollaborationModel
from models.collaboration import Message, MessageUpdate
from models.event import EventModel
from models.event import EventType
class MessageDeletedModel(BaseCollaborationModel):
  event_type: str = EventType.MESSAGE_DELETED.name
  message_data: MessageUpdate | None = None

class MessageDeleted(BaseCollaboration):
  event_data: MessageDeletedModel

  def set_model(self, base_model: EventModel):
    self.info = MessageDeletedModel(**base_model.model_dump())

  def apply(self):
      self.info.message_data.content = '[deleted]'
      self.info.message_data.deleted = self.info.timestamp
      message_record = self.info.message_data.dict(by_alias=True)
      db_resp = self.tx.collection('message').update(message_record, return_new=True)
      self.set_response(dict(
        message="Message deleted correctly",
      ))
