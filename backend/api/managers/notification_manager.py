import traceback
import json
import uuid

from commons.kafka_utils.kafka_producer import KafkaProducer
from utils.delayedqueue.conflated_delayedqueue import ConflatedDelayedQueue
from threading import Thread


class NotificationManager:
  _instance = None

  def __init__(self):
        self.cancelled = False
        self.delayed_queue = ConflatedDelayedQueue()
        self.poll_thread = Thread(target=self.consume_delayed_loop)
        self.poll_thread.start()

  @staticmethod
  def getInstance():
    if NotificationManager._instance == None:
      NotificationManager._instance = NotificationManager()
    return NotificationManager._instance

  def close(self):
    self.cancelled = True

  def notify(self, topic, key, notification):
    try:
       KafkaProducer.getInstance().produce_async(topic=topic, key=key, value=notification)
    except:
       print(traceback.format_exc())

  def consume_delayed_loop(self):
    while not self.cancelled:
      item = self.delayed_queue.get()
      self.notify(topic=item.key, key=str(uuid.uuid4()), notification=item.item)

  def delayed_enqueu(self, topic, message: str, delay: int):
    self.delayed_queue.put(topic, message, delay)

  def notifyGlobalRefresh(self):
      self.delayed_enqueu("global-notification", json.dumps({ "notification" : "REFRESH" }), 5)
