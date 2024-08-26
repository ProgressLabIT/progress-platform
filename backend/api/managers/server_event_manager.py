import asyncio
from fastapi import Request
import json
from utils.delayedqueue.conflated_delayedqueue import ConflatedDelayedQueue
from utils.delayedqueue.delayed_queue_item import DelayedQueueItem
from threading import Thread

class ServerEventManager:
    _instance = None

    def __init__(self):
        self.queue = {}
        self.cancelled = False

    @staticmethod
    def getInstance():
      if ServerEventManager._instance == None:
        ServerEventManager._instance = ServerEventManager()
      return ServerEventManager._instance

    def getQueue(self, topic, requestID):
        if (self.queue.get(topic) == None):
            self.queue[topic] = {}
        if (self.queue.get(topic).get(requestID) == None):
            self.queue.get(topic)[requestID] = asyncio.Queue()
        return self.queue.get(topic).get(requestID)

    def undergisterQueue(self, topic, requestID):
        if (self.queue.get(topic) == None):
            return
        if (self.queue.get(topic).get(requestID) == None):
            self.queue.get(topic).remove(requestID)
        return self.queue.get(topic).get(requestID)

    def enqueue(self, message: str):
        topic = json.loads(message)['subtopic']
        if (self.queue.get(topic) != None):
            for session in self.queue.get(topic):
              self.queue.get(topic).get(session).put_nowait(message)

    def close(self):
        self.cancelled = True

    async def push_events(self, request: Request, topic):
        while not self.cancelled:
            if await request.is_disconnected():
                ServerEventManager.getInstance().undergisterQueue(topic, request)
                break

            # Checks for new messages and return them to client if any
            event = await ServerEventManager.getInstance().getQueue(topic, request).get()
            if event:
                yield {
                    "event": topic,
                    "data": event
                }
