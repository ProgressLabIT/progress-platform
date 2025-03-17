import traceback

from events.serial.base_serial import BaseSerialEvent
from models.event import EventInfoModel, EventType
from models.serial import SerialNotificationErrorCode, SerialNotificationType


class SerialUnlinkedEvent(BaseSerialEvent):
  """
  This event is used to unlink components from their parent.
  """

  class InfoModel(EventInfoModel):
    child_serial_key: str
    parent_serial_key: str | None = None
    batch_key: str | None = None,
    reason: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.SERIAL_UNLINKED

  def apply(self):

    # Ensure record exists
    if self.info.parent_serial_key is None:
      if self.info.batch_key is None:
        raise ValueError('Parent serial key or batch key is required')
      _from = f'Batch/{self.info.batch_key}'

    else:
      _from = f'Serial/{self.info.parent_serial_key}'

    try:
      match = dict(_from=_from, _to=f'Serial/{self.info.child_serial_key}')
      update = dict(replaced=True, reason=self.info.reason)
      updates_count = self.tx.collection('contains').update_match(match, update)
      if updates_count == 0:
        raise ValueError('No serial found to unlink')
      if updates_count > 1:
        raise ValueError('Multiple serials found to unlink')
    except:
      print(traceback.format_exc())
      self.notify_results(dict(
        notification=SerialNotificationType.ERROR,
        error_code=SerialNotificationErrorCode.EXCEPTION,
        error=traceback.format_exc()
      ))

    self.notify_results(dict(
      notification=SerialNotificationType.UPDATED
    ))
    self.response = dict(
      message=f"Serial {self.info.child_serial_key} unlinked from parent {self.info.parent_serial_key}."
    )

