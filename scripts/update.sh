#!/usr/bin/env bash
# Update all apps and every tenant: rebuild (or pull) the image, restart, migrate each site.
# Takes a backup of everything first.
#   ./scripts/update.sh
. "$(dirname "$0")/common.sh"

./scripts/backup.sh
if [ "${PULL_POLICY:-missing}" = "always" ] || [[ "${GRACE_IMAGE}" == */* ]]; then
  dc pull backend
else
  ./scripts/build.sh
fi
dc up -d --force-recreate
dc exec -T backend bash -c 'ls -1 apps > sites/apps.txt'
sync_ai_key
failed=""
for site in $(list_sites); do
  echo "==> Migrating $site"
  # Tenants created before licence types existed: hosted here, so monthly subscription.
  dc exec -T backend grep -q '"grace_license"' "sites/$site/site_config.json" \
    || bench --site "$site" set-config grace_license subscription
  if bench --site "$site" migrate; then
    bench --site "$site" clear-cache
  else
    failed="$failed $site"
  fi
done
if [ -n "$failed" ]; then
  echo "Migration FAILED for:$failed (restore from backups/ if needed)" >&2
  exit 1
fi
echo "Update complete."
