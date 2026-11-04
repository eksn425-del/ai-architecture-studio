#!/bin/sh
# Never restore over the production database. Operator creates a new empty DB.
set -eu
: "${PGHOST:?}" "${PGUSER:?}" "${PGDATABASE:?}" "${KSTUDIO_BACKUP_IDENTITY:?age identity file required}"
case "$PGDATABASE" in kstudio_restore_*) ;; *) echo 'Target must start kstudio_restore_' >&2; exit 1;; esac
source=${1:?encrypted archive required}
test "$(psql -Atc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")" = 0 || { echo 'Restore target must be empty' >&2; exit 1; }
umask 077
temporary=$(mktemp -d)
trap 'rm -f "$temporary/database.dump"; rmdir "$temporary"' EXIT HUP INT TERM
age --decrypt --identity "$KSTUDIO_BACKUP_IDENTITY" --output "$temporary/database.dump" "$source"
pg_restore --exit-on-error --single-transaction --no-owner --dbname="$PGDATABASE" "$temporary/database.dump"
echo 'Run cloud.cli audit and compare task/order counts before any cutover.'
