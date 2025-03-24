import traceback

from events.serial.base_serial import BaseSerialEvent
from events.inventory.base_inventory import BaseInventoryEvent
from events.inventory.movement_completed import MovementCompletedEvent
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
    job_key: str | None = None
    batch_key: str | None = None
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
    return EventType.SERIAL_LINKED

  def apply(self):

    try:
      # Ensure serial is not already linked
      cursor = self.tx.collection('contains').find(dict(_to=f'Serial/{self.info.child_serial_key}'))
      if cursor.count() > 0:
        # ignore if the link is the same as already recorded
        parent_id = f"Serial/{self.info.parent_serial_key}" if self.info.parent_serial_key else f"Batch/{self.info.batch_key}"
        if cursor.next()['_from'] == parent_id:
          self.response = dict(message="Link already exists")
          return
        else:
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