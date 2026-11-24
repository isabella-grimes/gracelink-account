"""Apply G.R.A.C.E accounts branding to a site.

Frappe reads the product name, logo and favicon from site settings
(Website Settings, System Settings, Navbar Settings) before falling back to
app hooks, so this module writes them there.
"""

import frappe

BRAND_NAME = "G.R.A.C.E accounts"
BRAND_LOGO = "/assets/grace_accounting/images/grace-logo.svg"
BRAND_FAVICON = "/assets/grace_accounting/images/grace-favicon.svg"
BRAND_WORDMARK = "/assets/grace_accounting/images/grace-wordmark.svg"

# UI text that says "ERPNext" -> brand name, per language. Applied through
# Frappe's Translation doctype, which overrides strings shown with __() / _().
TEXT_REPLACEMENTS = {
	"en": {
		"ERPNext": BRAND_NAME,
		"ERPNext Settings": f"{BRAND_NAME} Settings",
		"Welcome to ERPNext": f"Welcome to {BRAND_NAME}",
		"Let's give your business a home.": "Let's set up your accounts.",
	},
	"ar": {
		"ERPNext": BRAND_NAME,
		"ERPNext Settings": f"إعدادات {BRAND_NAME}",
		"Welcome to ERPNext": f"مرحبًا بك في {BRAND_NAME}",
		"Let's give your business a home.": "لنجهّز حساباتك.",
	},
}


def apply_branding():
	_set_single("Website Settings", {
		"app_name": BRAND_NAME,
		"app_logo": BRAND_LOGO,
		"favicon": BRAND_FAVICON,
		"splash_image": BRAND_LOGO,
		"brand_html": f'<img src="{BRAND_WORDMARK}" alt="{BRAND_NAME}" style="height: 28px;">',
	})
	_set_single("System Settings", {
		"app_name": BRAND_NAME,
		# Removes the "Sent via ERPNext" footer from outgoing emails
		"disable_standard_email_footer": 1,
	})
	frappe.db.set_default("disable_standard_email_footer", 1)
	_set_single("Navbar Settings", {"app_logo": BRAND_LOGO})
	_set_translations()
	frappe.clear_cache()


def _set_single(doctype, values):
	"""Set fields on a Single doctype, skipping any field this Frappe version lacks."""
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
