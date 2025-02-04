from events.collaboration.base_collaboration import BaseCollaboration, BaseCollaborationModel
from models.event import EventModel
from models.event import EventType

class IssueUpdatedModel(BaseCollaborationModel):
  event_type: str = EventType.ISSUE_UPDATED.name

class IssueUpdated(BaseCollaboration):
  event_data: IssueUpdatedModel

  def set_model(self, base_model: EventModel):
    self.event_data = IssueUpdatedModel(**base_model.model_dump())

  def apply(self):
    self.tx.collection('Issue').update(self.event_data.issue_data)
    issue_key = self.event_data.issue_data['_key']

    # Update critical status of related job and work order
    self._update_production_status(f'Issue/{issue_key}')

    self.set_response(dict(
      message=f"Issue { issue_key } updated successfully"
    ))
