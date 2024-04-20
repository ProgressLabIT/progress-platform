package it.progresslab.utils;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class ExecutorManager {
  static final Logger log = LogManager.getLogger(ExecutorManager.class);
  static ExecutorManager instance = null;

  private final Map<String, ExecutorService> executorServiceMap = new HashMap<>();

  public static synchronized ExecutorManager getInstance() {
    if (instance == null) {
      instance = new ExecutorManager();
      instance.init();
    }
    return instance;
  }

  public void init() {
  }

  public void executeService(String serviceName, Runnable runnable) {
    if (executorServiceMap.containsKey(serviceName)) {
      executorServiceMap.get(serviceName).shutdown();
    }
    executorServiceMap.put(serviceName, Executors.newSingleThreadExecutor());
    executorServiceMap.get(serviceName).execute(runnable);

  }

  public boolean terminateService(String serviceName) {
    try {
      return executorServiceMap.get(serviceName).awaitTermination(1000, TimeUnit.MILLISECONDS);
    } catch (final InterruptedException e) {
      log.error("Failed to stop {} in 1000ms", getClass().getSimpleName());
    }
    return false;
  }


}
