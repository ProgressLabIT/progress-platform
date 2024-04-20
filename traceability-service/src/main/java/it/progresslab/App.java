package it.progresslab;

import com.fasterxml.jackson.databind.node.ObjectNode;
import it.progresslab.db.ArangoDBConnector;
import it.progresslab.services.SerialManagerService;
import org.apache.commons.cli.ParseException;

/**
 * Hello world!
 */
public class App {
  public static void main(final String[] args) {
    /*final ObjectNode documentAsJson = ArangoDBConnector.getInstance().getDocumentAsJson("PROGRESS_PROD", "User", "2863813");
    documentAsJson.get("_key");*/
    try {
      SerialManagerService.start(args);
    } catch (InterruptedException e) {
      throw new RuntimeException(e);
    } catch (ParseException e) {
      throw new RuntimeException(e);
    }
  }
}
