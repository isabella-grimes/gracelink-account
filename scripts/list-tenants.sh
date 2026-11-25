#!/usr/bin/env bash
# Show every tenant with its licence, plan and usage this month.
#   ./scripts/list-tenants.sh
. "$(dirname "$0")/common.sh"

printf "%-40s %-13s %-14s %6s %9s %10s %9s\n" SITE LICENCE PLAN USERS INV/MONTH WAREHOUSES COMPANIES
for site in $(list_sites); do
  out=$(bench --site "$site" execute grace_accounting.plans.get_usage 2>/dev/null | tail -1) || out=""
  python3 - "$site" "$out" <<'PY'
import json, sys
site, raw = sys.argv[1], sys.argv[2]
try:
    d = json.loads(raw)
except Exception:
    print(f"{site:<40} {'(unavailable)':<14}")
    sys.exit()
u, l = d["usage"], d.get("limits") or {}
def f(k):
    lim = l.get(k)
    return f"{u[k]}/{lim if lim is not None else '∞'}" if l else str(u[k])
print(f"{site:<40} {d.get('license') or '-':<13} {d.get('plan') or '-':<14} {f('users'):>6} {f('invoices_per_month'):>9} {f('warehouses'):>10} {f('companies'):>9}")
PY
done
