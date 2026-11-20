#!/usr/bin/env bash
set -euo pipefail

data_root=/var/lib/postgresql/data
passfile="$data_root/replication.pgpass"

chown postgres:postgres "$data_root"
umask 077
printf 'primary:5432:replication:lab_replicator:%s\n' \
  "$REPLICATION_PASSWORD" > "$passfile"
chown postgres:postgres "$passfile"
chmod 600 "$passfile"

if [ ! -s "$PGDATA/PG_VERSION" ]; then
  gosu postgres pg_basebackup \
    --dbname="host=primary port=5432 user=lab_replicator passfile=$passfile application_name=standby" \
    --pgdata="$PGDATA" \
    --write-recovery-conf \
    --wal-method=stream \
    --progress \
    --no-password
fi

exec gosu postgres postgres -c hot_standby=on
