import traceback
import copy
import json

from models.inventory import InventoryCommandType, InventoryNotificationType, InventoryNotificationErrorCode, InventoryMovement
from fastapi.encoders import jsonable_encoder
from managers.notification_manager import NotificationManager

from utils.exceptions import (
  InventoryMovementException
)


class InventoryEventManager:
    __instance = None

    def __init__(self) -> None:
       self.event = None
       self.tx = None

    @staticmethod
    def getInstance():
      if InventoryEventManager.__instance == None:
        InventoryEventManager.__instance = InventoryEventManager()
      return InventoryEventManager.__instance


    def handle_event(self, event, event_command, **event_parameters):
      self.event = event
      self.tx = event.tx
      match event_command:
        case InventoryCommandType.ADD_MOVEMENT:
           self.add_movement()
        case InventoryCommandType.UPDATE_MOVEMENT:
           ...
        case InventoryCommandType.DELETE_MOVEMENT:
           ...
        case _:
           print("Error")

    def add_movement(self):
      try:
         for movement in self.event.info.movements:
            self.create_movement(movement_data=movement)
      except:
           print(traceback.format_exc())
           self.notify_results(dict(
              notification = InventoryNotificationType.ERROR,
              error_code = InventoryNotificationErrorCode.EXCEPTION,
              error = traceback.format_exc()
           ))
           raise InventoryMovementException(f'Cannot add movements')

    def create_movement(self, movement_data):
       try:
          new_movement_record = InventoryMovement(**movement_data.dict()).dict(by_alias=True)
          movement_key = self.tx.collection('InventoryMovement').insert(dict(new_movement_record), return_new=True)['_key']
          self.tx.collection('is_in_position').insert(dict(
                   _from=movement_data.position_to,
                   _to=f'Product/{movement_data.product_key}'
                ))

          self.notify_results(dict(
             movement_key = movement_key,
             notification = InventoryNotificationType.MOVEMENT_ADDED,
             message="Movement created correctly",
          ))
       except:
          print(traceback.format_exc())
          self.notify_results(dict(
             notification = InventoryNotificationType.ERROR,
             error_code = InventoryNotificationErrorCode.EXCEPTION,
             error = traceback.format_exc()
          ))
          raise InventoryMovementException(f'Cannot add movement')

    def can_be_conflated(self, notification_type):
       return notification_type not in [InventoryNotificationType.ERROR]

    def notify_results(self, notification):
      notification['subtopic'] = "inventory-notification"
      inventory_event = copy.deepcopy(self.event.info)
      if 'error' in notification:
        inventory_event.event_type = "INVENTORY_"+notification['notification']+" ("+notification['error']+")"
      else:
        inventory_event.event_type = "INVENTORY_"+notification['notification']
      inventory_event.movement_key = notification.get('movement_key')
      self.tx.collection('Event').insert(inventory_event.model_dump())
      if self.can_be_conflated(notification.get('notification')):
         NotificationManager.getInstance().notifyConflated(subtopic="inventory-notification", message=json.dumps(notification), delay=5)
      else:
         NotificationManager.getInstance().notify(key=notification.get('movement_key'), notification=json.dumps(notification))
