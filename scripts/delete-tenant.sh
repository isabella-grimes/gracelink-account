#!/usr/bin/env bash
# Permanently delete a tenant (backs it up first into ./backups/deleted/).
#   ./scripts/delete-tenant.sh acme
. "$(dirname "$0")/common.sh"

[ $# -eq 1 ] || { sed -n '2,3p' "$0"; exit 1; }
SITE=$(site_name "$1")
site_exists "$SITE" || { echo "No site $SITE" >&2; exit 1; }
read -r -p "Type the site name to permanently delete $SITE: " confirm
[ "$confirm" = "$SITE" ] || { echo "Cancelled."; exit 1; }

./scripts/backup.sh "$SITE"
mkdir -p backups/deleted && mv "backups/$(ls -t backups | grep -v deleted | head -1)/$SITE" "backups/deleted/$SITE-$(date +%Y%m%d)" || true
bench drop-site "$SITE" --db-root-password "$DB_ROOT_PASSWORD" --no-backup --force
remove_route "$SITE"
[ -f "tenants/${SITE}.txt" ] && mv "tenants/${SITE}.txt" "tenants/${SITE}.deleted.txt"
echo "Deleted $SITE. Final backup: backups/deleted/"
