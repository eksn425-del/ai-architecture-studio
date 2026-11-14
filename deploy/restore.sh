#!/bin/sh
# Restore into a NEW explicitly named isolated database; never overwrite old data.
set -eu
: "${KSTUDIO_ENV_FILE:?private environment file required}"
exec python3 "$(dirname "$0")/ops.py" restore-drill --env-file "$KSTUDIO_ENV_FILE" --archive "${1:?encrypted archive required}" --target-db "${2:?new kstudio_restore_* database required}"
