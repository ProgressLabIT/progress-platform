import json
import traceback
import copy

from fastapi.encoders import jsonable_encoder
from utils.db import db, model_to_db_dict
from utils.dt import timestamp
from models.serial import Serial, SerialCommandType, SerialNotificationType, SerialNotificationErrorCode
from utils.counter import _generate_counter
from models.form import SerialFormFieldValue
from utils.serial import Queries
from managers.notification_manager import NotificationManager
from models.event import EventModel

from utils.exceptions import (
  SerialNotDeletedError,
  SerialNotUpdatedError,
  SerialNotLinkedError,
  SerialNotCreatedError,
  SerialCodeAlreadyPresent
)


class SerialEventManager:
    __instance = None

    def __init__(self) -> None:
       self.event = None
       self.serial_data = None
       self.tx = None

    @staticmethod
    def getInstance():
      if SerialEventManager.__instance == None:
        SerialEventManager.__instance = SerialEventManager()
      return SerialEventManager.__instance

    def handle_event(self, event, event_command, **event_parameters):
      self.event = event
      self.tx = event.tx
      if (event.info.serial_data != None):
         self.serial_data = jsonable_encoder(Serial(**event.info.serial_data))
      else:
         self.serial_data = None
      match event_command:
        case SerialCommandType.CREATE_FROM_BATCH:
           self.create_from_batch(quantity=event_parameters['quantity'])
        case SerialCommandType.CREATE_AND_FINALIZE:
           self.create_serial(serial_data=self.serial_data, batch_key=None, counter=True, finalize=True)
        case SerialCommandType.FINALIZE_BATCH:
           self.confirm_serials(quantity=event_parameters['quantity'], batch_execution_data=event_parameters['batch_execution_data'])
        case SerialCommandType.STORE_BATCH_DATA:
           self.store_data(quantity=event_parameters['quantity'], batch_execution_data=event_parameters['batch_execution_data'])
        case SerialCommandType.FINALIZE_WO:
           self.release_serials(batch_execution_data=event_parameters['batch_execution_data'])
        case SerialCommandType.UPDATE:
           self.update_serial()
        case SerialCommandType.DELETE:
           self.delete_serial(soft=True)
        case SerialCommandType.UPDATE_DATA_FROM_BATCH:
           self.update_serial_data(step_data=event_parameters['step_data'])
        case SerialCommandType.LINK_BATCH:
           self.link_batch_serial()
        case SerialCommandType.LINK_SERIALS:
           self.link_serials()
        case _:
           print("Error")
      #except:
      #  print(traceback.format_exc())
      #  self.notify_results(dict(
      #      notification = SerialNotificationType.ERROR,
      #      error_code = SerialNotificationErrorCode.EXCEPTION,
      #      error = traceback.format_exc()
      #   ))

    def retrieve_serial_in_batch(self, batch_key):
       cursor = self.tx.aql.execute(
          Queries.GET_BATCH_SERIALS,
          bind_vars=dict(batch_key=batch_key)
        )
       try:
          return [Serial(**t) for t in cursor]
       except StopIteration:
          return []

    def retrieve_serial_in_wo(self, wo_key):
       cursor = self.tx.aql.execute(
          Queries.GET_ALL_SERIALS_IN_WORK_ORDER,
          bind_vars=dict(
            wo_key=wo_key,
          )
        )
       try:
          return [Serial(**t) for t in cursor]
       except:
          return []

    def retrieve_serial_phases_data(self, product_key):
       cursor = self.tx.aql.execute(Queries.GET_PRODUCT_STEPS,
          bind_vars=dict(
            product_key = product_key,
          )
        )
       return [e for e in cursor]

    def create_serial(self, serial_data, batch_key, counter, finalize):
      new_serial_record = Serial(
         **serial_data
      ).dict(by_alias=True)

      #tx = self.tx.begin_transaction(write=['Serial', 'Counter', 'batch_serial'], read=[])
      if new_serial_record['code'] != None and not self.verify_serial_code_free(None, new_serial_record['product_key'], new_serial_record['code']):
         self.notify_results(dict(
            serial = new_serial_record['code'],
            notification = SerialNotificationType.ERROR,
            error_code = SerialNotificationErrorCode.SERIAL_ALREADY_PRESENT,
            error = 'Serial already present'
         ))
         raise SerialCodeAlreadyPresent(f'Cannot create serial, serial code already used')
      try:
         serial_no = "MISSING-COUNTER"
         if counter and new_serial_record['code'] == None:
            if (serial_data['counter_key']):
               serial_no = _generate_counter(self.tx, serial_data['counter_key'])
               new_serial_record['code'] = serial_no
            else:
               self.notify_results(dict(
                  notification = SerialNotificationType.ERROR,
                  error_code = SerialNotificationErrorCode.COUNTER_NOT_DEFINED,
                  error = 'Counter not defined'
                  ))

         if finalize:
            new_serial_record['released'] = timestamp()
         serial_key = self.tx.collection('Serial').insert(new_serial_record, return_new=True)['_key']

         serial_data['_key'] = serial_key

         if batch_key:
            self.tx.collection('batch_serial').insert(dict(
               _from=f'Batch/{batch_key}',
               _to=f'Serial/{serial_key}'))

         #tx.commit_transaction()
         self.notify_results(dict(
            serial_key = serial_data.get("_key"),
            serial = serial_no,
            notification = SerialNotificationType.CREATED
         ))

         self.event.response = dict(
           message="Serial created correctly",
           serial_key=serial_key
         )
      except:
         print(traceback.format_exc())
         self.notify_results(dict(
            serial_key = serial_data.get("_key"),
            notification = SerialNotificationType.ERROR,
            error_code = SerialNotificationErrorCode.EXCEPTION,
            error = traceback.format_exc()
         ))
         raise SerialNotCreatedError(f'Cannot create serial')

    def link_batch_serial(self):
      batch_key = self.event.batch.key
      batch_serials = self.event.info.batch_serials
      new_batch_serial_records = [dict(
         _from=f'Batch/{batch_key}',
         _to=f'Serial/{serial_key}'
      ) for serial_key in batch_serials]

      try:
         self.tx.collection('batch_serial').insert_many(new_batch_serial_records)
         for serial_key in batch_serials:
            self.notify_results(dict(
               serial_key = serial_key,
               notification = SerialNotificationType.UPDATED
            ))
      except:
         print(traceback.format_exc())
         self.notify_results(dict(
            notification = SerialNotificationType.ERROR,
            error_code = SerialNotificationErrorCode.EXCEPTION,
            error = traceback.format_exc()
         ))
         raise SerialNotLinkedError(f'Cannot link serials')

    def link_serials(self):

        serial_link_data = self.event.info.serial_link_data

        booked_serial = []
        for serial_links in serial_link_data:
           if serial_links.to_serial in booked_serial:
              raise SerialNotLinkedError(f'Cannot link serials: multiple usage of the same component')
           booked_serial.append(serial_links.to_serial)

        for serial_links in serial_link_data:
          from_serial = serial_links.from_serial
          to_serial = serial_links.to_serial
          reason = serial_links.reason
          wo_key = serial_links.wo_key
          component_key = serial_links.component_key
          batch_key = serial_links.batch_key
          batch_link_match = dict(_from=f'Batch/{batch_key}', _to=f'Serial/{to_serial}')
          serial_link_match = dict(_from=f'Serial/{from_serial}', _to=f'Serial/{to_serial}')
          try:
             batch_link_cursor = self.tx.collection('contains').find(batch_link_match)
             serial_link_cursor = self.tx.collection('contains').find(serial_link_match)
             if batch_link_cursor.count()>0:
                self.tx.collection('contains').update(dict(
                   _key = batch_link_cursor.next()['_key'],
                   _from=f'Batch/{batch_key}',
                   _to=f'Serial/{to_serial}',
                   replaced=serial_links.replaced,
                   wo_key = wo_key,
                   component_key=component_key,
                   from_serial=from_serial,
                   batch_key=batch_key,
                   reason=reason
                ))
             elif serial_link_cursor.count()>0:
                self.tx.collection('contains').update(dict(
                   _key = serial_link_cursor.next()['_key'],
                   _from=f'Serial/{from_serial}',
                   _to=f'Serial/{to_serial}',
                   replaced=serial_links.replaced,
                   wo_key = wo_key,
                   component_key=component_key,
                   from_serial=from_serial,
                   batch_key=batch_key,
                   reason=reason
                ))
             elif serial_links.link_serial_directly:
                self.tx.collection('contains').insert(dict(
                   _from=f'Serial/{from_serial}',
                   _to=f'Serial/{to_serial}',
                   replaced=False,
                   wo_key = wo_key,
                   component_key=component_key,
                   from_serial=from_serial,
                   batch_key=batch_key,
                   reason=''
                ))
             else:
                self.tx.collection('contains').insert(dict(
                   _from=f'Batch/{batch_key}',
                   _to=f'Serial/{to_serial}',
                   replaced=False,
                   wo_key = wo_key,
                   component_key=component_key,
                   from_serial=from_serial,
                   batch_key=batch_key,
                   reason=''
                ))
          except:
             print(traceback.format_exc())
             self.notify_results(dict(
                notification = SerialNotificationType.ERROR,
                error_code = SerialNotificationErrorCode.EXCEPTION,
                error = traceback.format_exc()
             ))
             raise SerialNotLinkedError(f'Cannot link serials')
        self.notify_results(dict(
            notification = SerialNotificationType.UPDATED
        ))

    def create_from_batch(self, quantity):
       batch_key = self.event.batch.key
       created_by = self.event.info.user_key
       wo_key = self.event.info.work_order_key
       product_key = self.event.info.product_key
       product = self.tx.collection('Product').get(product_key)

       serial_data = Serial()
       counter_key = None
       if 'counter_key' in product:
          setattr(serial_data, 'counter_key', product['counter_key'])
          counter_key = product['counter_key']
       else:
          setattr(serial_data, 'counter_key', None)
       setattr(serial_data, 'product_key', product_key)

       if self.event.job.serialcode_on_batchstart and not counter_key:
          self.notify_results(dict(
             notification = SerialNotificationType.ERROR,
             error_code = SerialNotificationErrorCode.COUNTER_NOT_DEFINED,
             error = 'Counter not defined'
          ))
          raise ValueError(f"Counter not defined for batch {self.event.info.active_batch_key}")

       phases_data = self.retrieve_serial_phases_data(product_key)
       data = []
       for phase in phases_data:
         for step in phase['steps']:
           if 'form_fields' in step:
             for field in step['form_fields']:
               field_data = SerialFormFieldValue()
               setattr(field_data, 'form_field_key', field['_key'])
               setattr(field_data, 'custom_field_key', field['custom_field_key'])
               setattr(field_data, 'phase_key', phase['phase_key'])
               setattr(field_data, 'step_key', step['_key'])
               data.append(field_data)

       setattr(serial_data, 'data', data)
       setattr(serial_data, 'created_by', created_by)
       setattr(serial_data, 'wo_key', wo_key)

       for i in range(int(quantity)):
          self.create_serial(serial_data=serial_data.model_dump(), batch_key=batch_key, counter=self.event.job.serialcode_on_batchstart, finalize=False)

    def verify_serial_code_free(self, serial_key, product_key, serial):
       cursor = self.tx.aql.execute(
          Queries.GET_SERIALS_FOR_SERIAL_CODE,
          bind_vars=dict(
            serial_key=serial_key,
            serial=serial,
            product_key=product_key
          )
        )
       try:
          return len([Serial(**t) for t in cursor])<=0
       except:
        return False

    def update_serial(self):

       try:
           serial = self.tx.collection('Serial').get(self.serial_data.get("_key"))
           if (self.serial_data.get('code') != None):
              can_edit_code = self.tx.collection('Config').get('allow_serial_code_edit')['value']
              if not can_edit_code:
                 self.notify_results(dict(
                    serial = self.serial_data.get('code'),
                    serial_key = self.serial_data.get("_key"),
                    notification = SerialNotificationType.ERROR,
                    error_code = SerialNotificationErrorCode.SERIAL_ALREADY_PRESENT,
                    error = 'Serial code edit not allowed'
                 ))
                 return
              if (self.serial_data.get('code') != None and not self.verify_serial_code_free(serial_key=serial.get("_key"), product_key=serial.get("product_key"), serial=self.serial_data.get('code'))):
                 self.notify_results(dict(
                    serial = self.serial_data.get('code'),
                    serial_key = self.serial_data.get("_key"),
                    notification = SerialNotificationType.ERROR,
                    error_code = SerialNotificationErrorCode.SERIAL_ALREADY_PRESENT,
                    error = 'Serial already present'
                    ))
                 return
              serial['code'] = self.serial_data.get('code')
           if (self.serial_data.get('data') != None):
              serial['data'] = self.serial_data.get('data')
           self.tx.update_document(serial)
       except:
           print(traceback.format_exc())
           self.notify_results(dict(
              serial_key = self.serial_data.get("_key"),
              notification = SerialNotificationType.ERROR,
              error_code = SerialNotificationErrorCode.EXCEPTION,
              error = traceback.format_exc()
           ))
           raise SerialNotUpdatedError(f'Cannot update serial {self.serial_data.get("_key")}')
       self.notify_results(dict(
              serial_key = self.serial_data.get("_key"),
              serial = self.serial_data.get("code"),
              notification = SerialNotificationType.UPDATED
           ))

    def delete_serial(self, soft=True):
        serial_key = self.serial_data.get("_key")
        allow_serial_delete = db.collection('Config').get('allow_serial_delete')
        if (allow_serial_delete == None or allow_serial_delete['value'] == False):
           self.notify_results(dict(
              serial_key = serial_key,
              notification = SerialNotificationType.ERROR,
              error_code = SerialNotificationErrorCode.EXCEPTION,
              error = 'Cannot delete serial because it is not allowed by configuration'
           ))
           raise SerialNotDeletedError(f'Serial {serial_key} cannot be deleted because it is not allowed by configuration')
        try:
           if soft:
              self.tx.collection('Serial').update(dict(_key=serial_key, deleted=True))
           else:
              self.tx.collection('Serial').delete(serial_key)
           self.notify_results(dict(
              serial_key = serial_key,
              notification = SerialNotificationType.DELETED
           ))
        except:
           print(traceback.format_exc())
           self.notify_results(dict(
              serial_key = serial_key,
              notification = SerialNotificationType.ERROR,
              error_code = SerialNotificationErrorCode.EXCEPTION,
              error = traceback.format_exc()
           ))
           raise SerialNotDeletedError(f'Serial {serial_key} got exception while deleting')


    def ensure_quanty(self):
        quantity = self.event.job.active_batch_qt
        wo_key = self.event.info.work_order_key
        serials = self.retrieve_serial_in_wo(wo_key=wo_key)
        if len(serials) > quantity:
           return
        elif len(serials) < quantity:
           quantity = quantity - len(serials)
           self.create_from_batch(quantity)


    def update_serial_data(self, step_data):
      batch_key = self.event.info.active_batch_key
      self.ensure_quanty()
      serials = self.retrieve_serial_in_batch(batch_key=batch_key)
      if (len(serials)==0):
         raise ValueError(f"No serials to update for batch {batch_key}")

      updates = []
      for serial in serials:
         for step in step_data:
            for data in serial.data:
               if step.form_field_key == data.form_field_key:
                  data.value = step.value
                  data.batch_key = step.batch_key
                  data.phase_key = step.phase_key
                  data.step_key = step.step_key
         updates.append(dict(_key=serial.key, data=serial.data))

      try:
         self.tx.collection('Serial').update_many(updates)
         self.notify_results(dict(
            serials = [serial['_key'] for serial in updates],
            notification = SerialNotificationType.UPDATED
         ))
      except:
         print(traceback.format_exc())
         self.notify_results(dict(
            serial_key = serial.get("_key"),
            notification = SerialNotificationType.ERROR,
            error_code = SerialNotificationErrorCode.EXCEPTION,
            error = traceback.format_exc()
         ))

    def confirm_serials(self, quantity, batch_execution_data):
      #tx = self.tx.begin_transaction(write=['Serial', 'Counter'], read=['batch_serial'])

      cursor = self.tx.aql.execute(
         Queries.GET_BATCH_SERIALS,
         bind_vars=dict(batch_key=self.event.info.active_batch_key
      ))


      # JUST IN CASE: Consider only serials to be confirmed to avoid reassigning a new code
      batch_serials = [Serial(**s) for s in cursor if s['code'] is None]
      # Counter key is the same for all serials in the batch
      counter_key = None
      if (batch_serials):
         counter_key = batch_serials[0].counter_key
      else:
         return

      if (counter_key!=None):
         last_phase = self.event.job.last_phase
         now = timestamp()

         for serial in batch_serials:
            serial.code = _generate_counter(self.tx, 'Counter/' + counter_key)
            serial.released = now if last_phase else None
            for step in batch_execution_data:
              for data in serial.data:
                 if step.form_field_key == data.form_field_key:
                    data.value = step.value
                    data.batch_key = step.batch_key
                    data.phase_key = step.phase_key
                    data.step_key = step.step_key
            confirm_serial_match = dict(_from=f'Batch/{self.event.info.active_batch_key}', from_serial=serial.key)
            confirm_serial_update = dict(_from=serial.id)
            self.tx.collection('contains').update_match(confirm_serial_match, confirm_serial_update)

         clean_serial_match = dict(_from=f'Batch/{self.event.info.active_batch_key}')
         self.tx.collection('contains').delete_match(clean_serial_match)

         new = self.tx.collection('Serial').update_many([model_to_db_dict(s) for s in batch_serials], return_new=True)
         #self.tx.commit_transaction()

         for serial in batch_serials:
            self.notify_results(dict(
               serial_key = serial.key,
               serial = serial.code,
               notification = SerialNotificationType.FINALIZED
            ))
      else:
         # Come gestire la notifica di errore?
         self.notify_results(dict(
            notification = SerialNotificationType.ERROR,
            error_code = SerialNotificationErrorCode.COUNTER_NOT_DEFINED,
            error = 'Counter not defined'
         ))
         raise ValueError(f"Counter not defined for batch {self.event.info.active_batch_key}")

    def store_data(self, quantity, batch_execution_data):
      #tx = self.tx.begin_transaction(write=['Serial', 'Counter'], read=['batch_serial'])

      cursor = self.tx.aql.execute(
         Queries.GET_BATCH_SERIALS,
         bind_vars=dict(batch_key=self.event.info.active_batch_key
      ))


      # JUST IN CASE: Consider only serials to be confirmed to avoid reassigning a new code
      batch_serials = [Serial(**s) for s in cursor]

      for serial in batch_serials:
         for step in batch_execution_data:
           for data in serial.data:
              if step.form_field_key == data.form_field_key:
                 data.value = step.value
                 data.batch_key = step.batch_key
                 data.phase_key = step.phase_key
                 data.step_key = step.step_key

         confirm_serial_match = dict(_from=f'Batch/{self.event.info.active_batch_key}', from_serial=serial.key)
         confirm_serial_update = dict(_from=serial.id)
         self.tx.collection('contains').update_match(confirm_serial_match, confirm_serial_update)

      clean_serial_match = dict(_from=f'Batch/{self.event.info.active_batch_key}')
      self.tx.collection('contains').delete_match(clean_serial_match)

      new = self.tx.collection('Serial').update_many([model_to_db_dict(s) for s in batch_serials], return_new=True)
      #self.tx.commit_transaction()

      for serial in batch_serials:
         self.notify_results(dict(
            serial_key = serial.key,
            serial = serial.code,
            notification = SerialNotificationType.UPDATED
         ))

    def release_serials(self, batch_execution_data):

      cursor = self.tx.aql.execute(
         Queries.GET_BATCH_SERIALS,
         bind_vars=dict(batch_key=self.event.info.active_batch_key
      ))
      # JUST IN CASE: Consider only serials to be released to avoid reassigning a new release date
      batch_serials = [Serial(**s) for s in cursor if s['released'] is None]

      now = timestamp()

      for serial in batch_serials:
         serial.released = now
         for step in batch_execution_data:
              for data in serial.data:
                 if step.form_field_key == data.form_field_key:
                    data.value = step.value
                    data.batch_key = step.batch_key
                    data.phase_key = step.phase_key
                    data.step_key = step.step_key
         confirm_serial_match = dict(_from=f'Batch/{self.event.info.active_batch_key}', from_serial=serial.key)
         confirm_serial_update = dict(_from=serial.id)
         self.tx.collection('contains').update_match(confirm_serial_match, confirm_serial_update)

      clean_serial_match = dict(_from=f'Batch/{self.event.info.active_batch_key}')
      self.tx.collection('contains').delete_match(clean_serial_match)

      self.tx.collection('Serial').update_many([model_to_db_dict(s) for s in batch_serials])

      for serial in batch_serials:
         self.notify_results(dict(
            serial_key = serial.key,
            serial = serial.code,
            notification = SerialNotificationType.FINALIZED
         ))

    def can_be_conflated(self, notification_type):
       return notification_type not in [SerialNotificationType.ERROR]

    def notify_results(self, notification):
      notification['subtopic'] = "serial-notification"
      serial_event = copy.deepcopy(self.event.info)
      if 'error' in notification:
        serial_event.event_type = "SERIAL_"+notification['notification']+" ("+notification['error']+")"
      else:
        serial_event.event_type = "SERIAL_"+notification['notification']
      serial_event.serial_key = notification.get('serial_key')
      self.tx.collection('Event').insert(serial_event.model_dump())
      if self.can_be_conflated(notification.get('notification')):
         NotificationManager.getInstance().notifyConflated(subtopic="serial-notification", message=json.dumps(notification), delay=5)
      else:
         NotificationManager.getInstance().notify(key=notification.get('serial_key'), notification=json.dumps(notification))


