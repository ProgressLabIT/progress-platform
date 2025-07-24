from events.collaboration.base_collaboration import BaseCollaboration, BaseIssueModel
from utils.file import FileHandler
from models.form import FileBucket
from models.event import EventType, EventInfoModel

class IssueDeletedEvent(BaseCollaboration):

  class InfoModel(BaseIssueModel):
    pass

  @classmethod
  def get_event_type(cls) -> EventType:
    return EventType.ISSUE_DELETED

  def apply(self):
    issue_key = self.info.issue_data['_key']

    self.tx.collection('Issue').delete(issue_key)
    self.tx.collection('issue_rel').delete_match(filters=dict(_from=f'Issue/{issue_key}'))
    self.tx.collection('message').delete_match(filters=dict(_to=f'Issue/{issue_key}'))

    # TODO: OBJECT STORAGE MIGRATION - Replace FileHandler.remove_dir() with object storage delete
    # Use object storage SDK to delete all files with prefix for this issue
    FileHandler(bucket=FileBucket.ISSUE, object_key=issue_key).remove_dir()

    self._update_production_status(f'Issue/{issue_key}')

    self.response = dict(
      message=f"Issue {issue_key} deleted successfuly"
    )

