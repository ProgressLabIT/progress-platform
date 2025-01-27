# PROGRESS PLATFORM REPO

## How to set up the development environment

### Prerequisites:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Steps

1. Clone the repo
2. Copy sample media files into media folder
3. Create volumes:

```bash
# run for each of the following: media, db_data, db_backup, logs
# replace <volume_name> with the name of the volume you want to create
# replace "/path/to/related/folder" with the path to the folder related to the volume you want to create, it needs to be an absolute path
# you can create those folders in the project root folder, then use their paths. They are gitignored.
docker volume create --driver local -o o=bind -o type=none -o device="d:\docker\logs" logs
docker volume create --driver local -o o=bind -o type=none -o device="d:\docker\media" media
docker volume create --driver local -o o=bind -o type=none -o device="d:\docker\db_data" db_data
docker volume create --driver local -o o=bind -o type=none -o device="d:\docker\db_backup" db_backup
docker volume create --driver local -o o=bind -o type=none -o device="d:\docker\robot_reports" robot_reports
```

3. From the project root folder, run the following command:

```bash
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.yaml --project-directory . --project-name progress_lab_dev pull
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.yaml --project-directory . --project-name progress_lab_dev build
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.yaml --project-directory . --project-name progress_lab_dev up -d
```

3.1. From the project root folder, run the following commands instead of the one on point 3 to enable remote debug:

```bash
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.debug.yaml --project-directory . --project-name progress_lab pull
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.debug.yaml --project-directory . --project-name progress_lab build
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.debug.yaml --project-directory . --project-name progress_lab up -d
docker compose -f deploy/compose/kafka.dev.yaml --project-directory . --project-name kafka pull
docker compose -f deploy/compose/kafka.dev.yaml --project-directory . --project-name kafka up -d


```

4. Restore db backup

```bash
docker exec progress_lab-db-1 arangorestore --input-directory "/db_backup" --all-databases true --create-database
```

Have fun!

_Please note that this procedure is only for development environments, as the DB server will run without authentication._
