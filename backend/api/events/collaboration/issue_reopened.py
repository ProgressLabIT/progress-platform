from events.collaboration.base_collaboration import BaseIssueModel
from events.collaboration.base_issue import BaseIssueEvent
from models.event import EventType

class IssueReopenedEvent(BaseIssueEvent):
  class InfoModel(BaseIssueModel):
    pass

  @classmethod
  def get_event_type(cls) -> EventType:
    return EventType.ISSUE_REOPENED

  def apply(self):
    issue_key = self.info.issue_data['_key']
    open_as_critical = self.info.issue_data.get('critical', False)
    issue_update = dict(
      _key = issue_key,
      open = True,
      critical = open_as_critical,
      closed = None,
      closed_by = None
    )
    self.tx.collection('Issue').update(issue_update)

    self._update_production_status(f'Issue/{issue_key}')

    self.response = dict(
      message=f"Issue {issue_key} opened successfuly."
    )
