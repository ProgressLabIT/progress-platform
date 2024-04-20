package it.progresslab.services.domain;

import io.confluent.kafka.streams.serdes.avro.SpecificAvroSerde;
import it.progresslab.services.avro.Serial;
import it.progresslab.services.avro.SerialValidation;
import it.progresslab.services.avro.SerialValue;
import org.apache.kafka.common.serialization.Serde;
import org.apache.kafka.common.serialization.Serdes;

import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

import static io.confluent.kafka.schemaregistry.client.SchemaRegistryClientConfig.BASIC_AUTH_CREDENTIALS_SOURCE;
import static io.confluent.kafka.schemaregistry.client.SchemaRegistryClientConfig.USER_INFO_CONFIG;
import static io.confluent.kafka.serializers.AbstractKafkaSchemaSerDeConfig.SCHEMA_REGISTRY_URL_CONFIG;

/**
 * A utility class that represents Topics and their various Serializers/Deserializers in a
 * convenient form.
 */
public class Schemas {

    public static SpecificAvroSerde<SerialValue> SERIAL_VALUE_SERDE = new SpecificAvroSerde<>();

    public static Map<String, ?> buildSchemaRegistryConfigMap(final Properties config) {
        final HashMap<String, String> map = new HashMap<>();
        if (config.containsKey(SCHEMA_REGISTRY_URL_CONFIG))
            map.put(SCHEMA_REGISTRY_URL_CONFIG, config.getProperty(SCHEMA_REGISTRY_URL_CONFIG));
        if (config.containsKey(BASIC_AUTH_CREDENTIALS_SOURCE))
            map.put(BASIC_AUTH_CREDENTIALS_SOURCE, config.getProperty(BASIC_AUTH_CREDENTIALS_SOURCE));
        if (config.containsKey(USER_INFO_CONFIG))
            map.put(USER_INFO_CONFIG, config.getProperty(USER_INFO_CONFIG));
        return map;
    }

    public static void configureSerdes(final Properties config) {
        Topics.createTopics(); //wipe cached schema registry
        for (final Topic<?, ?> topic : Topics.ALL.values()) {
            configureSerde(topic.keySerde(), config, true);
            configureSerde(topic.valueSerde(), config, false);
        }
        configureSerde(SERIAL_VALUE_SERDE, config, false);
    }

    private static void configureSerde(final Serde<?> serde, final Properties config, final Boolean isKey) {
        if (serde instanceof SpecificAvroSerde) {
            serde.configure(buildSchemaRegistryConfigMap(config), isKey);
        }
    }

    public static class Topic<K, V> {

        private final String name;
        private final Serde<K> keySerde;
        private final Serde<V> valueSerde;

        Topic(final String name, final Serde<K> keySerde, final Serde<V> valueSerde) {
            this.name = name;
            this.keySerde = keySerde;
            this.valueSerde = valueSerde;
            Topics.ALL.put(name, this);
        }

        public Serde<K> keySerde() {
            return keySerde;
        }

        public Serde<V> valueSerde() {
            return valueSerde;
        }

        public String name() {
            return name;
        }

        public String toString() {
            return name;
        }
    }

    public static class Topics {

        public final static Map<String, Topic<?, ?>> ALL = new HashMap<>();
        public static Topic<String, Serial> SERIAL;
        public static Topic<String, SerialValidation> SERIAL_VALIDATIONS;

        static {
            createTopics();
        }

        private static void createTopics() {
            SERIAL = new Topic<>("serials", Serdes.String(), new SpecificAvroSerde<>());
            SERIAL_VALIDATIONS = new Topic<>("serial-validations", Serdes.String(), new SpecificAvroSerde<>());
            SERIAL_VALUE_SERDE = new SpecificAvroSerde<>();
        }
    }
}
