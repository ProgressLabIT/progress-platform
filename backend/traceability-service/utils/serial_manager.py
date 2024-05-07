import asyncio
import threading

from asyncio import AbstractEventLoop
from typing import Dict
import json

from starlette.concurrency import run_in_threadpool
from fastapi.encoders import jsonable_encoder
from commons.utils.db import db
from commons.models.serial import SerialWithLinks, SerialLink, SerialLinkType
from commons.models.counter import Counter
from commons.utils.counter import _generate_counter_wo_tx


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
        self.poll_thread.join()
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

        counter_id = None
        match = dict()
        for link in serial_data.get('linked_to'):
            if link.get('type') == 'counter':
                  counter_id = link.get('key')
        match['_key'] = counter_id

        serial_no = _generate_counter_wo_tx('Counter/'+counter_id)
        serial_data['serial'] = serial_no

        db.collection('Serial').insert(serial_data)['_key']

