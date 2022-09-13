Q: Where should workflows/scripts be run on a ephemeral ad hoc container or should there 

# DB BACKUP

## Background worker for periodic backup
Use arangodump


- Setup global parameter to figure out frequency of backup (default hourly)

## Ad hoc backup/export of specific collections
Use arangoexport with options to choose output format (JSON/JSONL/CSV/XML) and optionally collection or a custom query.
See [documentation](https://www.arangodb.com/docs/stable/programs-arangoexport-examples.html)


# DB IMPORT
Create interface for arangoimport utility



# CUSTOM PYTHON WORKFLOWS
Prefect Connectors:
- Dremio (Lakehouse platform)
- Fivetran (Data integration platform)
- Kafka (consume or produce)
- Jupyter (can run notebooks!)
