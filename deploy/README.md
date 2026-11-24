# G.R.A.C.E accounts: deployment

G.R.A.C.E accounts runs as a standard Frappe bench with these apps:

| App | Repo | Branch | Role |
|---|---|---|---|
| frappe | frappe/frappe | `version-16` | Framework |
| erpnext | isabella-grimes/gracelink-account | `version-16` | Accounting, POS, inventory, HR |
| ksa_compliance | isabella-grimes/ksa_compliance | `master` | ZATCA e-invoicing, Phase 1 & 2 |
| grace_accounting | isabella-grimes/gracelink-account | `grace_accounting` | G.R.A.C.E branding and theme |

**Why `version-16` and not `develop`:** ksa_compliance supports Frappe `>=15,<17`. The `develop`
branch of this fork is v17-dev, which ksa_compliance does not support and which isn't stable.
The `version-16` branch here mirrors upstream `frappe/erpnext` `version-16`.

**Use only one ZATCA app.** Do not also install `zatca_erpgulf` or `zatca_integration` on the same
site. Each app signs and submits every Sales/POS Invoice on submit. Running two would send the same
invoice twice and break the invoice counter and hash chain (ICV/PIH), and ZATCA would reject invoices.

## Option A: bench (VPS / dev machine)

```bash
./deploy/setup-bench.sh accounts.example.sa
cd grace-bench && bench start
```

## Option B: Docker (frappe_docker custom image)

```bash
git clone https://github.com/frappe/frappe_docker && cd frappe_docker
export APPS_JSON_BASE64=$(base64 -w 0 /path/to/gracelink-account/deploy/apps.json)
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=grace-accounts:16 \
  --file=images/layered/Containerfile .
```

Then run it with frappe_docker's `pwd.yml` or compose setup, using image `grace-accounts:16`, and
install both apps on the site:

```bash
bench --site <site> install-app erpnext ksa_compliance grace_accounting
```

## ZATCA onboarding, after install

1. Company: fill in the VAT number, CR number and a full Saudi address (building no., street,
   district, city, postal code).
2. Open **ZATCA Business Settings** for the company. Start in the **Sandbox/Simulation**
   environment, run the onboarding wizard (it downloads the ZATCA CLI and JRE), enter the OTP from
   the Fatoora portal, and pass the compliance checks.
3. Switch to **Production** only after simulation invoices are accepted.
4. Customers: B2B customers need VAT number + address (Standard invoices, cleared). Individuals
   get Simplified invoices (reported).

## Keeping up to date

- ERPNext: sync `version-16` from upstream `frappe/erpnext` (GitHub "Sync fork" on that branch).
- ksa_compliance: sync `master` from upstream `lavaloon-eg/ksa_compliance`.
- After updating: `bench update --pull` (or rebuild the image), then `bench --site <site> migrate`.
