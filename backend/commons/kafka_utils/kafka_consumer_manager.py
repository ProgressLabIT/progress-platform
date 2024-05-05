from commons.kafka_utils.kafka_consumer import KafkaConsumer

class KafkaConsumerManager:
    __instance = None

    def __init__(self):
       self.consumers = list()

    @staticmethod
    def getInstance():
      if KafkaConsumerManager.__instance == None:
        KafkaConsumerManager.__instance = KafkaConsumerManager()
      return KafkaConsumerManager.__instance

    def registerConsumer(self, consumer):
       self.consumers.append(consumer)

    def closeAllConsumers(self):
       for consumer in self.consumers:
          consumer.close()

