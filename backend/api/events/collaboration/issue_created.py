from models.collaboration import Issue, IssueWithLinks
from events.collaboration.base_collaboration import BaseCollaboration, BaseIssueModel
from events.collaboration.base_issue import BaseIssueEvent
from models.event import EventType

class IssueCreatedEvent(BaseIssueEvent):

  class InfoModel(BaseIssueModel):
    pass

  @classmethod
  def get_event_type(cls) -> EventType:
    return EventType.ISSUE_CREATED

  def apply(self):
     self.issue_data = IssueWithLinks(**self.info.issue_data)
     # Remove links and exclude document id fields
     new_issue_record = Issue(
       **self.info.issue_data
     ).dict(by_alias=True)
     new_issue_id = self.tx.collection('Issue').insert(new_issue_record, return_new=True)['_id']

     rels = [BaseCollaboration._build_issue_link(_from=new_issue_id, link_dict=rel) for rel in self.info.issue_data['linked_to']]


     self.tx.collection('issue_rel').insert_many(rels, silent=True)

     # Update critical status of related job and work order
     self._update_production_status(new_issue_id)

     issue_key=new_issue_id.split('/')[1]
     self.info.issue_data['_key'] = issue_key

     self.response = dict(
       message="Issue created correctly",
       issue_key=issue_key
     )

