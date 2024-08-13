import asyncio
import json
import threading
import traceback

from asyncio import AbstractEventLoop
from datetime import datetime as dt
from typing import Dict

from fastapi.encoders import jsonable_encoder
from commons.utils.db import db, model_to_db_dict
from commons.utils.dt import timestamp
from commons.models.serial import Serial, SerialEvent, SerialEventType, SerialNotificationType, SerialNotificationErrorCode
from commons.utils.counter import _generate_counter
from commons.kafka_utils.kafka_producer import KafkaProducer
from commons.models.form import SerialFormFieldValue
from commons.utils.serial import Queries
from commons.models.traceability import WIP
from commons.models.product import TraceabilityLevel


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

    async def close(self):
        self.cancelled = True
        await self.queue.join()

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
                self.confirm_serials(serial_event=serial_event)
             case SerialEventType.FINALIZE_WO:
                self.release_serials(serial_event=serial_event)
             case SerialEventType.UPDATE:
                self.update_serial(serial_data=serial_event['serial'])
             case SerialEventType.DELETE:
                self.delete_serial(serial_key=serial_event['serial'].get("_key"), soft=True)
             case SerialEventType.UPDATE_DATA_FROM_BATCH:
                self.update_serial_data(serial_event=serial_event, batch_key=serial_event['batch_key'], step_data=serial_event['step_data'])
             case SerialEventType.LINK_BATCH:
                self.link_batch_serial(batch_key=serial_event['batch_key'], batch_serials=serial_event['batch_serials'])
             case SerialEventType.LINK_SERIALS:
                self.link_serials(serial_link_data=serial_event['serial_link_data'])
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
          Queries.GET_ALL_SERIALS_IN_BATCH,
          bind_vars=dict(
            from_id=f'Batch/{batch_key}',
          )
        )
       try:
          return [Serial(**t) for t in cursor]
       except StopIteration:
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
         if finalize and new_serial_record['code'] == None:
            if (serial_data['counter_key']):
               serial_no = _generate_counter(tx, serial_data['counter_key'])
               new_serial_record['code'] = serial_no
            else:
               self.notify_results(dict(
                  notification = SerialNotificationType.ERROR,
                  error_code = SerialNotificationErrorCode.COUNTER_NOT_DEFINED,
                  error = 'Counter not defined'
                  ))

         serial_key = tx.collection('Serial').insert(new_serial_record, return_new=True)['_key']

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

    def link_serials(self, serial_link_data):

        for serial_links in serial_link_data:
          from_serial = serial_links['from_serial']
          to_serial = serial_links['to_serial']
          reason = serial_links['reason']
          wo_key = serial_links['wo_key']
          component_key = serial_links['component_key']
          batch_key = serial_links['batch_key']
          link_match = dict(_from=f'Serial/{from_serial}', _to=f'Serial/{to_serial}')
          try:
             link_cursor = db.collection('contains').find(link_match)
             if link_cursor.count()>0:
                db.collection('contains').update(dict(
                   _key = link_cursor.next()['_key'],
                   _from=f'Serial/{from_serial}',
                   _to=f'Serial/{to_serial}',
                   replaced=serial_links['replaced'],
                   reason=reason
                ))
             else:
                db.collection('contains').insert(dict(
                   _from=f'Serial/{from_serial}',
                   _to=f'Serial/{to_serial}',
                   replaced=serial_links['replaced'],
                   wo_key = wo_key,
                   component_key=component_key,
                   batch_key=batch_key,
                   reason=reason
                ))
          except:
             print(traceback.format_exc())
             self.notify_results(dict(
                notification = SerialNotificationType.ERROR,
                error_code = SerialNotificationErrorCode.EXCEPTION,
                error = traceback.format_exc()
             ))
        self.notify_results(dict(
            notification = SerialNotificationType.UPDATED
        ))

    def create_from_batch(self, serial_event):
       batch_key = serial_event['batch_key']
       created_by = serial_event['created_by']
       wo_key = serial_event['wo_key']
       product_key = serial_event['product_key']
       quantity = serial_event['quantity']

       product = db.collection('Product').get(product_key)

       serial_data = Serial()
       setattr(serial_data, 'counter_key', product['counter_key'])
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
        if (len(serials)==0):
           serials = self.retrieve_serial_in_wo(wo_key=serial_event['wo_key'])
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

    def confirm_serials(self, serial_event):
      tx = db.begin_transaction(write=['Serial', 'Counter'], read=['batch_serial'])

      cursor = tx.aql.execute(
         Queries.GET_BATCH_SERIALS,
         bind_vars=dict(batch_key=serial_event['batch_key']
      ))
      # JUST IN CASE: Consider only serials to be confirmed to avoid reassigning a new code
      batch_serials = [Serial(**s) for s in cursor if s['code'] is None]      
      # Counter key is the same for all serials in the batch
      counter_key = batch_serials[0].counter_key
      if (counter_key!=None):
         last_phase = serial_event['last_phase']
         now = timestamp()
         
         for serial in batch_serials:            
            serial.code = _generate_counter(tx, 'Counter/' + counter_key)
            serial.released = now if last_phase else None

         new = tx.collection('Serial').update_many([model_to_db_dict(s) for s in batch_serials], return_new=True)
         tx.commit_transaction()

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


    def release_serials(self, serial_event):

      cursor = db.aql.execute(
         Queries.GET_BATCH_SERIALS,
         bind_vars=dict(batch_key=serial_event['batch_key']
      ))
      # JUST IN CASE: Consider only serials to be released to avoid reassigning a new release date
      batch_serials = [Serial(**s) for s in cursor if s['released'] is None]      
   
      now = timestamp()
         
      for serial in batch_serials:            
         serial.released = now

      db.collection('Serial').update_many([model_to_db_dict(s) for s in batch_serials])
         
      for serial in batch_serials:
         self.notify_results(dict(
            serial_key = serial.key,
            serial = serial.code,
            notification = SerialNotificationType.FINALIZED
         ))


    def notify_results(self, notification):
        try:
           KafkaProducer.getInstance().produce_async(topic="serial_notifications", key=notification.get('serial_key'), value=json.dumps(notification))
        except:
           print(traceback.format_exc())


