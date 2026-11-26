#!/usr/bin/env bash
# Build the GraceERP Solution app image (accounting, HR, ZATCA, travel and branding apps)
# from apps.json. Takes 10-20 minutes. Rerun to pick up app updates.
# The travel app's repository is private: set GRACE_REPO_TOKEN in .env first.
#   ./scripts/build.sh            # uses GRACE_IMAGE:GRACE_TAG from .env
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && { set -a; . ./.env; set +a; }

IMAGE="${GRACE_IMAGE:-grace-accounts}:${GRACE_TAG:-16}"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

./scripts/render-apps-json.sh "$WORK/apps.json"   # adds GRACE_REPO_TOKEN for private repos
git clone --depth 1 https://github.com/frappe/frappe_docker "$WORK/frappe_docker"
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --build-arg=CACHE_BUST="$(date +%s)" \
  --secret=id=apps_json,src="$WORK/apps.json" \
  --tag="$IMAGE" \
  --file="$WORK/frappe_docker/images/layered/Containerfile" \
  "$WORK/frappe_docker"

echo "Built $IMAGE"
