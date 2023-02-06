# PROGRESS PLATFORM REPO

## How to set up the development environment

1. Clone the repo
2. Copy sample media files into media folder
3. Create volumes:
```
# run for each of the following: media, db_data, db_backup, logs
docker volume create --driver local -o o=bind -o type=none -o device="/path/to/related/folder" <volume_name>
```
3. From the project root folder, run the following command:
```
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.yaml --project-directory . --project-name <whatever you want> up -d
```
4. Restore db backup
```
docker exec <project-name>_db_1 arangorestore --input-directory "/db_backup" --all-databases true --create-database
```


Have fun!

_Please note that this procedure is only for development environments, as the DB server will run without authentication._
