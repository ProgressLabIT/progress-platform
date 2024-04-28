import sys
from confluent_kafka import Producer
import socket
from utils import config

class KafkaProducer:
    def __init__(self):
      conf = config.get_config()
      kafka_conf = {'bootstrap.servers': conf.kafka_bootstrap_server,
        'client.id': socket.gethostname()}
      # Create Producer instance
      KafkaProducer.producer = Producer(kafka_conf)

    def delivery_callback(err, msg):
        if err:
            print('ERROR: Message failed delivery: {}'.format(err))
        else:
            print("Produced event to topic {topic}: key = {key:12} value = {value:12}".format(
                topic=msg.topic(), key=msg.key().decode('utf-8'), value=msg.value().decode('utf-8')))

    @staticmethod
    def send_to_topic(topic, key, value, callback=delivery_callback):
        KafkaProducer.producer.produce(topic, key, value, callback)
        KafkaProducer.producer.poll(1)
        KafkaProducer.producer.flush()




