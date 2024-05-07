import asyncio
from abc import ABC, abstractmethod

from commons.utils import config
from commons.kafka_utils.kafka_consumer import KafkaConsumer
from threading import Thread
from utils.serial_manager import SerialManager

class SerialsKafkaConsumer(KafkaConsumer):

    def getTopic(self):
        return 'serials'

    def handle_message(self, msg):
      print("%% %s [%d] at offset %d with key %s:\n" %(msg.topic(), msg.partition(), msg.offset(),str(msg.key())))
      SerialManager.getInstance().enqueue(msg)
