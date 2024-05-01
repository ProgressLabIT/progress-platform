import asyncio

from utils import config
from utils.executor_manager import ExecutorManager
from utils.websocket_manager import WebsocketManager
from threading import Thread

from confluent_kafka import Consumer, KafkaException
from fastapi import WebSocketDisconnect

class KafkaConsumer:
    __instance = None

    def __init__(self):
      conf = config.get_config()
      self.kafka_conf = {'bootstrap.servers': conf.kafka_bootstrap_server,
        'group.id': conf.kafka_group_id,
        'client.id': conf.kafka_client_id_consumer,
        'auto.offset.reset': 'earliest'}
      self.loop = asyncio.get_event_loop()
      self.consumer = Consumer(self.kafka_conf)
      self.cancelled = False
      self.poll_thread = Thread(target=self.consume_loop)
      self.poll_thread.start()

    @staticmethod
    def getInstance():
      if KafkaConsumer.__instance == None:
        KafkaConsumer.__instance = KafkaConsumer()
      return KafkaConsumer.__instance

    def close(self):
       self.cancelled = True
       self.consumer.close()

    def consume_callback(err, msg):
      if err:
          print('ERROR: Message failed delivery: {}'.format(err))
      else:
          print("Produced event to topic {topic}: key = {key:12} value = {value:12}".format(
              topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))

    async def broadcast_message(self, msg):
      #callback(topic=msg.topic(), partiotion=ms.partition(), offset=msg.offset(), value=msg.value())
      websocketManager = WebsocketManager.getInstance()
      await websocketManager.broadcast(msg)

    def consume_loop(self):
       try:
          while not self.cancelled:
             msg = self.consumer.poll(timeout=1.0)
             if msg is None:
                continue
             if msg.error():
                raise KafkaException(msg.error())
             else:
                self.broadcast_message(msg)
       finally:
          self.consumer.close()

    def subscribe_topic(self, topic, callback=consume_callback):
        self.consumer.subscribe(topic)

    def unsubscribe_topic(self, topic):
       self.consumer.unsubscribe(topic)
