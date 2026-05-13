#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE thewealth'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'thewealth')\gexec
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d thewealth \
    -f /docker-entrypoint-initdb.d/002_app_schema.sql

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -f /docker-entrypoint-initdb.d/003_market_schema.sql
