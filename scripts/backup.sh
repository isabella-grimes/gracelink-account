#!/usr/bin/env bash
# Back up one tenant or all tenants (database + uploaded files) into ./backups/<date>/.
#   ./scripts/backup.sh              # all tenants
#   ./scripts/backup.sh acme         # one tenant
# Run daily from cron, and copy ./backups off the server (e.g. rclone to S3/Backblaze):
#   0 2 * * * cd /opt/grace-platform && ./scripts/backup.sh >> backups/backup.log 2>&1
. "$(dirname "$0")/common.sh"

STAMP=$(date +%Y-%m-%d_%H%M)
DEST="backups/$STAMP"
mkdir -p "$DEST"
CID=$(dc ps -q backend)

if [ $# -ge 1 ]; then
  sites=$(site_name "$1")
else
  sites=$(list_sites)
fi

failed=""
for site in $sites; do
  echo "==> $site"
  if ! bench --site "$site" backup --with-files --compress >/dev/null; then
    echo "    FAILED" >&2; failed="$failed $site"; continue
  fi
  mkdir -p "$DEST/$site"
  # Newest backup set (database, public files, private files, site config)
  for f in $(dc exec -T backend bash -c "ls -t sites/$site/private/backups/ | head -4"); do
    docker cp -q "$CID:/home/frappe/frappe-bench/sites/$site/private/backups/$f" "$DEST/$site/"
  done
  # Keep the last 3 sets inside the container too
  dc exec -T backend bash -c "cd sites/$site/private/backups && ls -t | tail -n +13 | xargs -r rm --"
done

# Keep 14 days of local backups
find backups -mindepth 1 -maxdepth 1 -type d -name '20*' -mtime +14 -exec rm -rf {} +

if [ -n "$failed" ]; then
  echo "Backup FAILED for:$failed" >&2
  exit 1
fi
echo "Backups saved in $DEST"
