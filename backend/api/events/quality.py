from fastapi import HTTPException

from events.shared import EventMeta
from models.quality import Issue, IssueLink, IssueWithLinks
from utils.dt import timestamp
from utils.quality import Queries

class IssueEvent:
  issue_collections = ['Event', 'Issue', 'issue_rel', 'WorkOrder', 'Job']
  message_collections = ['Event', 'message']
  # Mapping of event types to metadata

  ISSUE_CREATED = EventMeta(
    collections=issue_collections,
    action="create_issue"
  )

  ISSUE_UPDATED = EventMeta(
    collections=issue_collections,
    action="update_issue"
  )

  ISSUE_CLOSED = EventMeta(
    collections=issue_collections,
    action="close_issue"
  )

  ISSUE_DELETED = EventMeta(
    collections=issue_collections,
    action="delete_issue"
  )

  ISSUE_REOPENED = EventMeta(
    collections=issue_collections,
    action="reopen_issue"
  )

  MESSAGE_POSTED = EventMeta(
    collections=message_collections,
    action="post_message"
  )

  MESSAGE_UPDATED = EventMeta(
    collections=message_collections,
    action="update_message"
  )

  MESSAGE_DELETED = EventMeta(
    collections=message_collections,
    action="delete_message"
  )

  #===============================================================

  @staticmethod
  def _build_issue_link(_from: str, link_dict: IssueLink):
    """
    Utility function to create the database records for the issue_rel edge collection
    """
    link_map = dict(
      product="Product/",
      operation="Operation/",
      phase="Phase/",
      work_order="WorkOrder/",
      project="Project/",
      user="User/",
      job="Job/"
    )
    target = link_map[link_dict.type.value] + link_dict.key
    return dict(_from=_from, _to=target)


  def _update_production_status(self, issue_id):
    """
    Set critical flag of work order and job related to the issue,
    checking all other issues related to them
    """
    bind_vars = dict(issue_id=issue_id)
    cursor = self.tx.aql.execute(Queries.CHECK_PRODUCTION_CRITICAL_STATUS, bind_vars=bind_vars)
    for document in cursor:
      self.tx.update_document(document)


  #===============================================================

  def create_issue(self):
    self.info.issue_data = IssueWithLinks(**self.info.issue_data)
    # Remove links and exclude document id fields
    new_issue_record = Issue(
      **self.info.issue_data.dict()
    ).dict(by_alias=True)
    new_issue_id = self.tx.collection('Issue').insert(new_issue_record, return_new=True)['_id']

    rels = [self._build_issue_link(_from=new_issue_id, link_dict=rel) for rel in self.info.issue_data.linked_to]


    self.tx.collection('issue_rel').insert_many(rels, silent=True)

    # Update critical status of related job and work order
    self._update_production_status(new_issue_id)

    issue_key=new_issue_id.split('/')[1]
    self.info.issue_data.key = issue_key

    self.response = dict(
      message="Issue created correctly",
      detail=dict(issue_key=issue_key)
    )

  #===============================================================

  def update_issue(self):
    self.tx.collection('Issue').update(self.info.issue_data)
    issue_key = self.info.issue_data['_key']

    # Update critical status of related job and work order
    self._update_production_status(f'Issue/{issue_key}')

    self.response = dict(
      message=f"Issue { issue_key } updated successfully"
    )

  #===============================================================

  def close_issue(self):
    issue_key = self.info.issue_data['_key']
    issue_update = dict(
      _key = issue_key,
      open = False,
      closed = timestamp()
    )
    self.tx.collection('Issue').update(issue_update)

    # Update critical status of related job and work order
    self._update_production_status(f'Issue/{issue_key}')


    self.response = dict(
      message=f"Issue {issue_key} closed successfuly."
    )

  #===============================================================

  def reopen_issue(self):
    issue_key = self.info.issue_data['_key']
    open_as_critical = self.info.issue_data.get('critical', False)
    issue_update = dict(
      _key = issue_key,
      open = True,
      critical = open_as_critical,
      closed = None
    )
    self.tx.collection('Issue').update(issue_update)

    self._update_production_status(f'Issue/{issue_key}')

    self.response = dict(
      message=f"Issue {issue_key} opened successfuly."
    )

  #===============================================================

  def delete_issue(self):
    issue_key = self.info.issue_data['_key']

    self.tx.collection('Issue').delete(issue_key)
    self.tx.collection('issue_rel').delete_match(filters=dict(_from=f'Issue/{issue_key}'))
    self.tx.collection('message').delete_match(filters=dict(_to=f'Issue/{issue_key}'))
    self._update_production_status(f'Issue/{issue_key}')

    self.response = dict(
      message=f"Issue {issue_key} deleted successfuly"
    )

  #===============================================================

  def post_message(self):
    issue_key = self.info.message_data.recipient.split('/')[1]
    self.info.issue_data = dict(_key=issue_key)
    message_data = self.info.message_data.dict(by_alias=True, exclude={'_key', '_id', '_rev'})
    self.info.message_data = self.tx.collection('message').insert(message_data, return_new=True)['new']
    self.response = dict(
      message="Message posted correctly to issue {issue_key}"
    )

  #===============================================================

  def update_message(self):
    self.info.message_data.updated = self.info.timestamp
    message_record = self.info.message_data.dict(by_alias=True)
    db_resp = self.tx.collection('message').update(message_record, return_new=True)
    self.response = dict(
      message="Message updated correctly",
      detail=dict(
        new_message=db_resp['new']
      )
    )

  #===============================================================

  def delete_message(self):
    self.info.message_data.content = '[deleted]'
    self.info.message_data.deleted = self.info.timestamp
    message_record = self.info.message_data.dict(by_alias=True)
    db_resp = self.tx.collection('message').update(message_record, return_new=True)
    self.response = dict(
      message="Message deleted correctly",
    )



