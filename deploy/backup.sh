#!/bin/sh
# Compose-native dump. No host PGHOST/PGDATABASE or published 5432 is needed.
set -eu
: "${KSTUDIO_ENV_FILE:?private environment file required}"
exec python3 "$(dirname "$0")/ops.py" backup --env-file "$KSTUDIO_ENV_FILE" --output "${1:?new encrypted archive path required}"
