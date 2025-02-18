import traceback

from events.serial.base_serial import BaseSerialEvent
from models.event import EventInfoModel, EventType
from models.serial import (
  SerialLink,
  SerialNotificationErrorCode,
  SerialNotificationType,
)
from utils.exceptions import SerialNotLinkedError


class SerialLinkedEvent(BaseSerialEvent):
  """
  This event is used to link components to their parent, using the `contains` edge collection.
  The parent can be a specific product serial or batch in case of work order without traceability enabled.
  """

  class InfoModel(EventInfoModel):
    child_serial_key: str
    parent_serial_key: str | None = None
    wo_key: str | None = None,
    component_key: str | None = None,
    job_key: str | None = None,
    batch_key: str | None = None,

  @classmethod
  def get_event_type(cls):
    return EventType.SERIAL_LINKED

  def apply(self):

    try:
      # Ensure serial is not already linked
      if self.tx.collection('contains').find(dict(_to=f'Serial/{self.info.to_serial}')).count() > 0:
        raise ValueError('Cannot link serials: multiple usage of the same component')

      # Link to batch
      if self.info.parent_serial_key is None:
        # Ensure work order doesn't have traceability enabled
        if self.tx.collection('WorkOrder').get(self.info.wo_key).get('traceability_level', None) is not None:
          raise ValueError('You must provide a parent serial to link components to for this work order')

        else:
          self.tx.collection('contains').update(SerialLink(
            **self.info.model_dump(),
            _from=f'Batch/{self.info.batch_key}',
            _to=f'Serial/{self.info.child_serial_key}'
          ))

      # Link to parent serial
      else:
        self.tx.collection('contains').insert(SerialLink(
          **self.info.model_dump(),
          _from=f'Serial/{self.info.parent_serial_key}',
          _to=f'Serial/{self.info.child_serial_key}'
        ))

    except:
      print(traceback.format_exc())
      self.notify_results(dict(
        notification=SerialNotificationType.ERROR,
        error_code=SerialNotificationErrorCode.EXCEPTION,
        error=traceback.format_exc()
      ))
      raise SerialNotLinkedError('Cannot link serials')

    self.notify_results(dict(
      notification=SerialNotificationType.UPDATED
    ))
    self.response = dict(
      message="Serial linked correctly"
    )

