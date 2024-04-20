package it.progresslab.services;

import io.confluent.kafka.serializers.AbstractKafkaSchemaSerDeConfig;
import it.progresslab.services.avro.Serial;
import it.progresslab.services.avro.SerialValidation;
import it.progresslab.services.avro.SerialValidationResult;
import it.progresslab.services.avro.SerialValidationType;
import it.progresslab.services.base.Service;
import it.progresslab.services.domain.Schemas;
import it.progresslab.utils.ExecutorManager;
import it.progresslab.utils.MonitoringInterceptorUtils;
import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.TopicPartition;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Properties;
import java.util.concurrent.atomic.AtomicBoolean;
import org.apache.commons.cli.*;

import static java.util.Collections.singletonList;

public class SerialManagerService extends Service {
    public static final String SERVICE_NAME = "SerialManager";
    private static final Logger log = LoggerFactory.getLogger(SerialManagerService.class);
    private final AtomicBoolean running = new AtomicBoolean(false);
    private KafkaProducer producer;
    private KafkaConsumer consumer;

    @Override
    public String getConsumerGroupID() {
        return SERVICE_NAME;
    }

    public static void start(final String[] args) throws InterruptedException, ParseException {
        final SerialManagerService service = new SerialManagerService();
        service.init(args);
        service.startService(
                service.getBootstrapServers(),
                service.getStateDir(),
                service.getConfigs());
        service.addShutdownHookAndBlock();
    }

    @Override
    public void startService(final String bootstrapServers, String stateDir, final Properties defaultConfig) {
        ExecutorManager.getInstance().executeService(SERVICE_NAME, () -> execute(bootstrapServers, defaultConfig));
        running.set(true);
        log.info("SerialManagerService started");
    }

    private void execute(final String bootstrapServers, final Properties defaultConfig) {
        startConsumer(bootstrapServers, defaultConfig);
        startProducer(bootstrapServers, defaultConfig);

        try {
            final Map<TopicPartition, OffsetAndMetadata> consumedOffsets = new HashMap<>();
            consumer.subscribe(singletonList(Schemas.Topics.SERIAL.name()));
            if (isEosEnabled()) {
                producer.initTransactions();
            }

            while (running.get()) {
                final ConsumerRecords<String, Serial> records = consumer.poll(Duration.ofMillis(100));
                if (records.count() > 0) {
                    if (isEosEnabled()) {
                        producer.beginTransaction();
                    }
                    for (final ConsumerRecord<String, Serial> record : records) {
                        final Serial serial = record.value();
                        //TODO: do something
                        if (processSerial(serial)) {
                            producer.send(result(serial, isValid(serial) ? SerialValidationResult.PASS : SerialValidationResult.FAIL));
                            if (isEosEnabled()) {
                                recordOffset(consumedOffsets, record);
                            }
                        }
                    }
                    if (isEosEnabled()) {
                        producer.sendOffsetsToTransaction(consumedOffsets, new ConsumerGroupMetadata(getConsumerGroupID()));
                        producer.commitTransaction();
                    }
                }
            }
        } finally {
            close();
        }
    }

    private boolean isValid(final Serial serial) {
        //TODO: do something
        return true;
    }

    private boolean processSerial(final Serial serial) {
        //TODO: do something
        return true;
    }

    private void recordOffset(final Map<TopicPartition, OffsetAndMetadata> consumedOffsets,
                              final ConsumerRecord<String, Serial> record) {
        final OffsetAndMetadata nextOffset = new OffsetAndMetadata(record.offset() + 1);
        consumedOffsets.put(new TopicPartition(record.topic(), record.partition()), nextOffset);
    }

    private ProducerRecord<String, SerialValidation> result(final Serial serial,
                                                            final SerialValidationResult passOrFail) {
        return new ProducerRecord<>(
                Schemas.Topics.SERIAL_VALIDATIONS.name(),
                serial.getId(),
                new SerialValidation(serial.getId(), SerialValidationType.INVENTORY_CHECK, passOrFail)
        );
    }

    void startProducer(final String bootstrapServers, final Properties defaultConfig) {
        final Properties producerConfig = new Properties();
        producerConfig.putAll(defaultConfig);
        producerConfig.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        if (isEosEnabled()) {
            producerConfig.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG, "SerialManagerServerInstance");
        }
        producerConfig.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");
        producerConfig.put(ProducerConfig.RETRIES_CONFIG, String.valueOf(Integer.MAX_VALUE));
        producerConfig.put(ProducerConfig.ACKS_CONFIG, "all");
        producerConfig.put(ProducerConfig.CLIENT_ID_CONFIG, "serial-manager-service-producer");
        MonitoringInterceptorUtils.maybeConfigureInterceptorsProducer(producerConfig);

        producer = new KafkaProducer<>(producerConfig,
                Schemas.Topics.SERIAL_VALIDATIONS.keySerde().serializer(),
                Schemas.Topics.SERIAL_VALIDATIONS.valueSerde().serializer());
    }

    void startConsumer(final String bootstrapServers, final Properties defaultConfig) {
        final Properties consumerConfig = new Properties();
        consumerConfig.putAll(defaultConfig);
        consumerConfig.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        consumerConfig.put(ConsumerConfig.GROUP_ID_CONFIG, getConsumerGroupID());
        consumerConfig.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        consumerConfig.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, !eosEnabled.get());
        consumerConfig.put(ConsumerConfig.CLIENT_ID_CONFIG, "serial-manager-service-consumer");
        MonitoringInterceptorUtils.maybeConfigureInterceptorsConsumer(consumerConfig);

        consumer = new KafkaConsumer<>(consumerConfig,
                Schemas.Topics.SERIAL.keySerde().deserializer(),
                Schemas.Topics.SERIAL.valueSerde().deserializer());
    }

    void close() {
        if (producer != null) {
            producer.close();
        }
        if (consumer != null) {
            consumer.close();
        }
    }

    @Override
    public void stopService() {
        if (ExecutorManager.getInstance().terminateService(SERVICE_NAME)) {
            running.set(false);
            log.info("SerialManagerService was stopped");
        }
        log.error("Cannot stop SerialManagerService");
    }
}
