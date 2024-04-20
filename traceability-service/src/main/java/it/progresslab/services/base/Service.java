package it.progresslab.services.base;

import io.confluent.kafka.serializers.AbstractKafkaSchemaSerDeConfig;
import it.progresslab.services.domain.Schemas;
import org.apache.commons.cli.*;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Optional;
import java.util.Properties;
import java.util.concurrent.atomic.AtomicBoolean;

public abstract class Service {
    public static final String DEFAULT_BOOTSTRAP_SERVERS = "localhost:9092";
    public static final String DEFAULT_SCHEMA_REGISTRY_URL = "http://localhost:8081";

    static final Logger log = LogManager.getLogger(Service.class);
    protected AtomicBoolean eosEnabled = new AtomicBoolean(false);
    Properties defaultConfig = null;
    CommandLine cl = null;

    public abstract void startService(String bootstrapServers, String stateDir, Properties defaultConfig);

    public abstract void stopService();

    public abstract String getConsumerGroupID();

    public boolean isEosEnabled() {
        return eosEnabled.get();
    }

    public void setEosEnabled(boolean eosEnabled) {
        this.eosEnabled.set(eosEnabled);
    }

    public void addShutdownHookAndBlock() throws InterruptedException {
        Thread.currentThread().setUncaughtExceptionHandler((t, e) -> stopService());
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            try {
                stopService();
            } catch (final Exception ignored) {
            }
        }));
        Thread.currentThread().join();
    }

    public void init(final String[] args) throws ParseException {
        final Options opts = new Options();
        opts.addOption(Option.builder("b")
                .longOpt("bootstrap-servers")
                .hasArg()
                .desc("Kafka cluster bootstrap server string (ex: broker:9092)")
                .build());
        opts.addOption(Option.builder("s")
                .longOpt("schema-registry")
                .hasArg()
                .desc("Schema Registry URL")
                .build());
        opts.addOption(Option.builder("c")
                .longOpt("config-file")
                .hasArg()
                .desc("Java properties file with configurations for Kafka Clients")
                .build());
        opts.addOption(Option.builder("t")
                .longOpt("state-dir")
                .hasArg()
                .desc("The directory for state storage")
                .build());
        opts.addOption(Option.builder("h").longOpt("help").hasArg(false).desc("Show usage information").build());

        cl = new DefaultParser().parse(opts, args);

        if (cl.hasOption("h")) {
            final HelpFormatter formatter = new HelpFormatter();
            formatter.printHelp("Order Details Service", opts);
            return;
        }
        final Properties defaultConfig = Optional.ofNullable(cl.getOptionValue("config-file", null))
                .map(path -> {
                    try {
                        return buildPropertiesFromConfigFile(path);
                    } catch (final IOException e) {
                        throw new RuntimeException(e);
                    }
                })
                .orElse(new Properties());

        final String schemaRegistryUrl = cl.getOptionValue("schema-registry", DEFAULT_SCHEMA_REGISTRY_URL);
        defaultConfig.put(AbstractKafkaSchemaSerDeConfig.SCHEMA_REGISTRY_URL_CONFIG, schemaRegistryUrl);
        Schemas.configureSerdes(defaultConfig);
    }

    public static Properties buildPropertiesFromConfigFile(final String configFile) throws IOException {
        if (!Files.exists(Paths.get(configFile))) {
            throw new IOException(configFile + " not found.");
        }
        final Properties properties = new Properties();
        try (InputStream inputStream = new FileInputStream(configFile)) {
            properties.load(inputStream);
        }
        return properties;
    }

    public String getBootstrapServers() {
        return cl.getOptionValue("bootstrap-servers", DEFAULT_BOOTSTRAP_SERVERS);
    }

    public String getStateDir() {
        return cl.getOptionValue("state-dir", "/tmp/kafka-streams-examples");
    }

    public Properties getConfigs() {
        return defaultConfig;
    }

}
