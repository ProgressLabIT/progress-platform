import traceback

from events.serial.base_serial import BaseSerialEvent
from events.inventory.base_inventory import BaseInventoryEvent
from events.inventory.movement_reversed import MovementReversedEvent
from models.event import EventInfoModel, EventType
from models.inventory import InventoryMovementType
from models.serial import SerialNotificationErrorCode, SerialNotificationType


class SerialUnlinkedEvent(BaseSerialEvent, BaseInventoryEvent):
  """
  This event is used to unlink components from their parent.
  """

  class InfoModel(EventInfoModel):
    child_serial_key: str
    parent_serial_key: str | None = None
    batch_key: str | None = None,
    reason: str | None = None
    process_inventory: bool | None = True


  @classmethod
  def get_tx_collections(cls):
    return [
      'contains',
      'is_in_position',
      'movement',
      'Serial'
    ]


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
    except Exception as e:
      print(traceback.format_exc())
      self.notify_results(dict(
        notification=SerialNotificationType.ERROR,
        error_code=SerialNotificationErrorCode.EXCEPTION,
        error=traceback.format_exc()
      ))
      raise

    if self.info.process_inventory:
      self._process_inventory()

    self.notify_results(dict(
      notification=SerialNotificationType.UPDATED
    ))
    self.response = dict(
      message=f"Serial {self.info.child_serial_key} unlinked from parent {self.info.parent_serial_key}."
    )

  def _process_inventory(self):
    if not self._ensure_inventory_management_enabled():
      return

    inventory_management_enabled_for_component = self.tx.aql.execute("""
      FOR s IN Serial
      FILTER s._key == @serial_key
      RETURN NOT_NULL(DOCUMENT(Product, s.product_key).manage_inventory, false)
    """, bind_vars=dict(serial_key=self.info.child_serial_key)).next()

    if not inventory_management_enabled_for_component:
      return

    # Get last consumption movement for serial
    try:
      last_serial_consumption_movement = self.tx.aql.execute("""
        FOR m IN movement
        FILTER
          m.serial_key == @serial_key
          && m.type == 'consumption'
        SORT m.timestamp DESC
        LIMIT 1
        RETURN m
      """, bind_vars=dict(serial_key=self.info.child_serial_key)).next()
    except StopIteration:
      raise ValueError('No consumption movement found for serial')


    MovementReversedEvent.create_as_child(self, dict(
      original_movement_key=last_serial_consumption_movement['_key'],
      reason=f"Serial unlinked from {self.info.parent_serial_key}" if self.info.parent_serial_key else f"Serial unlinked from batch {self.info.batch_key}"
    ))