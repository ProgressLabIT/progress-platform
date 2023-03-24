from events.shared import EventMeta

class IssueEvent:
  issue_collections = ['Issue', 'issue_rel']

  # Mapping of event types to metadata

  ISSUE_CREATED = dict(category="quality", collections=issue_collections, action="open_issue")
  MESSAGE_POSTED = dict(category="quality", collections=issue_collections, action="post_message")
  MESSAGE_UPDATED = dict(category="collaboration")
  # MESSAGE_DELETED
  ISSUE_CLOSED = dict(category="quality", collections=issue_collections, action="")
  ISSUE_REOPENED = dict(category="quality", collections=issue_collections, action="")
