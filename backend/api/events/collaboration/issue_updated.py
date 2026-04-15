from events.collaboration.base_collaboration import BaseIssueModel
from events.collaboration.base_issue import BaseIssueEvent
from models.event import EventType


class IssueUpdatedEvent(BaseIssueEvent):

  class InfoModel(BaseIssueModel):
    pass

  @classmethod
  def get_event_type(cls) -> EventType:
    return EventType.ISSUE_UPDATED

  def apply(self):
    self.tx.collection('Issue').update(self.info.issue_data)
    issue_key = self.info.issue_data['_key']

    # Update critical status of related job and work order
    self._update_production_status(f'Issue/{issue_key}')

    self.response = dict(
      message=f"Issue { issue_key } updated successfully"
    )

