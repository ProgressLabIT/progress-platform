# PROGRESS PLATFORM REPO

## How to set up the development environment

1. Clone the repo
2. Copy sample media files into media folder
3. Create volumes:
```
# create implicit db_data volume
docker volume create db_data

# create other volumes linked to folders in the repo.
docker volume create --driver local -o o=bind -o type=none -o device="/path/to/project/media" media
docker volume create --driver local -o o=bind -o type=none -o device="/path/to/project/db/backup" db_backup
```
4. Install webapp dependencies
```
cd /path/to/project/webapps/main
npm install 
```
5. From the project root folder, run the following command:
```
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.yaml --project-directory . --project-name <whatever you want> up -d
```
6. Restore db backup
```
docker exec <project-name>-db-1 arangorestore --input-directory "/db_backup" --all-databases true --create-database
```


Have fun!

_Please note that this procedure is only for development environments, as the DB server will run without authentication._
