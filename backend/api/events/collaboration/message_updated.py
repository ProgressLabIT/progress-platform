from events.collaboration.base_collaboration import BaseCollaboration, BaseCollaborationModel
from models.collaboration import Message, MessageUpdate
from events.event_model import EventModel
from utils.dt import timestamp
from events.event_type import EventType
class MessageUpdatedModel(BaseCollaborationModel):
  event_type: str = EventType.MESSAGE_UPDATED.name
  message_data: MessageUpdate | None = None
class MessageUpdated(BaseCollaboration):
  event_data: MessageUpdatedModel

  def set_model(self, base_model: EventModel):
    self.event_data = MessageUpdatedModel(**base_model.model_dump())

  def apply(self):
    self.event_data.message_data.updated = self.event_data.timestamp
    message_record = self.event_data.message_data.dict(by_alias=True)
    db_resp = self.tx.collection('message').update(message_record, return_new=True)
    self.set_response(dict(
      message="Message updated correctly",
      detail=dict(
        new_message=db_resp['new']
      )
    ))
