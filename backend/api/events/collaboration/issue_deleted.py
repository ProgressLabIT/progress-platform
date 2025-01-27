from events.collaboration.base_collaboration import BaseCollaboration, BaseCollaborationModel
from utils.file import FileHandler
from models.form import FileBucket
from events.event_model import EventModel
from events.event_type import EventType

class IssueDeletedModel(BaseCollaborationModel):
  event_type: str = EventType.ISSUE_DELETED.name

class IssueDeleted(BaseCollaboration):
  event_data: IssueDeletedModel

  def set_model(self, base_model: EventModel):
    self.event_data = IssueDeletedModel(**base_model.model_dump())

  def apply(self):
      issue_key = self.event_data.issue_data['_key']

      self.tx.collection('Issue').delete(issue_key)
      self.tx.collection('issue_rel').delete_match(filters=dict(_from=f'Issue/{issue_key}'))
      self.tx.collection('message').delete_match(filters=dict(_to=f'Issue/{issue_key}'))

      FileHandler(bucket=FileBucket.ISSUE, object_key=issue_key).remove_dir()

      self._update_production_status(f'Issue/{issue_key}')

      self.set_response(dict(
        message=f"Issue {issue_key} deleted successfuly"
      ))
