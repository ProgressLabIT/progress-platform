import asyncio
from abc import ABC, abstractmethod

from commons.utils import config
from commons.websockets.websocket_manager import WebsocketManager
from commons.kafka_utils.kafka_consumer import KafkaConsumer
from threading import Thread

class SerialNotificationsKafkaConsumer(KafkaConsumer):

    def getTopic(self):
        return 'serial_notifications'

    def handle_message(self, msg):
      print("%% %s [%d] at offset %d with key %s:\n" %(msg.topic(), msg.partition(), msg.offset(),str(msg.key())))
      WebsocketManager.getInstance().enqueue(msg.value().decode('utf-8'))
