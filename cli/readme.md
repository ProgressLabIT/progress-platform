# CLI FEATURES

## Back up db: progress db backup
- Backup db into folder names with timestamp (requires DB root password)
- Create alias of the backup with name "latest"

```bash
export NOW=$(date '+%Y%m%d-%H%M%S') \
&& docker exec -i \
  $(docker ps --filter name=progress_db -q) \
  arangodump \
  --all-databases true \
  --output-directory "/db_backup/$NOW" \
&& cd /opt/progress/db_backup && ln -sfn $NOW latest
```



## copy backup or media from/to server (basically): progress copy [db|media]
NOTE: this is not actually copying the db data, but its backup/dump
Use scp with default values

Remote db backup path: `/opt/progress/db_backup/latest`
Remote media path : `/opt/progress/media`
Local path: based on input

base command: 
```bash
scp -r $SOURCE $DESTINATION
```

## Restore backup: progress db restore --db/-d DATABASE -s/--snapshot latest
```bash
docker exec -i \
  $(docker ps --filter name=progress_db -q) \
  arangorestore \
  --input-directory /db_backup/$SNAPSHOT/$DATABASE \
  --server.database $DATABASE
```
provide snapshot name and database as input with defaults (`latest` and `PROGRESS_PROD`)


## Update service: progress update [service_slug]
- First backup the DB
- Update services
- store release/version

```bash
docker service update --image $IMAGE_URL:$TAG $SERVICE_NAME
```
Specifying the image will make sure the tag is pulled even if already present.

Defaults: TAG=latest
Logic:
- IMAGE_URL = `registry.gitlab.com/progresslab/progress-platform/$SERVICE_SLUG`
- SERVICE_NAME = `progress_$SERVICE_SLUG`


