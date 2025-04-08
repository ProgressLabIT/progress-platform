import traceback

from events.serial.base_serial import BaseSerialEvent
from events.inventory.base_inventory import BaseInventoryEvent
from events.inventory.movement_completed import MovementCompletedEvent
from events.serial.serial_unlinked import SerialUnlinkedEvent
from models.event import EventInfoModel, EventType
from models.inventory import InventoryMovementType, InventoryMovementReferences, MovementStatus
from models.serial import (
  SerialLink,
  SerialNotificationErrorCode,
  SerialNotificationType,
)
from utils.exceptions import SerialNotLinkedError
from utils.inventory import Queries as InventoryQueries

class SerialLinkedEvent(BaseSerialEvent, BaseInventoryEvent):
  """
  This event is used to link components to their parent, using the `contains` edge collection.
  The parent can be a specific product serial or batch in case of work order without traceability enabled.
  """

  class InfoModel(EventInfoModel):
    child_serial_key: str
    parent_serial_key: str | None = None
    wo_key: str | None = None
    component_key: str | None = None
    batch_key: str | None = None
    phase_key: str | None = None
    job_key: str | None = None
    process_inventory: bool | None = True
    replace_existing: bool | None = None

  @classmethod
  def get_tx_collections(cls):
    return [
      'contains',
      'is_in_position',
      'movement',
      'Serial',
      'is_in_position',
      'movement',
    ]


  @classmethod
  def get_event_type(cls):
    return EventType.SERIAL_LINKED

  def apply(self):

    try:
      # Handle existing links
      cursor = self.tx.collection('contains').find(dict(_to=f'Serial/{self.info.child_serial_key}', replaced=False))
      if cursor.count() > 0:
        # ignore if the link is the same as already recorded
        record = cursor.next()
        parent_id = f"Serial/{self.info.parent_serial_key}" if self.info.parent_serial_key else f"Batch/{self.info.batch_key}"
        if record['_from'] == parent_id:
          if record.get('confirmed', True):
            # if the link is already confirmed, ignore
            self.response = dict(message="Link already exists")
            return
          else:
            # if the link is temporary, confirm it
            self.tx.collection('contains').update(record, dict(confirmed=True))
            self.response = dict(message="Temporary link confirmed")
            return
        else:
          if self.info.replace_existing:
            # Unlink from previous parent. No need to process inventory as it will be linked again
            self.info.process_inventory = False
            SerialUnlinkedEvent.create_as_child(self, dict(
              child_serial_key=self.info.child_serial_key,
              parent_serial_key=record['_from'].split('/')[-1],
              process_inventory=False,
            ))
          else:
            # if the link is to a different parent, raise an error
            raise ValueError('Cannot link serials: component already linked to a different parent')

      # Link to batch
      if self.info.parent_serial_key is None:
        # Ensure work order doesn't have traceability enabled
        if self.tx.collection('WorkOrder').get(self.info.wo_key).get('traceability_level', None) is not None:
          raise ValueError('You must provide a parent serial to link components to for this work order')

        else:
          self.tx.collection('contains').update(SerialLink(
            **self.info.model_dump(),
            confirmed=True,
            _from=f'Batch/{self.info.batch_key}',
            _to=f'Serial/{self.info.child_serial_key}'
          ))

      # Link to parent serial
      else:
        self.tx.collection('contains').insert(SerialLink(
          **self.info.model_dump(),
          confirmed=True,
          _from=f'Serial/{self.info.parent_serial_key}',
          _to=f'Serial/{self.info.child_serial_key}'
        ))

      if self.info.process_inventory:
        self._process_inventory()

    except Exception as e:
      print(traceback.format_exc())
      self.notify_results(dict(
        notification=SerialNotificationType.ERROR,
        error_code=SerialNotificationErrorCode.EXCEPTION,
        error=traceback.format_exc()
      ))
      raise SerialNotLinkedError('Cannot link serials') from e

    self.notify_results(dict(
      notification=SerialNotificationType.UPDATED
    ))
    self.response = dict(
      message="Serial linked correctly"
    )


  def _process_inventory(self):
    # Validate configurations
    if not self._ensure_inventory_management_enabled():
      return

    inventory_management_enabled_for_component = self.tx.aql.execute("""
      FOR s IN Serial
      FILTER s._key == @serial_key
      RETURN NOT_NULL(DOCUMENT(Product, s.product_key).manage_inventory, false)
    """, bind_vars=dict(serial_key=self.info.child_serial_key)).next()

    if not inventory_management_enabled_for_component:
      return

    # Get serial position
    try:
      serial_inventory = self.tx.collection('is_in_position').find(dict(serial_key=self.info.child_serial_key)).next()
    except StopIteration:
      raise ValueError('Serial is not in inventory')

    consumption_position_key = serial_inventory['_to'].split('/')[-1]

    # Create movement completed event
    MovementCompletedEvent.create_as_child(self, dict(
      product_key=self.info.component_key,
      serial_key=self.info.child_serial_key,
      qt_planned=1,
      qt_confirmed=1,
      position_from=consumption_position_key,
      movement_type=InventoryMovementType.CONSUMPTION,
      status=MovementStatus.COMPLETED,
      reason=f"Serial linked to {self.info.parent_serial_key}" if self.info.parent_serial_key else f"Serial linked to batch {self.info.batch_key}"
    ))