from fastapi import HTTPException

from events.shared import EventMeta
from models.quality import Issue, IssueLink, IssueWithLinks

class IssueEvent:
  issue_collections = ['Event', 'Issue', 'issue_rel']
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

  ISSUE_OPENED = EventMeta(
    collections=issue_collections,
    action="open_issue"
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

  @staticmethod
  def _build_issue_link(_from: str, link_dict: IssueLink):
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

  def create_issue(self):
    self.info.issue_data = IssueWithLinks(**self.info.issue_data)
    new_issue_record = Issue(**self.info.issue_data.dict())
    new_issue_id = self.tx.collection('Issue').insert(new_issue_record.dict(exclude={'_key', '_id', '_rev'}), return_new=True)['_id']

    issue_links = [l for l in self.info.issue_data.linked_to]
    rels = [self._build_issue_link(_from=new_issue_id, link_dict=rel) for rel in issue_links]

    self.tx.collection('issue_rel').insert_many(rels, silent=True)
    issue_key=new_issue_id.split('/')[1]
    self.info.issue_data.key = issue_key

    self.response = dict(
      message="Issue created correctly",
      detail=dict(issue_key=issue_key)
    )

  def update_issue(self):
    new_data = dict(_key = self.info.issue_data.issue_key)

    if self.info.issue_data.title:
      new_data['title'] = self.info.issue_data.title

    if self.info.issue_data.description:
      new_data['description'] = self.info.issue_data.description

    if self.info.issue_data.issue_type:
      new_data['issue_type'] = self.info.issue_data.issue_type

    if self.info.issue_data.critical:
      new_data['critical'] = self.info.issue_data.critical

    db_resp = self.tx.collection('Issue').update(new_data, return_new=True, return_old=True)

    self.info.original_issue = Issue(**db_resp['old'])
    self.info.updated_issue = Issue(**db_resp['new'])

    self.response = dict(
      message=f"Issue { updated_issue['_key'] } updated successfully",
      detail=updated_issue
    )

  def close_issue(self):
    issue_key = self.info.issue_data.issue_key
    issue_update = dict(_key = issue_key, open=False)
    self.tx.collection('Issue').update(issue_update)
    self.response = dict(
      message=f"Issue {issue_key} closed successfuly."
    )

  def open_issue(self):
    issue_key = self.info.issue_data.issue_key
    issue_update = dict(_key = issue_key, open=True)
    self.tx.collection('Issue').update(issue_update)
    self.response = dict(
      message=f"Issue {issue_key} opened successfuly."
    )

  def post_message(self):
    issue_key = self.info.message_data.recipient.split('/')[1]
    self.info.issue_data = dict(_key=issue_key)
    message_data = self.info.message_data.dict(by_alias=True, exclude={'_key', '_id', '_rev'})
    self.info.message_data = self.tx.collection('message').insert(message_data, return_new=True)['new']
    self.response = dict(
      message="Message posted correctly to issue {issue_key}"
    )

  def update_message(self):
    issue_key = self.info.message_data.recipient.split('/')[1]
    self.info.issue_data = dict(issue_key=issue_key)

    self.info.message_data.updated = True
    message_record = self.info.message_data.dict(by_alias=True)
    db_resp = self.tx.update(message_record, return_new=True)
    self.response = dict(
      message="Message updated correctly",
      detail=dict(
        new_message=db_resp['new']
      )
    )



