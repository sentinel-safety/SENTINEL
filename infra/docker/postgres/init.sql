-- runs once in the sentinel database (POSTGRES_DB) as POSTGRES_USER on first boot

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS age;

LOAD 'age';

SELECT ag_catalog.create_graph('sentinel_graph');

-- sentinel_app is the role services use at runtime; NOT a superuser, respects RLS.
-- sentinel (the owner) is used by alembic for DDL.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sentinel_app') THEN
        CREATE ROLE sentinel_app LOGIN PASSWORD 'sentinel_app_dev'
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE sentinel TO sentinel_app;
GRANT USAGE ON SCHEMA public TO sentinel_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sentinel_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO sentinel_app;
