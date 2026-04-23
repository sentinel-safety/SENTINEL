FROM apache/age:release_PG16_1.5.0

COPY init.sql /docker-entrypoint-initdb.d/00-sentinel-init.sql

HEALTHCHECK --interval=5s --timeout=5s --retries=20 \
  CMD pg_isready -U sentinel -d sentinel || exit 1
