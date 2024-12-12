import traceback
import copy
import json

from models.inventory import InventoryCommandType, InventoryNotificationType, InventoryNotificationErrorCode, InventoryMovement, InventoryMovementType
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
        movement_data=self.event.info.movement
        new_movement_record = InventoryMovement(**movement_data.dict()).dict(by_alias=True)
        self.adjust_inventory(new_movement_record, new_movement_record['type'])
        movement_key = self.tx.collection('movement').insert(dict(new_movement_record), return_new=True)['_key']
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
        raise InventoryMovementException(f'Cannot add movements')

    def adjust_inventory(self, new_movement_record, type):
       match type:
          case InventoryMovementType.RECEIPT:
             return self.handle_receipt(new_movement_record)
          case InventoryMovementType.SHIPMENT:
             return self.handle_shipment(new_movement_record)
          case InventoryMovementType.ADJUSTMENT:
             return self.handle_adjustment(new_movement_record)
          case _:
            raise InventoryMovementException(f'Invalid movement type')

    def handle_receipt(self, new_movement_record):
      product_key = new_movement_record['product_key']
      record_match = dict(_from=f'Product/{product_key}', _to=new_movement_record['_to'])
      if ('serial_key' in new_movement_record):
         record_match['serial_key'] = new_movement_record['serial_key']
      else:
         record_match['serial_key'] = None
      position_link_cursor = self.tx.collection('is_in_position').find(record_match)
      if (position_link_cursor.count()>0):
         position_status = position_link_cursor.next()
         final_qty = position_status['quantity'] + new_movement_record['qt_confirmed']
         self.tx.collection('is_in_position').update(dict(
              _key = position_status['_key'],
              quantity=final_qty
          ))
      else:
        self.tx.collection('is_in_position').insert(dict(
              _from=f'Product/{product_key}',
              _to=new_movement_record['_to'],
              quantity=new_movement_record['qt_confirmed'],
              owned=True,
              date_received=new_movement_record['end'],
              serial_key=new_movement_record['serial_key']
          ))

    def handle_shipment(self, new_movement_record):
      product_key = new_movement_record['product_key']
      record_match = dict(_from=f'Product/{product_key}', _to=new_movement_record['_from'])
      if ('serial_key' in new_movement_record):
         record_match['serial_key'] = new_movement_record['serial_key']
      else:
         record_match['serial_key'] = None
      position_link_cursor = self.tx.collection('is_in_position').find(record_match)
      if (position_link_cursor.count()>0):
         position_status = position_link_cursor.next()
         final_qty = position_status['quantity'] - new_movement_record['qt_confirmed']
         if (final_qty<0):
            raise InventoryMovementException(f'Cannot ship: quantity not enough')
         self.tx.collection('is_in_position').update(dict(
              _key = position_status['_key'],
              quantity=final_qty
          ))
      else:
        raise InventoryMovementException(f'Cannot find product to ship')

    def handle_adjustment(self, new_movement_record):
      product_key = new_movement_record['product_key']
      record_match = dict(_from=f'Product/{product_key}', _to=new_movement_record['_from'])
      if ('serial_key' in new_movement_record):
         record_match['serial_key'] = new_movement_record['serial_key']
      else:
         record_match['serial_key'] = None
      position_link_cursor = self.tx.collection('is_in_position').find(record_match)
      if (position_link_cursor.count()>0):
         position_status = position_link_cursor.next()
         final_qty = new_movement_record['qt_confirmed']
         self.tx.collection('is_in_position').update(dict(
              _key = position_status['_key'],
              quantity=final_qty
          ))
      else:
        raise InventoryMovementException(f'Cannot find product to adjust')


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
