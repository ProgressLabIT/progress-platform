docker run -d \
  -e ARANGO_NO_AUTH=1 \
  -p 8529:8529 \
  --name arango \
  --mount type=volume,source=arango-persist,target=/var/lib/arangodb3 \
  --mount type=bind,source=${HOME}/dev/Progress/db_backup/PROGRESS_TEST,target=/backup \
  \
  arangodb \
  --rocksdb.max-total-wal-size 1024000 \
  --rocksdb.write-buffer-size 2048000 \
  --rocksdb.max-write-buffer-number 2 \
  --rocksdb.total-write-buffer-size 81920000 \
  --rocksdb.dynamic-level-bytes false \
  \
  --rocksdb.block-cache-size 2560000 \
  --rocksdb.enforce-block-cache-size-limit true \
  --cache.size 10485760 \
  \
  --server.statistics false \
  \
  --javascript.v8-contexts 2 \
  --javascript.v8-max-heap 512



# Restore in docker
docker exec arango arangorestore --create-database true --server.database PROGRESS_TEST --input-directory "/backup" --server.authentication false

# Restore in docker-compose
docker-compose exec arangodb arangorestore --create-database true --server.database PROGRESS_TEST --input-directory "/db_backup/PROGRESS_TEST" --server.authentication false
