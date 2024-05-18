import asyncio
from abc import ABC, abstractmethod

from commons.utils import config
#from commons.server_events.server_event_manager import ServerEventManager
from commons.server_events.server_event_manager import ServerEventManager
from commons.kafka_utils.kafka_consumer import KafkaConsumer
from threading import Thread

class SerialNotificationsKafkaConsumer(KafkaConsumer):

    def getTopic(self):
        return 'serial_notifications'

    def handle_message(self, msg):
      print("%% %s [%d] at offset %d with key %s:\n" %(msg.topic(), msg.partition(), msg.offset(),str(msg.key())))
      ServerEventManager.getInstance().enqueue("serial-notifications", msg.value().decode('utf-8'))
