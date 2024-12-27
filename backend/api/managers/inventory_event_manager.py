import traceback
import copy
import json

from models.inventory import *
from models.serial import Serial
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
           raise InventoryMovementException(f'Invalid inventory event command')

    def add_movement(self):
      try:
        movement_data=self.event.info.movement
        self.adjust_inventory()
        new_movement_record = InventoryMovement(**movement_data.model_dump())
        movement_key = self.tx.collection('movement').insert(new_movement_record)['_key']
        self.notify_results(dict(
           movement_key = movement_key,
           notification = InventoryNotificationType.MOVEMENT_ADDED,
           message="Movement created correctly",
        ))
      except Exception as e:
        print(traceback.format_exc())
        self.notify_results(dict(
           notification = InventoryNotificationErrorCode.EXCEPTION,
           error_code = InventoryNotificationType.ERROR,
           error = traceback.format_exc()
        ))
        raise InventoryMovementException(f'Cannot add movements', e, traceback.format_exc())

    def adjust_inventory(self):
       match self.event.info.movement.type:
          case InventoryMovementType.RECEIPT:
             return self.handle_receipt()
          case InventoryMovementType.SHIPMENT:
             return self.handle_shipment()
          case InventoryMovementType.ADJUSTMENT:
             return self.handle_adjustment()
          case InventoryMovementType.TRANSFER:
             return self.handle_transfer()
          case InventoryMovementType.CONSUMPTION:
             return self.handle_consumption()
          case InventoryMovementType.PRODUCTION:
             return self.handle_production()
          case _:
            raise InventoryMovementException(f'Invalid movement type')

    def handle_production(self):
       self.handle_receipt(self.event.info.movement)

    def handle_consumption(self):
       #TODO: duplicate code, refactor while handling production events
       product_key = self.event.info.movement.product_key
       record_match = dict(_from=f'Product/{product_key}', _to=self.event.info.movement.position_from)
       if self.event.info.movement.serial_key is not None:
          record_match['serial_key'] = self.event.info.movement.serial_key
       else:
          record_match['serial_key'] = None
       position_link_cursor = self.tx.collection('is_in_position').find(record_match)
       if (position_link_cursor.count()>0):
          position_status = position_link_cursor.next()
          final_qty = position_status['quantity'] - self.event.info.movement.qt_confirmed
          if (final_qty<0):
             raise InventoryMovementException(f'Cannot consume: quantity not enough')
          elif (final_qty==0):
           self.tx.collection('is_in_position').delete_match(filters=dict(_key = position_status['_key']))
          else:
             self.tx.collection('is_in_position').update(dict(
               _key = position_status['_key'],
               quantity=final_qty
             ))
       else:
         raise InventoryMovementException(f'Cannot find product to consume')


    def _handle_receipt_with_traceability(self):
      serial_code = self.event.info.movement.serial_code or ''
      serial_code_provided = len(serial_code) > 0

      if not serial_code_provided:
        raise InventoryMovementException(f'Serial code is required for receipts of products with traceability')

      product_key = self.event.info.movement.product_key
      serial_exists = self.tx.collection('Serial').find(dict(
        code=serial_code,
        product_key=product_key,
        deleted=False
      )).count() > 0

      if serial_exists:
        raise InventoryMovementException(f'Serial already exists')

      # Create serial
      # TODO: Use SerialEventManager to create serial
      # TODO: Update serials as available when confirming planned movement
      new_serial_key = self.tx.collection('Serial').insert(Serial(
        product_key=product_key,
        code=serial_code,
        created=self.event.info.timestamp,
        released=self.event.info.timestamp,
        available=self.event.info.movement.status == MovementStatus.COMPLETED,
        user_key=self.event.info.user_key,
      ))['_key']

      self.event.info.movement.serial_key = new_serial_key


      if self.event.info.movement.status == MovementStatus.COMPLETED:
        new_inventory_record = self.tx.collection('is_in_position').insert(Inventory(
          product_id = 'Product/' + product_key,
          position_id = self.event.info.movement.position_to,
          serial_key = new_serial_key,
          quantity = 1
        ))

    def handle_receipt(self):
      """
      # SCENARIO 1: Receipt of product with traceability
      - Ensure serial code is provided
      - Create serial if movement is planned, serial is released, but not available
      - Create new inventory record

      # SCENARIO 2: Receipt of product with no traceability
      - Identify if inventory record (product/position) exists
      - Update quantity if it exists
      - Create new inventory record if it doesn't exist
      - Ignore serial code if provided
      """
      # TODO: handle serial creation if product requires it

      product_key = self.event.info.movement.product_key

      try:
        product_record = self.tx.collection('Product').get(product_key)
      except StopIteration:
        raise InventoryMovementException(f'Product not found')

      product_requires_serial = product_record.get('traceability_level', False)

      # SCENARIO 1: Receipt of product with traceability
      if product_requires_serial:
        self._handle_receipt_with_traceability()
        return

      # SCENARIO 2: Receipt of product without traceability.
      # Update inventory only if the movement is confirmed

      if self.event.info.movement.status == MovementStatus.COMPLETED:
        record_match = dict(_from=f'Product/{product_key}', _to=self.event.info.movement.position_to)
        position_link_cursor = self.tx.collection('is_in_position').find(record_match)
        if (position_link_cursor.count()>0):
          position_status = position_link_cursor.next()
          final_qty = position_status['quantity'] + self.event.info.movement.quantity
          self.tx.collection('is_in_position').update(dict(
            _key = position_status['_key'],
            quantity=final_qty
          ))
        else:
          self.tx.collection('is_in_position').insert(Inventory(
            product_id=f'Product/{product_key}',
            position_id=self.event.info.movement.position_to,
            quantity=self.event.info.movement.quantity,
            owned=True
          ))

    def handle_shipment(self):
      product_key = self.event.info.movement.product_key
      record_match = dict(_from=f'Product/{product_key}', _to=self.event.info.movement.position_from)
      if ('serial_key' in self.event.info.movement):
         record_match['serial_key'] = self.event.info.movement.serial_key
      else:
         record_match['serial_key'] = None
      position_link_cursor = self.tx.collection('is_in_position').find(record_match)
      if (position_link_cursor.count()>0):
         position_status = position_link_cursor.next()
         final_qty = position_status['quantity'] - self.event.info.movement.qt_confirmed
         if (final_qty<0):
            raise InventoryMovementException(f'Cannot ship: quantity not enough')
         elif (final_qty==0):
          self.tx.collection('is_in_position').delete_match(filters=dict(_key = position_status['_key']))
         else:
            self.tx.collection('is_in_position').update(dict(
              _key = position_status['_key'],
              quantity=final_qty
            ))
      else:
        raise InventoryMovementException(f'Cannot find product to ship')

    def handle_transfer(self):
      """
      - Remove inventory from start position
        - decrease quantity, if remaining quantity is 0, remove the record
      - Add inventory to end position
        - add quantity/serial
      """
      movement = InventoryMovement(**self.event.info.movement)


      # CONTAINER TRANSFER ======================================================
      # the product is not moved, only the position hierarchy is changed
      if movement.product_key is None and movement.serial_key is None and movement.position_from is not None:
        position = self.tx.collection('Position').get(movement.position_from)
        if position['fixed']:
          raise InventoryMovementException(f'Cannot transfer fixed position')
        match = dict(_from=movement.position_from)
        update = dict(_to=movement.position_to)
        self.tx.collection('is_in_position').update_match(match, update)
        return

      # PRODUCT TRANSFER ======================================================
      # the product is moved, and the inventory record (is_in_position) is updated
      inventory_match = dict(_from='Product/' + movement.product_key, _to=movement.position_from)
      if movement.serial_key is not None:
        inventory_match['serial_key'] = movement.serial_key
        movement.qt_confirmed = 1

      try:
        current_inventory_record = self.tx.collection('is_in_position').find(inventory_match).next()
      except StopIteration:
        raise InventoryMovementException(f'Cannot find inventory to transfer')

      final_qty = current_inventory_record['quantity'] - movement.qt_confirmed
      if final_qty == 0:
        self.tx.collection('is_in_position').delete_match(filters=inventory_match)
      else:
        self.tx.collection('is_in_position').update(dict(
          _key = current_inventory_record['_key'],
          quantity=final_qty
        ))

      # Update inventory to end position
      if movement.serial_key is not None:
        self.tx.collection('is_in_position').insert(dict(
          _from='Product/' + movement.product_key,
          _to=movement.position_to,
          quantity=1,
          owned=True,
          date_received=movement.end,
          serial_key=movement.serial_key
        ))
      else:
        self.tx.collection('is_in_position').insert(dict(
          _from='Product/' + movement.product_key,
          _to=movement.position_to,
          quantity=movement.qt_confirmed,
          owned=True,
          date_received=movement.end,
        ))


    def handle_adjustment(self):
      product_key = self.event.info.movement.product_key
      record_match = dict(_from=f'Product/{product_key}', _to=self.event.info.movement.position_from)
      if self.event.info.movement.serial_key is not None:
         record_match['serial_key'] = self.event.info.movement.serial_key
      else:
         record_match['serial_key'] = None
      position_link_cursor = self.tx.collection('is_in_position').find(record_match)
      if (position_link_cursor.count()>0):
         position_status = position_link_cursor.next()
         final_qty = self.event.info.movement.qt_confirmed
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
