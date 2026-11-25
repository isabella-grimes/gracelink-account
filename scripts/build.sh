#!/usr/bin/env bash
# Build the G.R.A.C.E accounts app image (accounting, HR, ZATCA and branding apps)
# from apps.json. Takes 10-20 minutes. Rerun to pick up app updates.
#   ./scripts/build.sh            # uses GRACE_IMAGE:GRACE_TAG from .env
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && { set -a; . ./.env; set +a; }

IMAGE="${GRACE_IMAGE:-grace-accounts}:${GRACE_TAG:-16}"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

git clone --depth 1 https://github.com/frappe/frappe_docker "$WORK/frappe_docker"
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --build-arg=CACHE_BUST="$(date +%s)" \
  --secret=id=apps_json,src="$PWD/apps.json" \
  --tag="$IMAGE" \
  --file="$WORK/frappe_docker/images/layered/Containerfile" \
  "$WORK/frappe_docker"

echo "Built $IMAGE"
