import asyncio

from commons.utils import config
from commons.websockets.websocket_manager import WebsocketManager
from threading import Thread

from confluent_kafka import Consumer, KafkaException

class KafkaConsumer:
    __instance = None

    def __init__(self):
      self.cancelled = False
      conf = config.get_config()
      kafka_conf = {'bootstrap.servers': conf.kafka_bootstrap_server,
        'group.id': conf.kafka_group_id,
        'client.id': conf.kafka_client_id_consumer,
        'auto.offset.reset': 'earliest',
        'enable.auto.offset.store': False}
      self.loop = asyncio.get_event_loop()
      self.consumer = Consumer(kafka_conf)
      self.subscribe_topic('test_chat')
      self.poll_thread = Thread(target=self.consume_loop)
      self.poll_thread.start()

    @staticmethod
    def getInstance():
      if KafkaConsumer.__instance == None:
        KafkaConsumer.__instance = KafkaConsumer()
      return KafkaConsumer.__instance

    def close(self):
       self.cancelled = True
       self.poll_thread.join()
       self.consumer.close()

    def print_assignment(consumer, partitions):
        print('Assignment:', partitions)

    def consume_callback(err, msg):
      if err:
          print('ERROR: Message failed delivery: {}'.format(err))
      else:
          print("Produced event to topic {topic}: key = {key:12} value = {value:12}".format(
              topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))

    def broadcast_message(self, msg):
      #callback(topic=msg.topic(), partiotion=ms.partition(), offset=msg.offset(), value=msg.value())
      print("%% %s [%d] at offset %d with key %s:\n" %(msg.topic(), msg.partition(), msg.offset(),str(msg.key())))
      WebsocketManager.getInstance().enqueue(msg.value().decode('utf-8'))
      #websocketManager = WebsocketManager.getInstance()
      #await websoc  ketManager.broadcast(msg)

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
                self.consumer.store_offsets(msg)
       finally:
          self.consumer.close()

    def subscribe_topic(self, topic):
        self.consumer.subscribe(topics=[topic])

    def unsubscribe_topic(self, topic):
       self.consumer.unsubscribe(topics=[topic])
