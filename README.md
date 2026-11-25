## GraceERP Solution

Branding and theme app for ERPNext v16. It sits on top of an unmodified ERPNext, so updating ERPNext never removes the branding.

What it changes:

- **Name.** The product name becomes "GraceERP Solution" in the browser tab, the login page and the desk. The name is never translated: it reads the same in every language. Upstream product names are replaced **in every language used on the site** (English, Arabic, the system language and each user's language), including the HR app, which becomes "GraceERP HR". The rest of the UI stays fully translated.
- **White-label.** The About dialog, help menu (with your own support link, `grace_support_url`), app switcher and apps screen, website footer, onboarding panels and emails show only GraceERP Solution.
- **Logo and favicon.** A floating, auto-rotating blue globe. It turns once every 24 seconds and gently bobs up and down. The animation lives inside the SVG itself, so it works anywhere the logo appears: navbar, login page, apps screen, splash screen and About dialog. For users whose system asks for reduced motion, it stays still on a view of Arabia. The favicon is a static globe, and emails get a PNG of the wordmark so Gmail and Outlook show it.
- **Emails.** The "Sent via ERPNext" footer is removed.
- **Theme.** Navy primary, globe-blue accents and gold highlights (taken from the logo), a soft grey canvas, white rounded cards, a solid navy active sidebar item, and pill-shaped status badges. Arabic text uses IBM Plex Sans Arabic. In dark mode the wordmark switches to its light version.

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
- **Logo:** replace the SVGs in `grace_accounting/public/images/`. `grace-logo.svg` is the animated globe, `grace-favicon.svg` the static one, `grace-wordmark.svg` / `grace-wordmark-light.svg` the logo with the name (for light and dark backgrounds), and `grace-hr-logo.svg` the HR tile. `grace-email-logo.png` is a still of the wordmark.
- **Name and renamed text:** `BRAND_NAME`, `NAME_REPLACEMENTS` and `CUSTOM_TEXT` (hand-written wording per language) in `grace_accounting/branding.py`.
- **About dialog and app tiles:** `grace_accounting/public/js/grace.js`.

After any change, run `bench build --app grace_accounting && bench --site <site> migrate`.

### Tests

```bash
bench --site <test-site> run-tests --app grace_accounting
```

### License

GPLv3. The underlying open-source apps keep their own license and copyright notices in their source code, as their licenses require.
