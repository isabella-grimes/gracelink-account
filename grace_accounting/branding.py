"""Apply G.R.A.C.E accounts branding to a site.

The product name, logo and favicon are read from site settings
(Website Settings, System Settings, Navbar Settings) before falling back to
app hooks, so this module writes them there.
"""

import frappe

BRAND_NAME = "G.R.A.C.E accounts"
BRAND_LOGO = "/assets/grace_accounting/images/grace-logo.svg"
BRAND_FAVICON = "/assets/grace_accounting/images/grace-favicon.svg"
BRAND_WORDMARK = "/assets/grace_accounting/images/grace-wordmark.svg"
BRAND_HR_LOGO = "/assets/grace_accounting/images/grace-hr-logo.svg"
HR_NAME = "G.R.A.C.E HR"

# Help/user menu items that point at the underlying open-source projects (removed).
UPSTREAM_MARKERS = ("frappe", "erpnext", "github.com", "discuss.", "school")

# UI text that says "ERPNext" -> brand name, per language. Applied through
# the Translation doctype, which overrides strings shown with __() / _().
TEXT_REPLACEMENTS = {
	"en": {
		"ERPNext": BRAND_NAME,
		"ERPNext Settings": f"{BRAND_NAME} Settings",
		"Welcome to ERPNext": f"Welcome to {BRAND_NAME}",
		"Let's give your business a home.": "Let's set up your accounts.",
		"Get to know ERPNext": f"Get to know {BRAND_NAME}",
		"Frappe HR": HR_NAME,
		"Let's build a workplace your team will love.": "Let's set up your team and payroll.",
		"Frappe": BRAND_NAME,
	},
	"ar": {
		"ERPNext": BRAND_NAME,
		"ERPNext Settings": f"إعدادات {BRAND_NAME}",
		"Welcome to ERPNext": f"مرحبًا بك في {BRAND_NAME}",
		"Let's give your business a home.": "لنجهّز حساباتك.",
		"Get to know ERPNext": f"تعرّف على {BRAND_NAME}",
		"Frappe HR": HR_NAME,
		"Let's build a workplace your team will love.": "لنجهّز فريقك ورواتبهم.",
		"Frappe": BRAND_NAME,
	},
}


def apply_branding():
	_set_single("Website Settings", {
		"app_name": BRAND_NAME,
		"app_logo": BRAND_LOGO,
		"favicon": BRAND_FAVICON,
		"splash_image": BRAND_LOGO,
		"brand_html": f'<img src="{BRAND_WORDMARK}" alt="{BRAND_NAME}" style="height: 28px;">',
		# Website footer ("Built on ...")
		"footer_powered": BRAND_NAME,
	})
	_set_single("System Settings", {
		"app_name": BRAND_NAME,
		# Removes the "Sent via ERPNext" footer from outgoing emails
		"disable_standard_email_footer": 1,
	})
	frappe.db.set_default("disable_standard_email_footer", 1)
	_set_single("Navbar Settings", {"app_logo": BRAND_LOGO})
	_clean_navbar_menus()
	_set_translations()
	frappe.clear_cache()


def _clean_navbar_menus():
	"""Hide help/user-menu links to the upstream projects; add our own support link."""
	if not frappe.db.exists("DocType", "Navbar Settings"):
		return
	settings = frappe.get_single("Navbar Settings")
	changed = False
	for table in ("help_dropdown", "settings_dropdown"):
		rows = settings.get(table) or []
		keep = [
			r for r in rows
			if not any(m in f"{r.item_label or ''} {r.route or ''} {r.action or ''}".lower() for m in UPSTREAM_MARKERS)
		]
		if len(keep) != len(rows):
			settings.set(table, keep)
			changed = True

	support_url = frappe.conf.get("grace_support_url")
	label = "Help & Support"
	existing = next((r for r in settings.help_dropdown if r.item_label == label), None)
	if support_url and not existing:
		settings.append(
			"help_dropdown",
			{"item_label": label, "item_type": "Route", "route": support_url, "is_standard": 0},
		)
		changed = True
	elif existing and (existing.route != support_url or existing.hidden != (0 if support_url else 1)):
		existing.route = support_url or existing.route
		existing.hidden = 0 if support_url else 1
		changed = True

	if changed:
		settings.flags.ignore_permissions = True
		settings.save()


def boot_session(bootinfo):
	# App names/logos on the apps screen are rebranded in public/js/grace.js,
	# because that list is built after boot_session hooks run.
	bootinfo.grace_support_url = frappe.conf.get("grace_support_url")


def _set_single(doctype, values):
	"""Set fields on a Single doctype, skipping any field this version lacks."""
	if not frappe.db.exists("DocType", doctype):
		return
	meta = frappe.get_meta(doctype)
	for fieldname, value in values.items():
		if meta.has_field(fieldname):
			frappe.db.set_single_value(doctype, fieldname, value)


def _set_translations():
	for language, replacements in TEXT_REPLACEMENTS.items():
		if not frappe.db.exists("Language", language):
			continue
		for source, target in replacements.items():
			existing = frappe.db.get_value(
				"Translation", {"language": language, "source_text": source}, "name"
			)
			if existing:
				frappe.db.set_value("Translation", existing, "translated_text", target)
			else:
				frappe.get_doc({
					"doctype": "Translation",
					"language": language,
					"source_text": source,
					"translated_text": target,
				}).insert(ignore_permissions=True)
