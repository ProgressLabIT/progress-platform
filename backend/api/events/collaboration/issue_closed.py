from events.collaboration.base_collaboration import BaseCollaboration, BaseCollaborationModel
from utils.dt import timestamp
from events.event_model import EventModel
from events.event_type import EventType

class IssueClosedModel(BaseCollaborationModel):
  event_type: str = EventType.ISSUE_CLOSED.name

class IssueClosed(BaseCollaboration):
  event_data: IssueClosedModel

  def set_model(self, base_model: EventModel):
    self.event_data = IssueClosedModel(**base_model.model_dump())

  def apply(self):
    issue_key = self.event_data.issue_data['_key']
    issue_update = dict(
      _key = issue_key,
      open = False,
      closed = timestamp(),
      closed_by = f'User/{self.event_data.user_key}'
    )
    self.tx.collection('Issue').update(issue_update)

    # Update critical status of related job and work order
    self._update_production_status(f'Issue/{issue_key}')


    self.set_response(dict(
      message=f"Issue {issue_key} closed successfuly."
    ))
