from events.collaboration.base_collaboration import BaseIssueModel
from events.collaboration.base_issue import BaseIssueEvent
from utils.dt import timestamp
from models.event import EventType

class IssueClosedEvent(BaseIssueEvent):

  class InfoModel(BaseIssueModel):
    pass

  @classmethod
  def get_event_type(cls) -> EventType:
    return EventType.ISSUE_CLOSED

  def apply(self):
    issue_key = self.info.issue_data['_key']
    issue_update = dict(
      _key = issue_key,
      open = False,
      closed = timestamp(),
      closed_by = f'User/{self.info.user_key}'
    )
    self.tx.collection('Issue').update(issue_update)

    # Update critical status of related job and work order
    self._update_production_status(f'Issue/{issue_key}')


    self.response = dict(
      message=f"Issue {issue_key} closed successfuly."
    )
