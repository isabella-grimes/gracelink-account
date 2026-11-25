## G.R.A.C.E accounts

Branding and theme app for ERPNext v16. It sits on top of an unmodified ERPNext, so updating ERPNext never removes the branding.

What it changes:

- **Name.** The product name becomes "G.R.A.C.E accounts" in the browser tab, the login page and the desk. Upstream product names are replaced in English and Arabic, including the HR app, which becomes "G.R.A.C.E HR".
- **White-label.** The About dialog, help menu (with your own support link, `grace_support_url`), app switcher and apps screen, website footer, onboarding panels and emails show only G.R.A.C.E.
- **Logo and favicon.** Your logo appears in the navbar, the login page, the apps screen, the splash screen and emails (PNG, so Gmail and Outlook show it).
- **Emails.** The "Sent via ERPNext" footer is removed.
- **Theme.** A plum primary color, a soft grey canvas, white rounded cards, a solid plum active sidebar item, and pill-shaped status badges. Arabic text uses IBM Plex Sans Arabic.

### Subscription plans (for the hosted platform)

`plans.py` enforces per-tenant limits on users, monthly invoices, warehouses, companies and HR/Payroll access. The operator sets them in each site's `site_config.json` (`grace_plan`, optional `grace_limits`), which tenants can't edit. A site with no plan is not limited. `provisioning.py` sets up a new tenant with Saudi defaults. See the `platform` branch for the scripts that use both.

### Demo data

`demo.py` fills a site with Saudi sample data: customers, suppliers, products, 15% VAT, three months of invoices and payments, and employees.

```bash
bench --site <site> execute grace_accounting.demo.create_demo_data
```

### Install

```bash
bench get-app --branch grace_accounting https://github.com/isabella-grimes/gracelink-account
bench --site <site> install-app grace_accounting
bench build --app grace_accounting
bench --site <site> clear-cache
```

Install it **after** erpnext, because it needs erpnext. The branding is applied again on every `bench migrate`.

### Rebrand or tweak

- **Colors and corners:** the `--grace-*` variables at the top of `grace_accounting/public/css/grace_theme.css`.
- **Logo:** replace the SVGs in `grace_accounting/public/images/`. `grace-logo.svg` is the square mark and `grace-wordmark.svg` is the logo with the name.
- **Name and renamed text:** `BRAND_NAME` and `TEXT_REPLACEMENTS` in `grace_accounting/branding.py`.
- **About dialog and app tiles:** `grace_accounting/public/js/grace.js`.

After any change, run `bench build --app grace_accounting && bench --site <site> migrate`.

### License

GPLv3. The underlying open-source apps keep their own license and copyright notices in their source code, as their licenses require.
