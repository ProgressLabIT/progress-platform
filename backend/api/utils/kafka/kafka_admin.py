import sys
from confluent_kafka import (KafkaException, ConsumerGroupTopicPartitions,
                             TopicPartition, ConsumerGroupState, TopicCollection,
                             IsolationLevel)
from confluent_kafka.admin import (AdminClient, NewTopic, NewPartitions, ConfigResource,
                                   ConfigEntry, ConfigSource, AclBinding,
                                   AclBindingFilter, ResourceType, ResourcePatternType,
                                   AclOperation, AclPermissionType, AlterConfigOpType,
                                   ScramMechanism, ScramCredentialInfo,
                                   UserScramCredentialUpsertion, UserScramCredentialDeletion,
                                   OffsetSpec)
import threading
from utils import config
from managers.executor_manager import ExecutorManager

class KafkaAdmin:
    __instance = None

    def __init__(self):
      conf = config.get_config()
      kafka_conf = {'bootstrap.servers': conf.kafka_bootstrap_server}
      self.admin_client = AdminClient(kafka_conf)

    @staticmethod
    def getInstance():
      if KafkaAdmin.__instance == None:
        KafkaAdmin.__instance = KafkaAdmin()
      return KafkaAdmin.__instance

    def create_topic(self, topic):
      new_topics = [NewTopic(topic, num_partitions=3, replication_factor=1)]
      fs = self.admin_client.create_topics(new_topics)
      for topic, f in fs.items():
          try:
              f.result()  # The result itself is None
              return "Topic {} created".format(topic)
          except Exception as e:
              return "Failed to create topic {}: {}".format(topic, e)

    def delete_topic(self, topics):
      fs = self.admin_client.delete_topics(topics, operation_timeout=30)
      for topic, f in fs.items():
         try:
             f.result()  # The result itself is None
             return "Topic {} deleted".format(topic)
         except Exception as e:
             return "Failed to delete topic {}: {}".format(topic, e)

    def list_topics(self):
      md = self.admin_client.list_topics(timeout=10)
      message = " {} topics:".format(len(md.topics))
      for t in iter(md.topics.values()):
         if t.error is not None:
            errstr = ": {}".format(t.error)
         else:
            errstr = ""
         message += "  \"{}\" with {} partition(s){}".format(t, len(t.partitions), errstr)
         for p in iter(t.partitions.values()):
             if p.error is not None:
                errstr = ": {}".format(g.error)
             else:
                errstr = ""
             message += "partition {} leader: {}, replicas: {}, isrs: {} errstr: {}".format(p.id, p.leader, p.replicas, p.isrs, errstr)
      return message

    def describe_topic(self, topics):
      topicsColl = TopicCollection(topics)
      futureMap = self.admin_client.describe_topics(topicsColl, request_timeout=10, include_authorized_operations=False)
      message = ""
      for topic_name, future in futureMap.items():
        try:
            t = future.result()
            message += "Topic name             : {}".format(t.name)
            message += "Topic id               : {}".format(t.topic_id)
            if (t.is_internal):
                message += "Topic is Internal"

            message += "Partition Information"
            for partition in t.partitions:
                message += "    Id                : {}".format(partition.id)
                leader = partition.leader
                message += f"    Leader            : {leader}"
                message += "    Replicas          : {}".format(len(partition.replicas))
                for replica in partition.replicas:
                    message += f"         Replica            : {replica}"
                message += "    In-Sync Replicas  : {}".format(len(partition.isr))
                for isr in partition.isr:
                    message += f"         In-Sync Replica    : {isr}"

        except KafkaException as e:
            return "Error while describing topic '{}': {}".format(topic_name, e)
        except Exception:
            raise
      return message
