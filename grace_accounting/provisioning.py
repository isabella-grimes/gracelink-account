"""Ready-to-use tenant setup, run by the platform's new-tenant script.

    bench --site acme.example.sa execute grace_accounting.provisioning.setup_tenant \
        --kwargs '{"company_name": "Acme Trading", "owner_email": "owner@acme.sa",
                   "owner_name": "Ahmed Ali", "owner_password": "..."}'

Completes ERPNext's setup wizard with Saudi defaults (SAR, Asia/Riyadh,
Arabic, calendar fiscal year), so the customer's owner logs straight into a
working company. The owner gets System Manager and full access to their own
site; the Administrator login stays with the platform operator.
"""

import re

import frappe
from frappe.utils import getdate, nowdate


def setup_tenant(
	company_name: str,
	owner_email: str,
	owner_name: str,
	owner_password: str,
	company_abbr: str | None = None,
	language: str = "ar",
	country: str = "Saudi Arabia",
	currency: str = "SAR",
	timezone: str = "Asia/Riyadh",
):
	from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

	if frappe.is_setup_complete():
		print("Setup is already complete on this site; nothing to do.")
		return

	year = getdate(nowdate()).year
	language_name = frappe.db.get_value("Language", language, "language_name") or "English"

	result = setup_complete(
		{
			"language": language_name,
			"country": country,
			"currency": currency,
			"timezone": timezone,
			"full_name": owner_name,
			"email": owner_email,
			"password": owner_password,
			"company_name": company_name,
			"company_abbr": company_abbr or make_abbr(company_name),
			"chart_of_accounts": "Standard",
			"fy_start_date": f"{year}-01-01",
			"fy_end_date": f"{year}-12-31",
			"setup_demo": 0,
		}
	)
	frappe.db.commit()

	if not frappe.is_setup_complete():
		raise Exception(f"Setup wizard did not complete: {result}")

	# Re-apply branding: the wizard resets a few settings (e.g. app name defaults).
	from grace_accounting.branding import apply_branding

	apply_branding()
	frappe.db.commit()
	print(f"Tenant ready: company '{company_name}', owner {owner_email}")


def make_abbr(company_name: str) -> str:
	words = re.findall(r"[A-Za-z0-9]+", company_name)
	abbr = "".join(w[0] for w in words).upper()[:5]
	return abbr or "CO"
