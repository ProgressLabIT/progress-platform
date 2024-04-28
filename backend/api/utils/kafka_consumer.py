import sys
from confluent_kafka import Consumer
import socket
from utils import config

class KafkaConsumer:
    def __init__(self):
      conf = config.get_config()
      kafka_conf = {'bootstrap.servers': conf.kafka_bootstrap_server,
        'group.id': 'foo',
        'auto.offset.reset': 'smallest'}
      # Create Producer instance
      self.consumer = Consumer(kafka_conf)

    def subscribe_topic(self, topic):
        self.consumer.subscribe(topic)






