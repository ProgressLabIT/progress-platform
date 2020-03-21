docker run -d \
  -e ARANGO_ROOT_PASSWORD=progress \
  # -e ARANGO_NO_AUTH=1
  -e ARANGO_STORAGE_ENGINE=rocksdb \
  -p 8529:8529 \
  --name arango \
  --mount type=volume,source=arango-persist,target=/var/lib/arangodb3 \
  --mount type=bind,source=/Volumes/Luca/DEV/Progress/Backup/PROGRESS_TEST,target=/backup \
  arangodb

  # WRITE OPERATIONS LIMITING
  # --rocksdb.max-total-wal-size 1024000 \
  # --rocksdb.write-buffer-size 2048000 \
  # --rocksdb.max-write-buffer-size 81920000 \
  # --rocksdb.dynamic-level-bytes false \

  # READ OPERATIONS LIMITING
  # --rocksdb.block.cache.size 2560000 \
  # --rocksdb.enforce-block-cache-size-limit true \
  # --cache.size 10485760

  # DISABLE STATISTICS
  # --server.statistics false

  # JAVASCRIPT ENVIRONMENT LIMITING
  # --javascript.v8-contexts 2
  # --javascript.v8-max-heap 512



docker exec arango arangorestore --create-database true --server.database PROGRESS_TEST --input-directory "/backup" --server.authentication false