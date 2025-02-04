from events.collaboration.base_collaboration import BaseCollaboration, BaseCollaborationModel
from models.event import EventModel
from models.event import EventType

class IssueReopenedModel(BaseCollaborationModel):
  event_type: str = EventType.ISSUE_REOPENED.name

class IssueReopened(BaseCollaboration):
  event_data: IssueReopenedModel

  def set_model(self, base_model: EventModel):
    self.event_data = IssueReopenedModel(**base_model.model_dump())

  def apply(self):
      issue_key = self.event_data.issue_data['_key']
      open_as_critical = self.event_data.issue_data.get('critical', False)
      issue_update = dict(
        _key = issue_key,
        open = True,
        critical = open_as_critical,
        closed = None,
        closed_by = None
      )
      self.tx.collection('Issue').update(issue_update)

      self._update_production_status(f'Issue/{issue_key}')

      self.set_response(dict(
        message=f"Issue {issue_key} opened successfuly."
      ))
