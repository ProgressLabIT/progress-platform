from events.collaboration.base_collaboration import BaseCollaboration


class BaseMessageEvent(BaseCollaboration):
  _notification_subtopic = "message"

  def _get_recipient_id(self):
    if hasattr(self.info, 'recipient'):
      return self.info.recipient
    msg = self.tx.collection('message').get(self.info.message_key)
    return msg['_to']

  def _build_event_payload(self) -> dict | None:
    payload = super()._build_event_payload()
    if payload:
      payload['recipient_id'] = self._get_recipient_id()
    return payload
