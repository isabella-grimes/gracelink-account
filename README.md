## G.R.A.C.E accounts

Branding and theme app for ERPNext v16. It sits on top of an unmodified ERPNext, so updating ERPNext never removes the branding.

What it changes:

- **Name.** The product name becomes "G.R.A.C.E accounts" in the browser tab, the login page and the desk. Text that says "ERPNext" is renamed in English and Arabic.
- **Logo and favicon.** Your logo appears in the navbar, the login page, the apps screen, the splash screen and emails.
- **Emails.** The "Sent via ERPNext" footer is removed.
- **Theme.** A plum primary color, a soft grey canvas, white rounded cards, a solid plum active sidebar item, and pill-shaped status badges. Arabic text uses IBM Plex Sans Arabic.

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

After any change, run `bench build --app grace_accounting && bench --site <site> migrate`.

### License

GPLv3
