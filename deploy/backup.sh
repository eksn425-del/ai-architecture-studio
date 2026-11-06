#!/bin/sh
# PGPASSWORD or a protected PGPASSFILE provides credentials, never CLI arguments.
set -eu
: "${PGHOST:?}" "${PGUSER:?}" "${PGDATABASE:?}" "${KSTUDIO_BACKUP_RECIPIENT:?age public recipient required}"
target=${1:?new encrypted backup path required}
test ! -e "$target" || { echo 'Refusing existing backup' >&2; exit 1; }
umask 077
temporary=$(mktemp -d "$(dirname "$target")/kstudio-backup.XXXXXX")
trap 'rm -f "$temporary/database.dump" "$temporary/database.age"; rmdir "$temporary"' EXIT HUP INT TERM
pg_dump --format=custom --no-owner --file="$temporary/database.dump"
age --recipient "$KSTUDIO_BACKUP_RECIPIENT" --output "$temporary/database.age" "$temporary/database.dump"
mv "$temporary/database.age" "$target"
sha256sum "$target"
