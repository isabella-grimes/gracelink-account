"""Sample data for demo tenants (sales demos, screenshots, training).

    bench --site demo.example.sa execute grace_accounting.demo.create_demo_data

Adds Saudi customers and suppliers, products and services, a 15% VAT
template, three months of sales and purchase invoices with payments, and
a few employees. Safe to run once per site; it refuses to run twice.
"""

import random

import frappe
from frappe.utils import add_days, getdate, nowdate

CUSTOMERS = [
	# name, type, VAT number (B2B only), city
	("Al Rajhi Contracting Co.", "Company", "310122393500003", "Riyadh"),
	("Makkah Hospitality Group", "Company", "310245781200003", "Makkah"),
	("Jeddah Marine Supplies", "Company", "310378452100003", "Jeddah"),
	("Dammam Logistics LLC", "Company", "310491236500003", "Dammam"),
	("Madinah Travel & Tours", "Company", "310512478900003", "Madinah"),
	("Abdullah Al-Qahtani", "Individual", None, "Riyadh"),
	("Noura Al-Shehri", "Individual", None, "Jeddah"),
	("Walk-in Customer", "Individual", None, "Riyadh"),
]

SUPPLIERS = [
	("Saudi Office Supplies Co.", "310600123400003"),
	("Gulf IT Solutions", "310711234500003"),
	("Riyadh Facilities Management", "310822345600003"),
]

# code, name, rate, is_stock_item, is_purchase_only
ITEMS = [
	("SRV-CONSULT", "Accounting Consultation (hour)", 450, 0, 0),
	("SRV-AUDIT", "Annual Audit Package", 12500, 0, 0),
	("SRV-ZATCA", "ZATCA E-Invoicing Setup", 3500, 0, 0),
	("SRV-PAYROLL", "Monthly Payroll Service", 1800, 0, 0),
	("PRD-POS", "POS Terminal", 2200, 1, 0),
	("PRD-PRINTER", "Thermal Receipt Printer", 650, 1, 0),
	("EXP-OFFICE", "Office Supplies", 900, 0, 1),
	("EXP-IT", "IT Services", 2400, 0, 1),
	("EXP-FACILITY", "Facility Maintenance", 3100, 0, 1),
]

EMPLOYEES = [
	("Faisal", "Al-Otaibi", "Male", "1988-03-14", "Finance Manager"),
	("Reem", "Al-Ghamdi", "Female", "1993-07-02", "Accountant"),
	("Omar", "Al-Zahrani", "Male", "1990-11-21", "Sales Executive"),
	("Hessa", "Al-Dosari", "Female", "1995-01-30", "HR Officer"),
]


def create_demo_data(company: str | None = None, months: int = 3, seed: int = 7):
	company = company or frappe.defaults.get_global_default("company") or frappe.get_all("Company", pluck="name")[0]
	if frappe.db.exists("Customer", {"customer_name": CUSTOMERS[0][0]}):
		print("Demo data already exists on this site; nothing to do.")
		return
	rnd = random.Random(seed)
	frappe.flags.in_import = True  # demo data shouldn't count against plan limits
	try:
		ctx = _context(company)
		_items(ctx)
		_parties(ctx)
		vat = _vat_templates(ctx)
		_sales(ctx, vat, months, rnd)
		_purchases(ctx, vat, months, rnd)
		_employees(ctx)
		frappe.db.commit()
	finally:
		frappe.flags.in_import = False
	print(f"Demo data created for {company}")


# ---------------------------------------------------------------- setup


def _root(doctype):
	parent_field = f"parent_{frappe.scrub(doctype)}"
	return frappe.db.get_value(doctype, {"is_group": 1, parent_field: ("in", ("", None))}, "name")


def _leaf(doctype, settings_doctype, fieldname):
	"""The default (non-group) value from settings, else any non-group record."""
	value = frappe.db.get_single_value(settings_doctype, fieldname)
	if value and not frappe.db.get_value(doctype, value, "is_group"):
		return value
	return frappe.db.get_value(doctype, {"is_group": 0}, "name")


def _context(company):
	abbr = frappe.get_cached_value("Company", company, "abbr")
	uom = "Nos" if frappe.db.exists("UOM", "Nos") else frappe.db.get_value("UOM", {}, "name")
	warehouse = frappe.get_cached_value("Company", company, "default_warehouse_for_sales_return") or frappe.db.get_value(
		"Warehouse", {"company": company, "is_group": 0}, "name"
	)
	return frappe._dict(
		company=company,
		abbr=abbr,
		uom=uom,
		warehouse=warehouse,
		item_group=_root("Item Group"),
		customer_group=_leaf("Customer Group", "Selling Settings", "customer_group"),
		supplier_group=_leaf("Supplier Group", "Buying Settings", "supplier_group"),
		territory=_leaf("Territory", "Selling Settings", "territory"),
		currency=frappe.get_cached_value("Company", company, "default_currency"),
		selling_price_list=frappe.db.get_single_value("Selling Settings", "selling_price_list")
		or frappe.db.get_value("Price List", {"selling": 1, "enabled": 1}, "name"),
		buying_price_list=frappe.db.get_single_value("Buying Settings", "buying_price_list")
		or frappe.db.get_value("Price List", {"buying": 1, "enabled": 1}, "name"),
	)


def _items(ctx):
	for code, name, rate, is_stock, purchase_only in ITEMS:
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": code,
				"item_name": name,
				"item_group": ctx.item_group,
				"stock_uom": ctx.uom,
				"is_stock_item": is_stock,
				"is_sales_item": 0 if purchase_only else 1,
				"is_purchase_item": 1,
				"standard_rate": rate,
				"opening_stock": 50 if is_stock else 0,
				"valuation_rate": round(rate * 0.6, 2) if is_stock else 0,
			}
		).insert(ignore_permissions=True)


def _parties(ctx):
	for name, ctype, vat, city in CUSTOMERS:
		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": name,
				"customer_type": ctype,
				"customer_group": ctx.customer_group,
				"territory": ctx.territory,
				"tax_id": vat,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Address",
				"address_title": name,
				"address_type": "Billing",
				"address_line1": "King Fahd Road",
				"city": city,
				"pincode": "12345",
				"country": "Saudi Arabia",
				"is_primary_address": 1,
				"links": [{"link_doctype": "Customer", "link_name": customer.name}],
			}
		).insert(ignore_permissions=True)
	for name, vat in SUPPLIERS:
		frappe.get_doc(
			{"doctype": "Supplier", "supplier_name": name, "supplier_group": ctx.supplier_group,
			 "supplier_type": "Company", "tax_id": vat}
		).insert(ignore_permissions=True)


def _vat_templates(ctx):
	parent = frappe.db.get_value("Account", {"company": ctx.company, "is_group": 1, "account_type": "Tax"}, "name")
	account_name = "VAT 15%"
	account = frappe.db.get_value("Account", {"company": ctx.company, "account_name": account_name}, "name")
	if not account:
		account = (
			frappe.get_doc(
				{
					"doctype": "Account",
					"account_name": account_name,
					"company": ctx.company,
					"parent_account": parent,
					"account_type": "Tax",
					"tax_rate": 15,
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
	templates = {}
	for doctype in ("Sales Taxes and Charges Template", "Purchase Taxes and Charges Template"):
		tpl = frappe.get_doc(
			{
				"doctype": doctype,
				"title": "KSA VAT 15%",
				"company": ctx.company,
				"is_default": 1,
				"taxes": [
					{
						"charge_type": "On Net Total",
						"account_head": account,
						"description": "VAT 15%",
						"rate": 15,
						**({"category": "Total", "add_deduct_tax": "Add"} if doctype.startswith("Purchase") else {}),
					}
				],
			}
		).insert(ignore_permissions=True)
		templates[doctype] = tpl.name
	return templates


# ---------------------------------------------------------------- transactions


def _dates(months, count, rnd):
	today = getdate(nowdate())
	span = months * 30
	return sorted(add_days(today, -rnd.randint(0, span)) for _ in range(count))


def _sales(ctx, vat, months, rnd):
	sellable = [i for i in ITEMS if not i[4]]
	for posting_date in _dates(months, 24, rnd):
		customer = rnd.choice(CUSTOMERS)[0]
		lines = rnd.sample(sellable, rnd.randint(1, 3))
		inv = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"company": ctx.company,
				"customer": customer,
				"currency": ctx.currency,
				"conversion_rate": 1,
				"selling_price_list": ctx.selling_price_list,
				"price_list_currency": ctx.currency,
				"plc_conversion_rate": 1,
				"set_posting_time": 1,
				"posting_date": posting_date,
				"posting_time": f"{rnd.randint(9, 20):02d}:{rnd.randint(0, 59):02d}:00",
				"due_date": add_days(posting_date, 30),
				"taxes_and_charges": vat["Sales Taxes and Charges Template"],
				# Billing only (no stock movement), so back-dated demo invoices
				# don't run into the opening stock dated today.
				"update_stock": 0,
				"items": [
					{"item_code": code, "qty": rnd.randint(1, 4), "rate": rate}
					for code, _name, rate, _stock, _p in lines
				],
			}
		)
		inv.set_missing_values()
		inv.set_taxes()
		inv.insert(ignore_permissions=True)
		inv.submit()
		# Most invoices get paid; the newest ones stay outstanding
		if (getdate(nowdate()) - getdate(posting_date)).days > 20 and rnd.random() < 0.8:
			_pay("Sales Invoice", inv.name, posting_date)


def _purchases(ctx, vat, months, rnd):
	expenses = [i for i in ITEMS if i[4]]
	for posting_date in _dates(months, 9, rnd):
		code, _name, rate, _stock, _p = rnd.choice(expenses)
		inv = frappe.get_doc(
			{
				"doctype": "Purchase Invoice",
				"company": ctx.company,
				"supplier": rnd.choice(SUPPLIERS)[0],
				"currency": ctx.currency,
				"conversion_rate": 1,
				"buying_price_list": ctx.buying_price_list,
				"price_list_currency": ctx.currency,
				"plc_conversion_rate": 1,
				"set_posting_time": 1,
				"posting_date": posting_date,
				"posting_time": f"{rnd.randint(9, 20):02d}:{rnd.randint(0, 59):02d}:00",
				"bill_date": posting_date,
				"due_date": add_days(posting_date, 30),
				"taxes_and_charges": vat["Purchase Taxes and Charges Template"],
				"items": [{"item_code": code, "qty": 1, "rate": rate}],
			}
		)
		inv.set_missing_values()
		inv.set_taxes()
		inv.insert(ignore_permissions=True)
		inv.submit()
		if rnd.random() < 0.7:
			_pay("Purchase Invoice", inv.name, posting_date)


def _pay(doctype, name, posting_date):
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	pe = get_payment_entry(doctype, name)
	pe.posting_date = add_days(posting_date, 7)
	pe.reference_no = f"TRX-{name}"
	pe.reference_date = pe.posting_date
	pe.insert(ignore_permissions=True)
	pe.submit()


def _employees(ctx):
	if not frappe.db.exists("DocType", "Employee"):
		return
	for first, last, gender, dob, designation in EMPLOYEES:
		if not frappe.db.exists("Designation", designation):
			frappe.get_doc({"doctype": "Designation", "designation_name": designation}).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": first,
				"last_name": last,
				"gender": gender,
				"date_of_birth": dob,
				"date_of_joining": "2024-01-01",
				"company": ctx.company,
				"designation": designation,
				"status": "Active",
			}
		).insert(ignore_permissions=True)
