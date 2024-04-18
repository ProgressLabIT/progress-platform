package it.progresslab;

import com.fasterxml.jackson.databind.node.ObjectNode;
import it.progresslab.db.ArangoDBConnector;

/**
 * Hello world!
 *
 */
public class App
{
    public static void main( String[] args )
    {
      ObjectNode documentAsJson = ArangoDBConnector.getInstance().getDocumentAsJson("PROGRESS_PROD", "User", "2863813");
      documentAsJson.get("_key");

    }
}
