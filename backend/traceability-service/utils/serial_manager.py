import asyncio
import threading
import traceback

from asyncio import AbstractEventLoop
from typing import Dict
import json

from fastapi.encoders import jsonable_encoder
from commons.utils.db import db
from commons.models.serial import SerialWithLinks, SerialLink, Serial
from commons.utils.counter import _generate_counter



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

        serial_data : SerialWithLinks = jsonable_encoder(SerialWithLinks(**serial))
        match serial['operation']:
           case 'CREATE':
              self.create_serial(serial_data=serial_data)
           case 'UPDATE':
              self.update_serial(serial_data=serial_data)
           case 'DELETE':
              self.delete_serial(serial_data=serial_data)
           case _:
              print("Error")


    @staticmethod
    def _build_serial_link(_from: str, link_dict: SerialLink):
      link_map = dict(
        product="Product/",
        user="User/",
        counter="Counter/"
      )
      target = link_map[link_dict.get('type')] + link_dict.get('key')
      return dict(_from=_from, _to=target)

    def create_serial(self, serial_data):

        counter_id = None
        match = dict()
        for link in serial_data.get('linked_to'):
            if link.get('type') == 'counter':
                  counter_id = link.get('key')
        match['_key'] = counter_id

        # Remove links and exclude document id fields
        new_serial_record = Serial(
          **serial_data
        ).dict(by_alias=True)

        tx = db.begin_transaction(write=['Serial', 'Counter', 'serial_rel'], read=[])
        try:
          serial_no = _generate_counter(tx, 'Counter/'+counter_id)
          new_serial_record['serial'] = serial_no

          new_serial_id = tx.collection('Serial').insert(new_serial_record, return_new=True)['_id']
          #rels = [self._build_issue_link(_from=new_issue_id, link_dict=rel) for rel in self.info.issue_data.linked_to]
          link = serial_data.get('linked_to')
          rels = [self._build_serial_link(_from=new_serial_id, link_dict=rel) for rel in link]
          tx.collection('serial_rel').insert_many(rels, silent=True)

          serial_key=new_serial_id.split('/')[1]
          serial_data['_key'] = serial_key
          tx.commit_transaction()
        except:
          print(traceback.format_exc())
          tx.abort_transaction()

    def update_serial(self, serial_data):
       try:
           db.collection('Serial').update(dict(**serial_data, by_alias=True), check_rev=False)
       except:
           print(traceback.format_exc())

    def delete_serial(self, serial_data):
        key = serial_data.get("_key")
        try:
           db.collection('Serial').delete(key, return_old=True)['old']
        except:
           print(traceback.format_exc())


