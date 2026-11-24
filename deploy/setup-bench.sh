#!/usr/bin/env bash
# GRACE Accounting: ERPNext v16 + KSA Compliance (ZATCA Phase 1 & 2) on a fresh bench.
#
# Usage:
#   ./setup-bench.sh <site-name> [bench-dir]
#   e.g. ./setup-bench.sh accounts.gracelink.sa
#
# Prerequisites (already installed): Python 3.14, Node 24, yarn, MariaDB 10.6+, Redis,
# wkhtmltopdf, and frappe-bench (`pip install frappe-bench`).
# Java is NOT needed up front: ksa_compliance downloads the JRE and ZATCA CLI
# itself during its onboarding wizard.
set -euo pipefail

SITE="${1:?Usage: $0 <site-name> [bench-dir]}"
BENCH_DIR="${2:-grace-bench}"

FRAPPE_BRANCH="version-16"
ERPNEXT_REPO="https://github.com/isabella-grimes/gracelink-account"
ERPNEXT_BRANCH="version-16"
KSA_REPO="https://github.com/isabella-grimes/ksa_compliance"
KSA_BRANCH="master"

if [ ! -d "$BENCH_DIR" ]; then
  bench init --frappe-branch "$FRAPPE_BRANCH" "$BENCH_DIR"
fi
cd "$BENCH_DIR"

# The fork keeps the app name "erpnext", so bench installs it as apps/erpnext.
[ -d apps/erpnext ]        || bench get-app --branch "$ERPNEXT_BRANCH" "$ERPNEXT_REPO"
[ -d apps/ksa_compliance ] || bench get-app --branch "$KSA_BRANCH" "$KSA_REPO"
bench setup requirements

if [ ! -d "sites/$SITE" ]; then
  bench new-site "$SITE"   # prompts for the MariaDB root and Administrator passwords
fi

bench --site "$SITE" install-app erpnext
bench --site "$SITE" install-app ksa_compliance
bench --site "$SITE" migrate
bench --site "$SITE" set-config default_site "$SITE" || true

echo
echo "Done. Start with: cd $BENCH_DIR && bench start"
echo "Then finish ERPNext setup, and run ZATCA onboarding: search 'ZATCA Business Settings'."
