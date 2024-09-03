import asyncio
from abc import ABC, abstractmethod

from utils import config
from managers.server_event_manager import ServerEventManager
from utils.kafka.kafka_consumer import KafkaConsumer
from threading import Thread

class NotificationsKafkaConsumer(KafkaConsumer):

    def getTopic(self):
        return 'notifications'

    def handle_message(self, msg):
      print("%% %s [%d] at offset %d with key %s:\n" %(msg.topic(), msg.partition(), msg.offset(),str(msg.key())))
      ServerEventManager.getInstance().enqueue(msg.value().decode('utf-8'))
