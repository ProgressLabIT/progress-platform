package it.progresslab.db;

import com.arangodb.ArangoDB;

import com.arangodb.ArangoDBException;
import com.arangodb.entity.BaseDocument;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.util.Map;

public class ArangoDBConnector {
  private static final Logger log = LogManager.getLogger(ArangoDBConnector.class);
  static ArangoDBConnector instance = null;
  private ArangoDB arangoDB = null;


  public static synchronized ArangoDBConnector getInstance() {
    if (instance!=null) {
      return instance;
    }
    instance = new ArangoDBConnector();
    instance.init("localhost", 8529);
    return instance;
  }

  protected void init(String host, int port) {
    try {
      arangoDB = new ArangoDB.Builder().host(host, port).build();
      log.info("ArangoDB connector initialized on host {} and port {}", host, port);
    } catch (ArangoDBException e) {
      log.error("Exception while init ArangoDB connection {} host {} port: {}", e.getMessage(), host, port, e);
    }
  }

  public void createDB(String dbName) {
    try {
      arangoDB.createDatabase(dbName);
      log.info("DB created {}", dbName);
    } catch (ArangoDBException e) {
      log.error("Exception on DB {} creation: {}", dbName, e.getMessage(), e);
    }
  }

  public void createCollection(String dbName, String collectionName) {
    try {
      arangoDB.db(dbName).createCollection(collectionName);
      log.info("DB {} collection {} created", dbName, collectionName);
    } catch (ArangoDBException e) {
      log.error("Exception on DB {} collection {} creation: {}", dbName, collectionName, e.getMessage(), e);
    }
  }

  public void addDocument(String dbName, String collectionName, BaseDocument document) {
    try {
      arangoDB.db(dbName).collection(collectionName).insertDocument(document);
      log.info("DB {} collection {} document {} added", dbName, collectionName, document.toString());
    } catch(ArangoDBException e) {
      log.error("Exception while adding document on DB {} collection {} document {}: {}", dbName, collectionName, document.toString(), e.getMessage(), e);
    }
  }

  public BaseDocument getDocument(String dbName, String collectionName, String key) {
    try {
      return arangoDB.db(dbName).collection(collectionName).getDocument(key, BaseDocument.class);
    } catch(ArangoDBException e) {
      log.error("Exception retrieving document on DB {} collection {} key {}: {}", dbName, collectionName, key, e.getMessage(), e);
      return null;
    }
  }

  public ObjectNode getDocumentAsJson(String dbName, String collectionName, String key) {
    try {
      return arangoDB.db(dbName).collection(collectionName).getDocument(key, ObjectNode.class);
    } catch(ArangoDBException e) {
      log.error("Exception retrieving document on DB {} collection {} key {}: {}", dbName, collectionName, key, e.getMessage(), e);
      return null;
    }
  }

  public void updateDocument(String dbName, String collectionName, String key, BaseDocument document) {
    try {
      arangoDB.db(dbName).collection(collectionName).updateDocument(key, document);
      log.info("DB {} collection {} document {} updated", dbName, collectionName, document.toString());
    } catch (ArangoDBException e) {
      log.error("Exception while updating document on DB {} collection {} document {}: {}", dbName, collectionName, document.toString(), e.getMessage(), e);
    }
  }

  public void deleteDocument(String dbName, String collectionName, String key) {
    try {
      arangoDB.db(dbName).collection(collectionName).deleteDocument(key);
      log.info("DB {} collection {} document {} deleted", dbName, collectionName, key);
    } catch (ArangoDBException e) {
      log.error("Exception while deleting document on DB {} collection {} document {}: {}", dbName, collectionName, key, e.getMessage(), e);
    }
  }

}
