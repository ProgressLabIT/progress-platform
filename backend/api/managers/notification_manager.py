import asyncio
import json
import logging
import traceback
import uuid

from utils.delayedqueue.conflated_delayedqueue import ConflatedDelayedQueue
from utils.nats_client import subtopic_to_subject, get_nats, get_loop
from threading import Thread

logger = logging.getLogger("notification_manager")


class NotificationManager:
  _instance = None

  def __init__(self):
        self.cancelled = False
        self.delayed_queue = ConflatedDelayedQueue()
        self.poll_thread = Thread(target=self.consume_delayed_loop, daemon=True)
        self.poll_thread.start()

  @staticmethod
  def getInstance():
    if NotificationManager._instance == None:
      NotificationManager._instance = NotificationManager()
    return NotificationManager._instance

  def close(self):
    self.cancelled = True

  def notify(self, key, notification):
    try:
       data = notification if isinstance(notification, str) else json.dumps(notification)
       parsed = json.loads(data)
       subtopic = parsed.get("subtopic", "global-notification")
       subject = subtopic_to_subject(subtopic)

       loop = get_loop()
       asyncio.run_coroutine_threadsafe(
           get_nats().publish(subject, data.encode()),
           loop,
       )
    except:
       logger.error(traceback.format_exc())

  def consume_delayed_loop(self):
    while not self.cancelled:
      item = self.delayed_queue.get()
      self.notify(key=str(uuid.uuid4()), notification=item.item)

  def delayed_enqueue(self, subtopic, message: str, delay: int):
    self.delayed_queue.put(subtopic, message, delay)

  def notifyGlobalRefresh(self):
      self.notifyConflated("global-notification", json.dumps({ "subtopic": "global-notification", "notification" : "REFRESH" }), 5)

  def notifyConflated(self, subtopic, message, delay):
      self.delayed_enqueue(subtopic, message, delay)
