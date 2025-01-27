from models.collaboration import Issue, IssueWithLinks
from events.collaboration.base_collaboration import BaseCollaboration, BaseCollaborationModel
from events.event_model import EventModel
from events.event_type import EventType

class IssueCreatedModel(BaseCollaborationModel):
   event_type: str = EventType.ISSUE_CREATED.name

class IssueCreated(BaseCollaboration):
  event_data: IssueCreatedModel

  def set_model(self, base_model: EventModel):
    self.event_data = IssueCreatedModel(**base_model.model_dump())


  def apply(self):
     self.issue_data = IssueWithLinks(**self.event_data.issue_data)
     # Remove links and exclude document id fields
     new_issue_record = Issue(
       **self.event_data.issue_data
     ).dict(by_alias=True)
     new_issue_id = self.tx.collection('Issue').insert(new_issue_record, return_new=True)['_id']

     rels = [BaseCollaboration._build_issue_link(_from=new_issue_id, link_dict=rel) for rel in self.event_data.issue_data['linked_to']]


     self.tx.collection('issue_rel').insert_many(rels, silent=True)

     # Update critical status of related job and work order
     self._update_production_status(new_issue_id)

     issue_key=new_issue_id.split('/')[1]
     self.issue_data.key = issue_key

     self.set_response(dict(
       message="Issue created correctly",
       issue_key=issue_key
     ))

