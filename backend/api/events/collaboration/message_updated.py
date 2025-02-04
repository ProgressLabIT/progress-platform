from events.collaboration.base_collaboration import BaseCollaboration, BaseCollaborationModel
from models.collaboration import Message, MessageUpdate
from models.event import EventModel
from utils.dt import timestamp
from models.event import EventType
class MessageUpdatedModel(BaseCollaborationModel):
  event_type: str = EventType.MESSAGE_UPDATED.name
  message_data: MessageUpdate | None = None
class MessageUpdated(BaseCollaboration):
  event_data: MessageUpdatedModel

  def set_model(self, base_model: EventModel):
    self.info = MessageUpdatedModel(**base_model.model_dump())

  def apply(self):
    self.info.message_data.updated = self.info.timestamp
    message_record = self.info.message_data.dict(by_alias=True)
    db_resp = self.tx.collection('message').update(message_record, return_new=True)
    self.set_response(dict(
      message="Message updated correctly",
      detail=dict(
        new_message=db_resp['new']
      )
    ))
