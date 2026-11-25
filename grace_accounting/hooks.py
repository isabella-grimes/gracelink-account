app_name = "grace_accounting"
app_title = "G.R.A.C.E accounts"
app_publisher = "GraceLink"
app_description = "G.R.A.C.E accounts: branding and theme for ERPNext"
app_email = "info@gracelink.sa"
app_license = "gpl-3.0"

required_apps = ["frappe/erpnext"]

BRAND_LOGO = "/assets/grace_accounting/images/grace-logo.svg"
BRAND_FAVICON = "/assets/grace_accounting/images/grace-favicon.svg"

app_logo_url = BRAND_LOGO

# Theme for the desk (/app) and for the website/login pages
app_include_css = ["/assets/grace_accounting/css/grace_theme.css"]
app_include_js = ["/assets/grace_accounting/js/grace.js"]
web_include_css = ["/assets/grace_accounting/css/grace_theme.css"]

# Installed after ERPNext, so these values win over ERPNext's favicon and splash
website_context = {
	"favicon": BRAND_FAVICON,
	"splash_image": BRAND_LOGO,
}

# PNG, because many email apps (Gmail, Outlook) don't show SVG images
email_brand_image = "assets/grace_accounting/images/grace-email-logo.png"

# Write the brand name, logo, favicon and translations into the site settings.
# Runs on install and again on every `bench migrate`, so an ERPNext update
# can't bring the ERPNext name back.
after_install = "grace_accounting.branding.apply_branding"
after_migrate = "grace_accounting.branding.apply_branding"

# ---------------------------------------------------------------- subscription plans
# Limits per tenant site; see grace_accounting/plans.py
doc_events = {
	"User": {"validate": "grace_accounting.plans.validate_user"},
	"Sales Invoice": {"before_insert": "grace_accounting.plans.before_insert_invoice"},
	"POS Invoice": {"before_insert": "grace_accounting.plans.before_insert_invoice"},
	"Warehouse": {"before_insert": "grace_accounting.plans.before_insert_warehouse"},
	"Company": {"before_insert": "grace_accounting.plans.before_insert_company"},
}

has_permission = {"*": "grace_accounting.plans.has_permission"}
permission_query_conditions = {"*": "grace_accounting.plans.permission_query_conditions"}

boot_session = [
	"grace_accounting.plans.boot_session",
	"grace_accounting.branding.boot_session",
]
