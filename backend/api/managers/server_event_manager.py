import asyncio
import json

from fastapi import Request
from fastapi.sse import ServerSentEvent

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
        if self.queue.get(topic) is None:
            return
        self.queue[topic].pop(requestID, None)

    def enqueue(self, message: str):
        topic = json.loads(message)['subtopic']
        # Exact-topic delivery
        if self.queue.get(topic) is not None:
            for session in list(self.queue[topic].keys()):
                self.queue[topic][session].put_nowait(message)

        # Wildcard fan-out: deliver to {prefix}:* subscribers (per D-04)
        if ':' in topic:
            prefix, _ = topic.split(':', 1)
            wildcard = f"{prefix}:*"
            if self.queue.get(wildcard) is not None:
                for session in list(self.queue[wildcard].keys()):
                    self.queue[wildcard][session].put_nowait(message)

    def close(self):
        self.cancelled = True

    async def push_events(self, request: Request, topic):
        try:
            while not self.cancelled:
                if await request.is_disconnected():
                    break

                # Poll for new messages with a timeout so we can detect disconnects promptly
                try:
                    event = await asyncio.wait_for(
                        ServerEventManager.getInstance().getQueue(topic, request).get(),
                        timeout=14.0
                    )
                except asyncio.TimeoutError:
                    yield ServerSentEvent(comment="")
                    continue

                if event:
                    yield ServerSentEvent(raw_data=event, event=topic)
        finally:
            ServerEventManager.getInstance().undergisterQueue(topic, request)

    async def push_events_multi(self, request: Request, topics):
        """Stream events for MULTIPLE topics over a single SSE connection.

        Lets one browser tab open one EventSource carrying every subscribed
        topic instead of one connection per topic — which exhausts the
        browser's per-host HTTP/1.1 connection budget once a second tab opens.

        Each topic keeps its own queue (so `enqueue`'s exact + wildcard fan-out
        is untouched); a pump task drains each into a shared local queue, and
        emitted events keep the same `event: <topic>` name as the single-topic
        stream so the client routes them per topic unchanged.
        """
        mgr = ServerEventManager.getInstance()
        topics = list(dict.fromkeys(topics))  # de-dupe, preserve order
        queues = {topic: mgr.getQueue(topic, request) for topic in topics}
        merged: asyncio.Queue = asyncio.Queue()

        async def _pump(topic, queue):
            while True:
                msg = await queue.get()
                merged.put_nowait((topic, msg))

        pumps = [asyncio.create_task(_pump(t, q)) for t, q in queues.items()]
        try:
            while not self.cancelled:
                if await request.is_disconnected():
                    break

                try:
                    topic, event = await asyncio.wait_for(merged.get(), timeout=14.0)
                except asyncio.TimeoutError:
                    yield ServerSentEvent(comment="")
                    continue

                if event:
                    yield ServerSentEvent(raw_data=event, event=topic)
        finally:
            for pump in pumps:
                pump.cancel()
            for topic in topics:
                mgr.undergisterQueue(topic, request)
