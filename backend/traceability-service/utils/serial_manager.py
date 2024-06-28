import asyncio
import threading
import traceback

from asyncio import AbstractEventLoop
from typing import Dict
import json

from fastapi.encoders import jsonable_encoder
from commons.utils.db import db
from commons.models.serial import Serial, SerialEvent, SerialEventType, SerialNotificationType, SerialNotificationErrorCode
from commons.utils.counter import _generate_counter
from commons.kafka_utils.kafka_producer import KafkaProducer
from commons.models.form import SerialFormFieldValue
from commons.utils.serial import Queries
from commons.models.traceability import WIP


class SerialManager:
    __instance = None

    def run(corofn, *args):
        event_loops_for_each_thread: Dict[int, AbstractEventLoop] = {}
        curr_thread_id = threading.current_thread().ident

        if curr_thread_id not in event_loops_for_each_thread:
            event_loops_for_each_thread[curr_thread_id] = asyncio.new_event_loop()

        thread_loop = event_loops_for_each_thread[curr_thread_id]
        coro = corofn(*args)
        return thread_loop.create_task(coro)

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.cancelled = False
        self.loop.create_task(self.poll_loop())
        self.queue = asyncio.Queue(maxsize=100)

    def close(self):
        self.cancelled = True
        self.queue.join()

    async def poll_loop(self):
        while not self.cancelled:
            message = await self.queue.get()
            print(f'> websocket_manager got {message}')
            self.handleMessage(str(message.key()), json.loads(message.value().decode('utf-8')))
        return "DONE!"

    def enqueue(self, message: str):
       self.queue.put_nowait(message)

    @staticmethod
    def getInstance():
      if SerialManager.__instance == None:
        SerialManager.__instance = SerialManager()
      return SerialManager.__instance

    def handleMessage(self, key, serial):
        print(serial)

        try:
          serial_event : SerialEvent = jsonable_encoder(SerialEvent(**serial))
          match serial['operation']:
             case SerialEventType.CREATE_FROM_BATCH:
                self.create_from_batch(serial_event=serial_event)
             case SerialEventType.CREATE_AND_FINALIZE:
                self.create_serial(serial_data=serial_event['serial'], batch_key=None, finalize=True)
             case SerialEventType.FINALIZE_BATCH:
                self.finalize_serial(serial_event=serial_event, batch_key=serial_event['batch_key'], ensure_qt=False)
             case SerialEventType.FINALIZE_WO:
                self.finalize_serial(serial_event=serial_event, batch_key=serial_event['batch_key'], ensure_qt=True)
             case SerialEventType.UPDATE:
                self.update_serial(serial_data=serial_event['serial'])
             case SerialEventType.DELETE:
                self.delete_serial(serial_key=serial_event['serial'].get("_key"), soft=True)
             case SerialEventType.UPDATE_DATA_FROM_BATCH:
                self.update_serial_data(serial_event=serial_event, batch_key=serial_event['batch_key'], step_data=serial_event['step_data'])
             case SerialEventType.LINK_BATCH:
                self.link_batch_serial(batch_key=serial_event['batch_key'], batch_serials=serial_event['batch_serials'])
             case _:
                print("Error")
        except:
          print(traceback.format_exc())
          self.notify_results(dict(
              notification = SerialNotificationType.ERROR,
              error_code = SerialNotificationErrorCode.EXCEPTION,
              error = traceback.format_exc()
           ))

    def retrieve_serial_in_batch(self, batch_key):
       cursor = db.aql.execute(
          Queries.GET_SERIALS_IN_BATCH,
          bind_vars=dict(
            from_id=f'Batch/{batch_key}',
          )
        )
       try:
          return [Serial(**t) for t in cursor]
       except:
          return []

    def retrieve_serial_in_wo(self, wo_key):
       cursor = db.aql.execute(
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
       cursor = db.aql.execute(Queries.GET_PRODUCT_STEPS,
          bind_vars=dict(
            product_key = product_key,
          )
        )
       return [e for e in cursor]

    def create_serial(self, serial_data, batch_key, finalize):

        new_serial_record = Serial(
          **serial_data
        ).dict(by_alias=True)

        tx = db.begin_transaction(write=['Serial', 'Counter', 'batch_serial'], read=[])
        try:
          serial_no = "MISSING-COUNTER"
          if finalize:
            if (serial_data['counter_key']):
              serial_no = _generate_counter(tx, 'Counter/'+serial_data['counter_key'])
              new_serial_record['code'] = serial_no
            else:
              self.notify_results(dict(
                 notification = SerialNotificationType.ERROR,
                 error_code = SerialNotificationErrorCode.COUNTER_NOT_DEFINED,
                 error = 'Counter not defined'
                ))

          new_serial_id = tx.collection('Serial').insert(new_serial_record, return_new=True)['_id']

          serial_key=new_serial_id.split('/')[1]
          serial_data['_key'] = serial_key

          if batch_key:
             tx.collection('batch_serial').insert(dict(
                _from=f'Batch/{batch_key}',
                _to=f'Serial/{serial_key}'))

          tx.commit_transaction()
          self.notify_results(dict(
              serial_key = serial_data.get("_key"),
              serial = serial_no,
              notification = SerialNotificationType.CREATED
           ))
        except:
          print(traceback.format_exc())
          tx.abort_transaction()
          self.notify_results(dict(
              serial_key = serial_data.get("_key"),
              notification = SerialNotificationType.ERROR,
              error_code = SerialNotificationErrorCode.EXCEPTION,
              error = traceback.format_exc()
           ))

    def link_batch_serial(self, batch_key, batch_serials):
       for serial_key in batch_serials:
          try:
             db.collection('batch_serial').insert(dict(
                _from=f'Batch/{batch_key}',
                _to=f'Serial/{serial_key}'))
             self.notify_results(dict(
              serial_key = serial_key,
              notification = SerialNotificationType.UPDATED
           ))
          except:
             print(traceback.format_exc())
             self.notify_results(dict(
                serial_key = serial_key,
                notification = SerialNotificationType.ERROR,
                error_code = SerialNotificationErrorCode.EXCEPTION,
                error = traceback.format_exc()
             ))

    def create_from_batch(self, serial_event):
       batch_key = serial_event['batch_key']
       created_by = serial_event['created_by']
       wo_key = serial_event['wo_key']
       product_key = serial_event['product_key']
       quantity = serial_event['quantity']

       product = db.collection('Product').get(product_key)

       serial_data = Serial()
       setattr(serial_data, 'counter_key', product['counter_id'])
       setattr(serial_data, 'product_key', product_key)

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
          self.create_serial(serial_data=serial_data.dict(), batch_key=batch_key, finalize=False)

    def verify_serial_counter(self, serial_key, serial):
       cursor = db.aql.execute(
          Queries.GET_SERIALS_FOR_SERIAL_NO,
          bind_vars=dict(
            serial_key=serial_key,
            serial=serial
          )
        )
       try:
          return len([Serial(**t) for t in cursor])<=0
       except:
        return False

    def update_serial(self, serial_data):

       if (serial_data.get('code') != None and not self.verify_serial_counter(serial_key=serial_data.get("_key"), serial=serial_data.get('code'))):
          self.notify_results(dict(
              serial = serial_data.get('code'),
              serial_key = serial_data.get("_key"),
              notification = SerialNotificationType.ERROR,
              error_code = SerialNotificationErrorCode.SERIAL_ALREADY_PRESENT,
              error = 'Serial already present'
           ))
          return

       try:
           serial = db.collection('Serial').get(serial_data.get("_key"))
           if (serial_data.get('code') != None):
              serial['code'] = serial_data.get('code')
           serial['data'] = serial_data.get('data')
           db.update_document(serial)
       except:
           print(traceback.format_exc())
           self.notify_results(dict(
              serial_key = serial_data.get("_key"),
              notification = SerialNotificationType.ERROR,
              error_code = SerialNotificationErrorCode.EXCEPTION,
              error = traceback.format_exc()
           ))
       self.notify_results(dict(
              serial_key = serial_data.get("_key"),
              serial = serial_data.get("code"),
              notification = SerialNotificationType.UPDATED
           ))

    def delete_serial(self, serial_key, soft=True):
        try:
           if soft:
              db.collection('Serial').update(dict(_key=serial_key, deleted=True))
           else:
              db.collection('Serial').delete(serial_key)
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

    def ensure_quanty(self, serial_event):
        quantity = serial_event['quantity']
        wo_key = serial_event['wo_key']
        serials = self.retrieve_serial_in_wo(wo_key=wo_key)
        if len(serials) > quantity:
           return
           #for idx, serial in enumerate(serials):
           #   if idx > len(serials) -quantity:
           #      self.delete_serial(serial.key, soft=False)
        elif len(serials) < quantity:
           serial_event['quantity'] = quantity - len(serials)
           self.create_from_batch(serial_event=serial_event)


    def update_serial_data(self, serial_event, batch_key, step_data):
        self.ensure_quanty(serial_event)
        serials = self.retrieve_serial_in_batch(batch_key=batch_key)
        for serial in serials:
           try:
             for step in step_data:
                for data in serial.data:
                   if step.get('form_field_key') == data.form_field_key or step.get('custom_field_key') == data.custom_field_key :
                      data.value = step['value']
             serial_key = serial.key
             db_serial = db.collection('Serial').get(serial_key)
             db_serial['data'] = serial.data
             db.update_document(db_serial)
             self.notify_results(dict(
                 serial = serial.code,
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

    def finalize_serial(self, serial_event, batch_key, ensure_qt):
        if (ensure_qt):
           self.ensure_quanty(serial_event)
        serials = self.retrieve_serial_in_batch(batch_key=batch_key)
        for serial in serials:
           if (serial.code == None):
             tx = db.begin_transaction(write=['Serial', 'Counter', 'batch_serial'], read=[])
             try:
               serial_no = "MISSING-COUNTER"
               if (serial.counter_key!=None):
                  serial_no = _generate_counter(tx, 'Counter/'+serial.counter_key)
               else:
                  self.notify_results(dict(
                     notification = SerialNotificationType.ERROR,
                     error_code = SerialNotificationErrorCode.COUNTER_NOT_DEFINED,
                     error = 'Counter not defined'
                  ))
               serial.code = serial_no
               serial_key = serial.key
               db_serial = tx.collection('Serial').get(serial_key)
               db_serial['code'] = serial_no
               tx.update_document(db_serial)
               tx.commit_transaction()
             except:
                 print(traceback.format_exc())
                 tx.abort_transaction()
                 self.notify_results(dict(
                    serial_key = serial.key,
                    notification = SerialNotificationType.ERROR,
                    error_code = SerialNotificationErrorCode.EXCEPTION,
                    error = traceback.format_exc()
                 ))
             self.notify_results(dict(
                  serial_key = serial.key,
                  serial = serial_no,
                  notification = SerialNotificationType.FINALIZED
               ))

    def notify_results(self, notification):
        try:
           KafkaProducer.getInstance().produce_async(topic="serial_notifications", key=notification.get('serial_key'), value=json.dumps(notification))
        except:
           print(traceback.format_exc())


