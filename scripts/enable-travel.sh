#!/usr/bin/env bash
# Turn an existing tenant into a travel agency: install GraceERP Travel (grace_travel).
# Takes a backup of the tenant first. Safe to run again.
#   ./scripts/enable-travel.sh acme
. "$(dirname "$0")/common.sh"

[ $# -eq 1 ] || { sed -n '2,4p' "$0"; exit 1; }
SITE=$(site_name "$1")
site_exists "$SITE" || { echo "No site $SITE." >&2; exit 1; }
has_app grace_travel || { echo "This image has no grace_travel. Rebuild or pull the image first." >&2; exit 1; }

if bench --site "$SITE" list-apps | grep -q '^grace_travel'; then
  echo "GraceERP Travel is already installed on $SITE."
  exit 0
fi

./scripts/backup.sh "$1"
echo "==> Installing GraceERP Travel on $SITE"
bench --site "$SITE" install-app grace_travel
bench --site "$SITE" migrate      # re-applies GraceERP branding after the new app
bench --site "$SITE" clear-cache
sync_ai_key
echo "Done. Next: in $SITE open Travel Settings > Check Setup (accounts and default VAT)."
