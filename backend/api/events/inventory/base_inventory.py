import traceback
import copy
import json

from typing import Any
from events.base_event import BaseEvent
from models.event import EventModel
from abc import ABC, abstractmethod
from pydantic import model_validator
from models.inventory import *
from models.serial import Serial
from fastapi.encoders import jsonable_encoder
from models.product import ProductFull
from managers.notification_manager import NotificationManager

from utils.exceptions import (
  InventoryMovementException
)

class BaseInventoryModel(EventModel):
    # Inventory fields
    movement: InventoryMovementNew | InventoryMovementUpdate | None = None
    movement_list: MovementListNew | None = None
    movement_key: str | None = None
    # supplier_key: Any | None = None

class BaseInventory(BaseEvent, ABC):
    event_data: BaseInventoryModel

    product: ProductFull | None = None

    def adjust_inventory(self):
       match self.info.movement.type:
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

    @abstractmethod
    def apply(self):
      pass

    @abstractmethod
    def set_model(self, base_model: EventModel):
      pass

    def validate_event(self):
      enable_inventory_management = self.tx.collection('Config').get('enable_inventory_management') or False
      if not enable_inventory_management:
        self.not_handled_response('Inventory management is not enabled')
        return False
      return super().validate_event()

    def get_write_collections(self):
      return list(set(super().get_write_collections() + [
        'is_in_position',
        'Serial',
        'Product',
        'Position',
        'movement',
        'Event'
      ]))

    def handle_production(self):
      product_key = self.info.movement.product_key
      serial_key = self.info.movement.serial_key

      if serial_key is not None:
        self.tx.collection('is_in_position').insert(Inventory(
          product_id=f'Product/{product_key}',
          position_id=self.info.movement.position_to,
          quantity = 1,
          serial_key = serial_key
        ))
      else:
        try:
          existing_inventory = self.tx.collection('is_in_position').find(dict(
            _from=f'Product/{product_key}',
            _to=self.info.movement.position_to,
            serial_key=None
          )).next()

          final_qty = existing_inventory['quantity'] + self.info.movement.qt_confirmed

          self.tx.collection('is_in_position').update(dict(
            _key = existing_inventory['_key'],
            quantity=final_qty
          ))

        except StopIteration: # No existing inventory found, create new inventory
          self.tx.collection('is_in_position').insert(Inventory(
            product_id=f'Product/{product_key}',
            position_id=self.info.movement.position_to,
            quantity=self.info.movement.qt_confirmed,
            owned=True
          ))

    def handle_consumption(self):
       #TODO: duplicate code, refactor while handling production events
       product_key = self.info.movement.product_key
       record_match = dict(_from=f'Product/{product_key}', _to=self.info.movement.position_from)
       if self.info.movement.serial_key is not None:
          record_match['serial_key'] = self.info.movement.serial_key
       else:
          record_match['serial_key'] = None
       position_link_cursor = self.tx.collection('is_in_position').find(record_match)
       if (position_link_cursor.count()>0):
          position_status = position_link_cursor.next()
          final_qty = position_status['quantity'] - self.info.movement.qt_confirmed
          if (final_qty<0):
            raise InventoryMovementException(f'Cannot consume: quantity not enough in the provided position')
          elif (final_qty==0):
            self.tx.collection('is_in_position').delete_match(filters=dict(_key = position_status['_key']))
          else:
             self.tx.collection('is_in_position').update(dict(
               _key = position_status['_key'],
               quantity=final_qty
             ))
       else:
         raise InventoryMovementException(f'Cannot find product to consume in the provided position')

    def _handle_receipt_with_traceability(self):
      serial_code = self.info.movement.serial_code or ''
      serial_code_provided = len(serial_code) > 0

      if not serial_code_provided:
        raise InventoryMovementException(f'Serial code is required for receipts of products with traceability')

      product_key = self.info.movement.product_key

      # First try to find an existing serial
      serial_cursor = self.tx.collection('Serial').find(dict(
        code=serial_code,
        product_key=product_key,
        deleted=False
      ))
      if serial_cursor.count() == 0:
         # Serial does not exist, create new serial
        new_serial_key = self.tx.collection('Serial').insert(Serial(
          product_key=product_key,
          code=serial_code,
          created=self.info.timestamp,
          released=self.info.timestamp,
          available=self.info.movement.status == MovementStatus.COMPLETED,
          user_key=self.info.user_key,
        ))['_key']
        self.info.movement.serial_key = new_serial_key

      else:
        # Serial exists, check if it's in inventory
        existing_serial = serial_cursor.next()
        self.info.movement.serial_key = existing_serial['_key']

        inventory_exists = self.tx.collection('is_in_position').find(dict(
          serial_key=existing_serial['_key']
        )).count() > 0

        if inventory_exists:
          raise InventoryMovementException(f'Serial is already in inventory')

      if self.info.movement.status == MovementStatus.COMPLETED:
        new_inventory_record = self.tx.collection('is_in_position').insert(Inventory(
          product_id = 'Product/' + product_key,
          position_id = self.info.movement.position_to,
          serial_key = self.info.movement.serial_key,
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

      self._get_product()

      product_requires_serial = self.product.get('traceability_level', False)

      # SCENARIO 1: Receipt of product with traceability
      if product_requires_serial:
        self._handle_receipt_with_traceability()
        return

      # SCENARIO 2: Receipt of product without traceability.
      # Update inventory only if the movement is confirmed

      if self.info.movement.status == MovementStatus.COMPLETED:
        record_match = dict(_from=f'Product/{self.product.key}', _to=self.info.movement.position_to)
        position_link_cursor = self.tx.collection('is_in_position').find(record_match)
        if (position_link_cursor.count()>0):
          position_status = position_link_cursor.next()
          final_qty = position_status['quantity'] + self.info.movement.qt_confirmed
          self.tx.collection('is_in_position').update(dict(
            _key = position_status['_key'],
            quantity=final_qty
          ))
        else: # No existing inventory found, create new inventory
          self.tx.collection('is_in_position').insert(Inventory(
            product_id=f'Product/{self.product.key}',
            position_id=self.info.movement.position_to,
            quantity=self.info.movement.qt_confirmed,
            owned=True
          ))

    def handle_shipment(self):
      self._get_product()

      product_requires_serial = self.product.get('traceability_level', False)

      # SCENARIO 1: Receipt of product with traceability
      if product_requires_serial:
        serial_code = self.info.movement.serial_code
        serial_key = self.info.movement.serial_key
        serial_provided = any([serial_code, serial_key])

        if serial_key is None:
          if serial_code is None:
            self.info.movement.serial_code = 'NONE'
          else:
            try:
              serial_key = self.tx.collection('Serial').find(dict(
                code=serial_code,
                product_key=self.product.key,
                deleted=False
              )).next()['_key']
              self.info.movement.serial_key = serial_key
            except StopIteration:
              raise InventoryMovementException(f'Serial {serial_code} not found')
        else:
          if not self.tx.collection('Serial').has(serial_key):
            raise InventoryMovementException(f'Serial {serial_key} not found')

      if self.info.movement.status == MovementStatus.COMPLETED:
        record_match = dict(
          _from=f'Product/{self.product.key}',
          _to=self.info.movement.position_from,
          serial_key=getattr(self.info.movement, 'serial_key', None)
        )
        position_link_cursor = self.tx.collection('is_in_position').find(record_match)
        if (position_link_cursor.count()>0):
          position_status = position_link_cursor.next()
          final_qty = position_status['quantity'] - self.info.movement.qt_confirmed
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
          raise InventoryMovementException(f'Cannot find product inventory to ship')

    def handle_transfer(self):
      """
      - Remove inventory from start position
        - decrease quantity, if remaining quantity is 0, remove the record
      - Add inventory to end position
        - add quantity/serial
      """
      movement = InventoryMovement(**self.info.movement.model_dump())


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
          serial_key=movement.serial_key
        ))
      else:
        destination_match = dict(_from='Product/' + movement.product_key, _to=movement.position_to)
        try:
          existing_inventory = self.tx.collection('is_in_position').find(destination_match).next()
          final_qty = existing_inventory['quantity'] + movement.qt_confirmed
          self.tx.collection('is_in_position').update(dict(
            _key = existing_inventory['_key'],
            quantity=final_qty
          ))
        except StopIteration: # No existing inventory found, create new inventory
          self.tx.collection('is_in_position').insert(dict(
            _from='Product/' + movement.product_key,
            _to=movement.position_to,
            quantity=movement.qt_confirmed,
            owned=True,
          ))


    def handle_adjustment(self):
      product_key = self.info.movement.product_key
      record_match = dict(_from=f'Product/{product_key}', _to=self.info.movement.position_from)
      if self.info.movement.serial_key is not None:
        record_match['serial_key'] = self.info.movement.serial_key
      else:
        record_match['serial_key'] = None
      position_link_cursor = self.tx.collection('is_in_position').find(record_match)
      try:
        position_status = position_link_cursor.next()
        final_qty = position_status['quantity'] + self.info.movement.qt_confirmed
        if final_qty < 0:
          raise InventoryMovementException(f'Cannot adjust inventory: quantity cannot be negative')
        elif final_qty == 0:
          self.tx.collection('is_in_position').delete(position_status['_key'])
        else:
          self.tx.collection('is_in_position').update(dict(
            _key = position_status['_key'],
            quantity=final_qty
          ))
      except StopIteration: # No existing inventory found, create new inventory
        if self.info.movement.qt_confirmed > 0:
          self.tx.collection('is_in_position').insert(dict(
            _from='Product/' + product_key,
            _to=self.info.movement.position_from,
            quantity=self.info.movement.qt_confirmed,
            serial_key=self.info.movement.serial_key,
            owned=True,
          ))
        else:
          raise InventoryMovementException(f'Cannot adjust inventory: quantity cannot be negative')
      except Exception as e:
        raise Exception(f'Error adjusting inventory', e)


    def _get_product(self):
      if self.info.movement is not None and self.info.movement.product_key is not None:
        product_cursor = self.tx.collection('Product').get(self.info.movement.product_key)
        if product_cursor.count() > 0:
          self.product = product_cursor.next()

      if self.info.movement is not None and self.info.movement.product_code is not None:
        product_cursor = self.tx.collection('Product').find(dict(
          code=self.info.movement.product_code
        ))
        if product_cursor.count() > 0:
          self.product = product_cursor.next()

      if self.product is None:
        raise InventoryMovementException(f'Product not found')


    def can_be_conflated(self, notification_type):
       return notification_type not in [InventoryNotificationType.ERROR]

    def notify_results(self, notification):
      notification['subtopic'] = "inventory-notification"
      inventory_event = copy.deepcopy(self.info)
      if 'error' in notification:
        inventory_event.event_type = "INVENTORY_"+notification['notification']+" ("+notification['error']+")"
      else:
        inventory_event.event_type = "INVENTORY_"+notification['notification']
      inventory_event.movement_key = notification.get('movement_key')
      #self.tx.collection('Event').insert(inventory_event.model_dump())
      if self.can_be_conflated(notification.get('notification')):
         NotificationManager.getInstance().notifyConflated(subtopic="inventory-notification", message=json.dumps(notification), delay=5)
      else:
         NotificationManager.getInstance().notify(key=notification.get('movement_key'), notification=json.dumps(notification))



    def add_inventory(self):
      """
      - Add inventory to a position
      - Add serial to a position
      """
      ...

    def remove_inventory(self):
      ...




