#!/usr/bin/env bash
# Restore a tenant from a backup folder made by backup.sh (overwrites the tenant's current data).
#   ./scripts/restore-tenant.sh acme backups/2026-11-25_0200/acme.graceaccounts.sa
# If the site no longer exists it is created first, then restored.
. "$(dirname "$0")/common.sh"

[ $# -eq 2 ] || { sed -n '2,4p' "$0"; exit 1; }
SITE=$(site_name "$1"); SRC="${2%/}"
DB=$(ls "$SRC"/*-database.sql.gz 2>/dev/null | head -1)
PUB=$(ls "$SRC"/*-files.tgz 2>/dev/null | grep -v private-files | head -1)
PRIV=$(ls "$SRC"/*-private-files.tgz 2>/dev/null | head -1)
[ -n "$DB" ] || { echo "No *-database.sql.gz in $SRC" >&2; exit 1; }

read -r -p "This replaces ALL current data of $SITE. Type the site name to continue: " confirm
[ "$confirm" = "$SITE" ] || { echo "Cancelled."; exit 1; }

CID=$(dc ps -q backend)
TMP="/tmp/restore-$$"
dc exec -T backend mkdir -p "$TMP"
for f in "$DB" $PUB $PRIV; do docker cp -q "$f" "$CID:$TMP/"; done
dc exec -T -u root backend chown -R frappe "$TMP"

ARGS=(--db-root-password "$DB_ROOT_PASSWORD" --force)
[ -n "$PUB" ] && ARGS+=(--with-public-files "$TMP/$(basename "$PUB")")
[ -n "$PRIV" ] && ARGS+=(--with-private-files "$TMP/$(basename "$PRIV")")

if ! site_exists "$SITE"; then
  echo "==> $SITE does not exist; creating it"
  bench new-site "$SITE" --mariadb-user-host-login-scope=% --db-root-password "$DB_ROOT_PASSWORD" \
    --admin-password "$(random_password 24)"
  write_route "$SITE"
fi

echo "==> Restoring $SITE"
bench --site "$SITE" restore "$TMP/$(basename "$DB")" "${ARGS[@]}"
bench --site "$SITE" migrate
dc exec -T backend rm -rf "$TMP"
echo "Restored $SITE from $SRC"
