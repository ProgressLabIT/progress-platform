import asyncio
import threading

from typing import Dict, Set
from fastapi import WebSocket
from asyncio import AbstractEventLoop
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor
from starlette.concurrency import run_in_threadpool


class WebsocketManager:
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
        self.active_connections: list[WebSocket] = []
        self.messages: list[str] = []
        self.queue = asyncio.Queue(maxsize=100)
        self.loop = asyncio.get_event_loop()
        self.cancelled = False
        self.loop.create_task(self.poll_loop())


    def close(self):
        self.cancelled = True
        self.poll_thread.join()
        self.queue.join()

    @staticmethod
    def getInstance():
      if WebsocketManager.__instance == None:
        WebsocketManager.__instance = WebsocketManager()
      return WebsocketManager.__instance

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    def enqueue(self, message: str):
        #self.messages.append(message)
        self.queue.put_nowait(message)

    async def poll_loop(self):
        while not self.cancelled:
            message = await self.queue.get()
            print(f'> websocket_manager got {message}')
            await self.broadcast(message=message)
        return "DONE!"



