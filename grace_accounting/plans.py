"""Subscription plans for G.R.A.C.E accounts tenants.

Each customer business is one site. The platform operator sets that
site's plan in its site_config.json, which tenants cannot edit:

    bench --site acme.example.sa set-config grace_plan basic

Optional per-tenant overrides of any limit:

    bench --site acme.example.sa set-config -p grace_limits '{"users": 8}'

A limit of None means unlimited. Sites with no grace_plan set (for example
your own internal site) are not limited at all.
"""

import frappe
from frappe import _
from frappe.utils import get_first_day, nowdate

UNLIMITED = None

PLANS = {
	"economic": {
		"title": "Economic",
		"title_ar": "الاقتصادية",
		"users": 2,
		"invoices_per_month": 300,
		"warehouses": 1,
		"companies": 1,
		"hr": False,
	},
	"basic": {
		"title": "Basic",
		"title_ar": "الأساسية",
		"users": 5,
		"invoices_per_month": 2000,
		"warehouses": 3,
		"companies": 2,
		"hr": False,
	},
	"comprehensive": {
		"title": "Comprehensive",
		"title_ar": "الشاملة",
		"users": 15,
		"invoices_per_month": UNLIMITED,
		"warehouses": 10,
		"companies": 5,
		"hr": True,
	},
}

# Warehouses ERPNext creates on its own for every company. They don't count.
# ERPNext names them in the site's language at setup (e.g. Arabic), so match both.
DEFAULT_WAREHOUSES = ("Stores", "Work In Progress", "Finished Goods", "Goods In Transit")
INVOICE_DOCTYPES = ("Sales Invoice", "POS Invoice")
NON_COUNTED_USERS = ("Administrator", "Guest")


class PlanLimitError(frappe.ValidationError):
	pass


# ---------------------------------------------------------------- plan lookup


def get_plan_name() -> str | None:
	return frappe.conf.get("grace_plan") or None


def get_limits() -> dict | None:
	"""The active limits for this site, or None if the site has no plan."""
	plan_name = get_plan_name()
	if not plan_name:
		return None
	if plan_name not in PLANS:
		frappe.throw(_("Unknown subscription plan '{0}'. Contact support.").format(plan_name))
	limits = dict(PLANS[plan_name])
	limits.update(frappe.conf.get("grace_limits") or {})
	return limits


def _skip_checks() -> bool:
	flags = frappe.flags
	return bool(
		flags.in_install
		or flags.in_migrate
		or flags.in_patch
		or flags.in_setup_wizard
		or flags.in_import
		or flags.in_test
	)


def _check(limit_key: str, used: int, label: str):
	limits = get_limits()
	if not limits or _skip_checks():
		return
	limit = limits.get(limit_key, UNLIMITED)
	if limit is not UNLIMITED and used >= limit:
		frappe.throw(
			_(
				"Your {0} plan allows {1} {2}. Upgrade your plan to add more."
			).format(_(limits["title"]), limit, _(label)),
			exc=PlanLimitError,
			title=_("Plan limit reached"),
		)


# ---------------------------------------------------------------- usage


def count_users() -> int:
	return frappe.db.count(
		"User",
		{"enabled": 1, "user_type": "System User", "name": ("not in", NON_COUNTED_USERS)},
	)


def count_invoices_this_month() -> int:
	start = get_first_day(nowdate())
	return sum(
		frappe.db.count(dt, {"posting_date": (">=", start), "docstatus": ("!=", 2)})
		for dt in INVOICE_DOCTYPES
		if frappe.db.table_exists(dt)
	)


def _translated(name: str) -> set[str]:
	langs = {"en", frappe.db.get_single_value("System Settings", "language") or "en"}
	return {name} | {_(name, lang=lang) for lang in langs}


def default_warehouse_names() -> set[str]:
	return set().union(*(_translated(n) for n in DEFAULT_WAREHOUSES))


def count_warehouses() -> int:
	names = frappe.get_all(
		"Warehouse", filters={"is_group": 0, "disabled": 0}, pluck="warehouse_name"
	)
	# Count the main "Stores" warehouse once, so a limit of 1 means "just the main store".
	defaults, stores = default_warehouse_names(), _translated("Stores")
	custom = [n for n in names if n not in defaults]
	return len(custom) + (1 if any(n in stores for n in names) else 0)


def count_companies() -> int:
	return frappe.db.count("Company")


@frappe.whitelist()
def get_usage() -> dict:
	"""Plan and current usage, for the tenant's own admins."""
	frappe.only_for(("System Manager", "Administrator"))
	limits = get_limits()
	return {
		"plan": get_plan_name(),
		"limits": limits,
		"usage": {
			"users": count_users(),
			"invoices_per_month": count_invoices_this_month(),
			"warehouses": count_warehouses(),
			"companies": count_companies(),
		},
	}


# ---------------------------------------------------------------- doc events


def validate_user(doc, method=None):
	if doc.name in NON_COUNTED_USERS or not doc.enabled or doc.user_type != "System User":
		return
	was_counted = False
	if not doc.is_new():
		before = frappe.db.get_value("User", doc.name, ["enabled", "user_type"], as_dict=True)
		was_counted = bool(before and before.enabled and before.user_type == "System User")
	if not was_counted:
		_check("users", count_users(), "users")


def before_insert_invoice(doc, method=None):
	_check("invoices_per_month", count_invoices_this_month(), "invoices per month")


def before_insert_warehouse(doc, method=None):
	if doc.is_group or doc.warehouse_name in default_warehouse_names():
		return
	_check("warehouses", count_warehouses(), "warehouses")


def before_insert_company(doc, method=None):
	if count_companies() == 0:
		return  # the first company, created by the setup wizard
	_check("companies", count_companies(), "companies")


# ---------------------------------------------------------------- HR module gate


def _hr_allowed(user: str | None = None) -> bool:
	if (user or frappe.session.user) == "Administrator":
		return True
	limits = get_limits()
	return not limits or bool(limits.get("hr"))


def _hr_modules() -> set[str]:
	def fetch():
		if not frappe.db.exists("DocType", "Module Def"):
			return []
		return frappe.get_all("Module Def", filters={"app_name": "hrms"}, pluck="name")

	return set(frappe.cache.get_value("grace_hr_modules", fetch) or [])


def _is_hr_doctype(doctype: str) -> bool:
	try:
		return frappe.get_meta(doctype).module in _hr_modules()
	except frappe.DoesNotExistError:
		return False


def has_permission(doc, ptype=None, user=None, debug=False):
	"""Deny HR/Payroll documents on plans without HR.

	A falsy return means "deny", so everything else must return True
	(which only means "no objection": it never grants a permission the user lacks).
	"""
	if _hr_allowed(user):
		return True
	return not _is_hr_doctype(doc.doctype)


def permission_query_conditions(user=None, doctype=None):
	"""Hide HR/Payroll lists on plans without HR."""
	if not doctype or _hr_allowed(user):
		return ""
	if _is_hr_doctype(doctype):
		return "1=0"
	return ""


def boot_session(bootinfo):
	limits = get_limits()
	bootinfo.grace_plan = {"name": get_plan_name(), "limits": limits} if limits else None
