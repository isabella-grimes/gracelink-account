#!/usr/bin/env bash
# Create a ready-to-use tenant: site + database + all apps + plan + company + owner login.
#
#   ./scripts/new-tenant.sh acme --company "Acme Trading" --email owner@acme.sa --name "Ahmed Ali"
#   ./scripts/new-tenant.sh erp.acme.sa --company "Acme" --email owner@acme.sa --name "Ahmed" --plan comprehensive
#
# "acme" becomes acme.<PLATFORM_DOMAIN>. A full domain (with dots) is used as a custom domain;
# point its DNS A record at this server first.
# Options: --plan economic|basic|comprehensive (default from .env), --password <owner password>
#          (generated if omitted), --lang ar|en (default ar), --abbr <company abbreviation>
. "$(dirname "$0")/common.sh"

[ $# -ge 1 ] || { sed -n '2,11p' "$0"; exit 1; }
SITE=$(site_name "$1"); shift
COMPANY="" EMAIL="" NAME="" PLAN="${DEFAULT_PLAN:-basic}" PASSWORD="" LANG_CODE="ar" ABBR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --company) COMPANY="$2"; shift 2 ;;
    --email) EMAIL="$2"; shift 2 ;;
    --name) NAME="$2"; shift 2 ;;
    --plan) PLAN="$2"; shift 2 ;;
    --password) PASSWORD="$2"; shift 2 ;;
    --lang) LANG_CODE="$2"; shift 2 ;;
    --abbr) ABBR="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done
[ -n "$COMPANY" ] && [ -n "$EMAIL" ] && [ -n "$NAME" ] || { echo "--company, --email and --name are required" >&2; exit 1; }
valid_plan "$PLAN" || { echo "Unknown plan '$PLAN'. Use one of: $PLANS" >&2; exit 1; }
site_exists "$SITE" && { echo "Site $SITE already exists." >&2; exit 1; }
[ -n "$PASSWORD" ] || PASSWORD=$(random_password 14)
ADMIN_PASSWORD=$(random_password 24)

# Install order matters: erpnext first, grace_accounting last (its branding must win).
AVAILABLE=" $(dc exec -T backend ls -1 apps | tr '\n' ' ') "
INSTALL_ARGS=()
for app in erpnext hrms ksa_compliance grace_accounting; do
  case "$AVAILABLE" in *" $app "*) INSTALL_ARGS+=(--install-app "$app") ;; esac
done

echo "==> Creating site $SITE with apps: ${INSTALL_ARGS[*]//--install-app /} (takes a few minutes)"
bench new-site "$SITE" \
  --mariadb-user-host-login-scope=% \
  --db-root-password "$DB_ROOT_PASSWORD" \
  --admin-password "$ADMIN_PASSWORD" \
  "${INSTALL_ARGS[@]}"

bench --site "$SITE" scheduler enable   # background jobs: ZATCA submissions, emails, reports

echo "==> Applying plan: $PLAN"
bench --site "$SITE" set-config grace_plan "$PLAN"
# Every tenant on this platform is a monthly subscription (hosted, maintained and
# supported 24/7 by GraceERP). Lifetime-licence customers host their own server.
bench --site "$SITE" set-config grace_license subscription

echo "==> Setting up company and owner account"
KWARGS=$(python3 - "$COMPANY" "$EMAIL" "$NAME" "$PASSWORD" "$LANG_CODE" "$ABBR" <<'PY'
import json, sys
company, email, name, password, lang, abbr = sys.argv[1:7]
kw = {"company_name": company, "owner_email": email, "owner_name": name,
      "owner_password": password, "language": lang}
if abbr:
    kw["company_abbr"] = abbr
print(json.dumps(kw))
PY
)
bench --site "$SITE" execute grace_accounting.provisioning.setup_tenant --kwargs "$KWARGS"

write_route "$SITE"
SCHEME=$([ "${TLS:-true}" = "true" ] && echo https || echo http)

mkdir -p tenants
cat > "tenants/${SITE}.txt" <<INFO
site=$SITE
company=$COMPANY
plan=$PLAN
owner_email=$EMAIL
created=$(date -u +%Y-%m-%dT%H:%M:%SZ)
administrator_password=$ADMIN_PASSWORD
INFO
chmod 600 "tenants/${SITE}.txt"

cat <<DONE

Tenant ready.
  URL:       ${SCHEME}://${SITE}
  Login:     ${EMAIL}
  Password:  ${PASSWORD}
  Plan:      ${PLAN}
Send the owner their login. The Administrator password is saved in tenants/${SITE}.txt (keep it private).
Next step for the customer: ZATCA onboarding (search "ZATCA Business Settings" after logging in).
DONE
