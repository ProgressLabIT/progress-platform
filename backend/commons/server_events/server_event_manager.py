import asyncio

class ServerEventManager:
    _instance = None

    def __init__(self):
        self.queue = {}

    @staticmethod
    def getInstance():
      if ServerEventManager._instance == None:
        ServerEventManager._instance = ServerEventManager()
      return ServerEventManager._instance

    def getQueue(self, topic):
        if (self.queue.get(topic) == None):
            self.queue[topic] = asyncio.Queue(maxsize=100)
        return self.queue.get(topic)

    def enqueue(self, topic, message: str):
        self.getQueue(topic).put_nowait(message)
