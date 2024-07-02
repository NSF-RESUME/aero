#!/bin/bash
docker exec dsaas-postgres-database-1 psql -U postgres -d osprey_development -c 'ALTER SEQUENCE source_id_seq RESTART WITH 1;TRUNCATE TABLE alembic_version, function, provenance, provenance_derivation, proxy, source, source_file, source_tag, source_version, tag;'
