#!/usr/bin/env bash
# Create a demo tenant full of sample data, for sales demos and training.
#   ./scripts/demo-tenant.sh                  # creates demo.<PLATFORM_DOMAIN>
#   ./scripts/demo-tenant.sh trial-acme       # any other name
# Login: owner@demo.sa / the password printed at the end. Comprehensive plan.
# Sample data: Saudi customers and suppliers, products and services, 15% VAT,
# three months of sales and purchase invoices with payments, and employees.
. "$(dirname "$0")/common.sh"

NAME="${1:-demo}"
SITE=$(site_name "$NAME")
PASSWORD=$(random_password 12)

./scripts/new-tenant.sh "$NAME" \
  --company "Al Noor Trading" --abbr ANT \
  --email owner@demo.sa --name "Khalid Al-Harbi" \
  --plan comprehensive --password "$PASSWORD"

echo "==> Adding sample data"
bench --site "$SITE" execute grace_accounting.demo.create_demo_data

SCHEME=$([ "${TLS:-true}" = "true" ] && echo https || echo http)
cat <<DONE

Demo ready: ${SCHEME}://${SITE}
  Login:    owner@demo.sa
  Password: ${PASSWORD}
Delete it when you're done: ./scripts/delete-tenant.sh ${NAME}
DONE
