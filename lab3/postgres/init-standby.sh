#!/usr/bin/env bash
set -euo pipefail

data_root=/var/lib/postgresql/data
passfile="$data_root/replication.pgpass"
upstream_host="${UPSTREAM_HOST:-primary}"
standby_name="${STANDBY_NAME:-standby}"

chown postgres:postgres "$data_root"
umask 077
printf '%s:5432:replication:lab_replicator:%s\n' \
  "$upstream_host" "$REPLICATION_PASSWORD" > "$passfile"
chown postgres:postgres "$passfile"
chmod 600 "$passfile"

if [ ! -s "$PGDATA/PG_VERSION" ]; then
  gosu postgres pg_basebackup \
    --dbname="host=$upstream_host port=5432 user=lab_replicator passfile=$passfile application_name=$standby_name" \
    --pgdata="$PGDATA" \
    --write-recovery-conf \
    --wal-method=stream \
    --progress \
    --no-password
fi

exec gosu postgres postgres -c hot_standby=on
