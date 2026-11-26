"""Apply GraceERP Solution branding to a site.

The product name, logo and favicon are read from site settings
(Website Settings, System Settings, Navbar Settings) before falling back to
app hooks, so this module writes them there.

The brand name is never translated: "GraceERP Solution" reads the same in
every language. Upstream product names ("ERPNext", "Frappe HR", "Frappe") are
replaced in every language used on the site, through the Translation doctype,
so the rest of the UI stays fully multilingual.
"""

from pathlib import Path

import frappe

BRAND_NAME = "GraceERP Solution"
BRAND_LOGO = "/assets/grace_accounting/images/grace-logo.svg"
BRAND_FAVICON = "/assets/grace_accounting/images/grace-favicon.svg"
BRAND_WORDMARK = "/assets/grace_accounting/images/grace-wordmark.svg"
BRAND_HR_LOGO = "/assets/grace_accounting/images/grace-hr-logo.svg"
HR_NAME = "GraceERP HR"

# Help/user menu items that point at the underlying open-source projects (removed).
UPSTREAM_MARKERS = ("frappe", "erpnext", "github.com", "discuss.", "school")

# Upstream name -> brand name, applied inside any text. Order matters:
# "Frappe HR" is replaced first, as a whole.
NAME_REPLACEMENTS = (
	("Frappe HR", HR_NAME),
	("ERPNext", BRAND_NAME),
)

# Source strings that are just a product name. Replaced only as a whole,
# never inside other text: "Frappe" also appears in "Frappe Cloud", "frappe.io", etc.
EXACT_REPLACEMENTS = {
	"Frappe": BRAND_NAME,
}

# Hand-written wording for some languages. It takes priority over the text
# derived from upstream translations.
CUSTOM_TEXT = {
	"en": {
		"Let's give your business a home.": "Let's set up your accounts.",
		"Let's build a workplace your team will love.": "Let's set up your team and payroll.",
	},
	"ar": {
		"ERPNext Settings": f"إعدادات {BRAND_NAME}",
		"Welcome to ERPNext": f"مرحبًا بك في {BRAND_NAME}",
		"Get to know ERPNext": f"تعرّف على {BRAND_NAME}",
		"Let's give your business a home.": "لنجهّز حساباتك.",
		"Let's build a workplace your team will love.": "لنجهّز فريقك ورواتبهم.",
	},
}

# Always branded, even when an app's message catalog doesn't list them.
BASE_SOURCES = (
	"ERPNext",
	"ERPNext Settings",
	"Welcome to ERPNext",
	"Get to know ERPNext",
	"Frappe HR",
	"Frappe",
)


# ---------------------------------------------------------------- pure helpers


def rebrand_text(text: str) -> str:
	"""Replace upstream product names inside a piece of UI text."""
	if text in EXACT_REPLACEMENTS:
		return EXACT_REPLACEMENTS[text]
	for upstream, ours in NAME_REPLACEMENTS:
		text = text.replace(upstream, ours)
	return text


def needs_rebrand(source: str) -> bool:
	return source in EXACT_REPLACEMENTS or any(upstream in source for upstream, _ in NAME_REPLACEMENTS)


def brand_translations(language: str, sources, upstream: dict[str, str]) -> dict[str, str]:
	"""The Translation records a language needs, as {source text: branded text}.

	`upstream` holds the language's translations shipped with the apps. The
	branded text is the upstream translation (or the English source when there
	is none) with the product names replaced. Hand-written CUSTOM_TEXT wins.
	Sources whose text would not change are left out.
	"""
	custom = CUSTOM_TEXT.get(language) or CUSTOM_TEXT.get(language.split("-")[0], {})
	result = {}
	for source in sources:
		current = upstream.get(source) or source
		target = custom.get(source) or rebrand_text(current)
		if target != current or source in custom:
			result[source] = target
	for source, target in custom.items():
		result.setdefault(source, target)
	return result


# ---------------------------------------------------------------- site setup


def apply_branding():
	_set_single(
		"Website Settings",
		{
			"app_name": BRAND_NAME,
			"app_logo": BRAND_LOGO,
			"favicon": BRAND_FAVICON,
			"splash_image": BRAND_LOGO,
			"brand_html": f'<img src="{BRAND_WORDMARK}" alt="{BRAND_NAME}" style="height: 32px;">',
			# Website footer ("Built on ...")
			"footer_powered": BRAND_NAME,
		},
	)
	_set_single(
		"System Settings",
		{
			"app_name": BRAND_NAME,
			# Removes the "Sent via ERPNext" footer from outgoing emails
			"disable_standard_email_footer": 1,
		},
	)
	frappe.db.set_default("disable_standard_email_footer", 1)
	_set_single("Navbar Settings", {"app_logo": BRAND_LOGO})
	_clean_navbar_menus()
	set_translations()
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
			r
			for r in rows
			if not any(
				m in f"{r.item_label or ''} {r.route or ''} {r.action or ''}".lower() for m in UPSTREAM_MARKERS
			)
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
	bootinfo.grace_brand_name = BRAND_NAME


def _set_single(doctype, values):
	"""Set fields on a Single doctype, skipping any field this version lacks."""
	if not frappe.db.exists("DocType", doctype):
		return
	meta = frappe.get_meta(doctype)
	for fieldname, value in values.items():
		if meta.has_field(fieldname):
			frappe.db.set_single_value(doctype, fieldname, value)


# ---------------------------------------------------------------- translations


def get_branded_sources() -> list[str]:
	"""Every UI source string of the installed apps that names an upstream product."""
	from babel.messages.pofile import read_po

	sources = set(BASE_SOURCES)
	for app in frappe.get_installed_apps():
		pot = Path(frappe.get_app_path(app, "locale", "main.pot"))
		if not pot.exists():
			continue
		with pot.open("rb") as f:
			catalog = read_po(f)
		for message in catalog:
			if message.id and isinstance(message.id, str) and not message.context and needs_rebrand(message.id):
				sources.add(message.id)
	return sorted(sources)


def get_site_languages() -> list[str]:
	"""Languages in use on this site: English, Arabic, the system default and each user's language."""
	languages = {"en", "ar", frappe.db.get_single_value("System Settings", "language") or "en"}
	languages.update(
		frappe.get_all("User", filters={"enabled": 1, "language": ("is", "set")}, pluck="language", distinct=True)
	)
	return sorted(lang for lang in languages if lang and frappe.db.exists("Language", lang))


def set_translations(languages: list[str] | None = None):
	from frappe.translate import get_translations_from_apps

	sources = get_branded_sources()
	for language in languages or get_site_languages():
		wanted = brand_translations(language, sources, get_translations_from_apps(language))
		existing = {
			row.source_text: row
			for row in frappe.get_all(
				"Translation",
				filters={"language": language, "source_text": ("in", list(wanted))},
				fields=["name", "source_text", "translated_text"],
			)
		}
		for source, target in wanted.items():
			row = existing.get(source)
			if row and row.translated_text != target:
				frappe.db.set_value("Translation", row.name, "translated_text", target)
			elif not row:
				frappe.get_doc(
					{
						"doctype": "Translation",
						"language": language,
						"source_text": source,
						"translated_text": target,
					}
				).insert(ignore_permissions=True)


def on_language_change(doc, method=None):
	"""Brand a language as soon as a user or the system starts using it."""
	if frappe.flags.in_install or frappe.flags.in_migrate:
		return
	language = doc.get("language")
	if not language or not doc.has_value_changed("language"):
		return
	set_translations([language])
	frappe.translate.clear_cache()
