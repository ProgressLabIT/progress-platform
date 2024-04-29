import sys
from confluent_kafka import Consumer, KafkaException
import socket
from utils import config
from utils.executor_manager import ExecutorManager

class KafkaConsumer:
    __instance = None

    def __init__(self):
      conf = config.get_config()
      self.kafka_conf = {'bootstrap.servers': conf.kafka_bootstrap_server,
        'group.id': conf.kafka_group_id,
        'auto.offset.reset': 'smallest',
        'enable_auto_commit': True,
        'session_timeout_ms': conf.kafka_session_to_ms,}

    @staticmethod
    def getInstance():
      if KafkaConsumer.__instance == None:
        KafkaConsumer.__instance = KafkaConsumer()
      return KafkaConsumer.__instance

    def close(self):
       self.consumer.close()

    def consume_callback(err, msg):
      if err:
          print('ERROR: Message failed delivery: {}'.format(err))
      else:
          print("Produced event to topic {topic}: key = {key:12} value = {value:12}".format(
              topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))

    def consume_loop(self, consumer, callback):
       try:
          while True:
             msg = consumer.poll(timeout=1.0)
             if msg is None:
                continue
             if msg.error():
                raise KafkaException(msg.error())
             else:
                callback(topic=msg.topic(), partiotion=ms.partition(), offset=msg.offset(), value=msg.value())
       finally:
          consumer.close()

    def subscribe_topic(self, topic, callback=consume_callback):
        consumer = Consumer(self.kafka_conf)
        consumer.subscribe(topic)
        ExecutorManager.getInstance().execute(self.consume_loop, consumer, callback)

    def unsubscribe_topic(self, topic):
       return
       #self.consumer.unsubscribe(topic)
