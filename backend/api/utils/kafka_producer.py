import sys
import asyncio
import confluent_kafka

from confluent_kafka import KafkaException
from confluent_kafka import Producer
from threading import Thread
import socket
from utils import config

class KafkaProducer:
    __instance = None

    def __init__(self):
      conf = config.get_config()
      kafka_conf = {'bootstrap.servers': conf.kafka_bootstrap_server,
                   # 'enable.idempotence': True,
                    'acks': "all",
                    'client.id': conf.kafka_client_id_producer}
      # Create Producer instance
      self.loop = asyncio.get_event_loop()
      self.producer = Producer(kafka_conf)
      self.cancelled = False
      self.poll_thread = Thread(target=self.poll_loop)
      self.poll_thread.start()

    @staticmethod
    def getInstance():
      if KafkaProducer.__instance == None:
        KafkaProducer.__instance = KafkaProducer()
      return KafkaProducer.__instance

    def delivery_callback(err, msg):
      if err:
          print('ERROR: Message failed delivery: {}'.format(err))
      else:
          print("Produced event to topic {topic}: key = {key:12} value = {value:12}".format(
              topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))

    def poll_loop(self):
        while not self.cancelled:
            self.producer.poll(0.1)

    def close(self):
        self.cancelled = True
        self.poll_thread.join()

    def produce_async(self, topic, key, value, callback=delivery_callback):
        result = self.loop.create_future()

        def ack(err, msg):
            if err:
                self.loop.call_soon_threadsafe(
                    result.set_exception, KafkaException(err))
            else:
                self.loop.call_soon_threadsafe(
                    result.set_result, msg)
            if callback:
                self.loop.call_soon_threadsafe(
                    callback, err, msg)
        self.producer.produce(topic, key, value, on_delivery=ack)
        return result

    def produce_synch(self, topic, key, value, callback=delivery_callback):
        self.producer.produce(topic, key, value, callback)
        self.producer.poll(1)
        self.producer.flush()




