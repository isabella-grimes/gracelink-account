#!/usr/bin/env bash
# Change a tenant's subscription plan, or give them custom limits.
#   ./scripts/set-plan.sh acme comprehensive
#   ./scripts/set-plan.sh acme basic --limits '{"users": 8, "hr": true}'   # plan + custom limits
#   (null = unlimited, e.g. '{"invoices_per_month": null}')
#   ./scripts/set-plan.sh acme none                              # remove all limits
. "$(dirname "$0")/common.sh"

[ $# -ge 2 ] || { sed -n '2,5p' "$0"; exit 1; }
SITE=$(site_name "$1"); PLAN="$2"; LIMITS="${4:-}"
site_exists "$SITE" || { echo "No site $SITE" >&2; exit 1; }

if [ "$PLAN" = "none" ]; then
  bench --site "$SITE" set-config grace_plan ""
else
  valid_plan "$PLAN" || { echo "Unknown plan '$PLAN'. Use one of: $PLANS" >&2; exit 1; }
  bench --site "$SITE" set-config grace_plan "$PLAN"
fi
if [ "${3:-}" = "--limits" ] && [ -n "$LIMITS" ]; then
  # set-config -p reads Python literals; convert from JSON and check the keys.
  PYLIMITS=$(python3 - "$LIMITS" <<'PY'
import json, sys
allowed = {"users", "invoices_per_month", "warehouses", "companies", "hr"}
d = json.loads(sys.argv[1])
bad = set(d) - allowed
if bad:
    sys.exit(f"Unknown limit(s): {', '.join(sorted(bad))}. Allowed: {', '.join(sorted(allowed))}")
print(repr(d))
PY
) || exit 1
  bench --site "$SITE" set-config -p grace_limits "$PYLIMITS"
elif [ "$PLAN" != "none" ]; then
  bench --site "$SITE" set-config -p grace_limits "{}"   # new plan replaces old custom limits
fi
bench --site "$SITE" clear-cache
[ -f "tenants/${SITE}.txt" ] && sed -i "s/^plan=.*/plan=${PLAN}/" "tenants/${SITE}.txt"
echo "$SITE is now on plan: $PLAN (takes effect within a minute)"
