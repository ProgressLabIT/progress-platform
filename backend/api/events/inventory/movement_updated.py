import traceback

from pydantic import Field

from events.inventory.base_inventory import BaseInventoryEvent, BaseInventoryModel
from events.inventory.movement_completed import MovementCompletedEvent
from models.event import EventType, EventInfoModel
from models.inventory import *
from utils.inventory import Queries
from utils.exceptions import InventoryMovementException

class MovementUpdatedEvent(BaseInventoryEvent):
  """Used for updating planned movement"""

  class InfoModel(EventInfoModel):
    movement_key: str = Field(..., alias='_key')
    qt_confirmed: float
    qt_planned: float
    split_into: list[MovementSplitData] | None = []
    position_from: str | None = None
    position_to: str | None = None

  @classmethod
  def get_event_type(cls):
    return EventType.MOVEMENT_UPDATED

  @classmethod
  def get_tx_collections(cls):
    return ['movement', 'is_in_position', 'Serial']


  def apply(self):
    original_movement = self.tx.collection('movement').get(self.info.movement_key)

    # Check if the movement exists and is not completed
    if original_movement is None:
      raise InventoryMovementException(f'Cannot find movement to update')
    if original_movement['status'] == MovementStatus.COMPLETED:
      raise InventoryMovementException(f'Cannot update completed movement')

    try:
      # Handle split movements
      # TODO: consider using multiple events to confirm the initial movement
      # and automatically generate transfers for the splits
      if len(self.info.split_into) > 0:
        if self.info.qt_confirmed >= self.info.qt_planned:
          # If the split is for the whole movement, delete the original movement
          self.tx.collection('movement').delete(self.info.movement_key)
        else:
          # If the split is for a partial movement, subtract the quantity from the original movement
          self.tx.collection('movement').update(dict(
            _key=self.info.movement_key,
            qt_planned=self.info.qt_planned - self.info.qt_confirmed,
            status=MovementStatus.PLANNED,
            qt_confirmed=0
          ))
        # Create new completed movements for the splits
        for split in self.info.split_into:
          MovementCompletedEvent.create_as_child(self, dict(
            movement_key=None,
            movement_type=original_movement['type'],
            product_key=original_movement['product_key'],
            qt_planned=split.qt_planned,
            qt_confirmed=split.qt_confirmed,
            position_from=split.position_from,
            position_to=split.position_to,
            serial_key=split.serial_key,
            serial_code=split.serial_code,
            references=original_movement['references'],
            reason=original_movement['reason'],
            extra=original_movement['extra']
          ))

      # No split, only update the original movement
      elif self.info.qt_confirmed >= self.info.qt_planned:
        MovementCompletedEvent.create_as_child(self, dict(
          movement_key=self.info.movement_key,
          movement_type=original_movement['type'],
          product_key=original_movement['product_key'],
          qt_planned=self.info.qt_planned,
          qt_confirmed=self.info.qt_confirmed,
          position_from=self.info.position_from,
          position_to=self.info.position_to
        ))



      pass
    except Exception as e:
      print(traceback.format_exc())
      self.notify_error(dict(
        notification = InventoryNotificationErrorCode.EXCEPTION,
        error_code = InventoryNotificationType.ERROR,
        error = traceback.format_exc()
      ))
      raise InventoryMovementException(f'Cannot update movements', e, traceback.format_exc())
