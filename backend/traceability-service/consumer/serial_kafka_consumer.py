import asyncio
from abc import ABC, abstractmethod

from commons.utils import config
from commons.websockets.websocket_manager import WebsocketManager
from commons.kafka_utils.kafka_consumer import KafkaConsumer
from threading import Thread

class SerialKafkaConsumer(KafkaConsumer):

    def getTopic(self):
        return 'serial'

    def broadcast_message(self, msg):
      print("received message from topic {topic}: value = {value:12}".format(topic=msg.topic(), value=msg.value().decode('utf-8')))
      WebsocketManager.getInstance().enqueue(msg.value().decode('utf-8'))
