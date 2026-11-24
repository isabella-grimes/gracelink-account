#!/usr/bin/env bash
# First-time setup on a fresh server (Ubuntu 22.04/24.04 with Docker installed).
#   ./scripts/install.sh
set -euo pipefail
cd "$(dirname "$0")/.."

command -v python3 >/dev/null || { echo "python3 is required (it ships with Ubuntu)."; exit 1; }
command -v docker >/dev/null || { echo "Install Docker first: https://docs.docker.com/engine/install/"; exit 1; }
docker compose version >/dev/null || { echo "Docker Compose v2 is required."; exit 1; }

if [ ! -f .env ]; then
  cp .env.example .env
  pw=$(python3 -c 'import secrets; print(secrets.token_urlsafe(24).replace("-", "").replace("_", ""))')
  sed -i "s/^DB_ROOT_PASSWORD=.*/DB_ROOT_PASSWORD=${pw}/" .env
  chmod 600 .env
  echo "Created .env with a generated database password."
  echo "Edit PLATFORM_DOMAIN and LETSENCRYPT_EMAIL in .env, then run this script again."
  exit 0
fi

. ./scripts/common.sh

if ! docker image inspect "${GRACE_IMAGE}:${GRACE_TAG}" >/dev/null 2>&1; then
  if [ "${PULL_POLICY:-missing}" = "always" ] || [[ "${GRACE_IMAGE}" == */* ]]; then
    dc pull backend
  else
    ./scripts/build.sh
  fi
fi

dc up -d
echo
echo "Platform is running. Create your first customer with:"
echo "  ./scripts/new-tenant.sh acme --company \"Acme Trading\" --email owner@acme.sa --name \"Owner Name\""
