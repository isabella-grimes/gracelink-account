from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from grace_accounting import plans


def site_config(**values):
	"""Temporarily set site_config.json values (as the platform operator would)."""
	clean = {"grace_license": None, "grace_plan": None, "grace_limits": None}
	clean.update(values)
	return patch.dict(frappe.local.conf, clean)


# The real checks are skipped while tests run (frappe.flags.in_test); turn them back on.
enforce = patch.object(plans, "_skip_checks", return_value=False)


class TestCommercialModels(IntegrationTestCase):
	def test_lifetime_licence_has_no_limits(self):
		with site_config(grace_license="lifetime", grace_plan="economic"):
			self.assertEqual(plans.get_license_type(), "lifetime")
			self.assertIsNone(plans.get_limits())

	def test_subscription_uses_the_plan_tiers(self):
		with site_config(grace_license="subscription", grace_plan="basic"):
			self.assertEqual(plans.get_license_type(), "subscription")
			self.assertEqual(plans.get_limits()["users"], 5)

	def test_sites_without_a_licence_type_keep_todays_behaviour(self):
		with site_config(grace_plan="basic"):
			self.assertIsNone(plans.get_license_type())
			self.assertEqual(plans.get_limits()["users"], 5)
		with site_config():
			self.assertIsNone(plans.get_limits())

	def test_unknown_licence_type_is_rejected(self):
		with site_config(grace_license="forever"), self.assertRaises(frappe.ValidationError):
			plans.get_license_type()

	def test_lifetime_never_blocks_invoices(self):
		with site_config(grace_license="lifetime", grace_plan="economic", grace_limits={"invoices_per_month": 0}):
			with enforce:
				plans.before_insert_invoice(frappe._dict(doctype="Sales Invoice"))

	def test_subscription_blocks_invoices_over_the_cap(self):
		with site_config(grace_license="subscription", grace_plan="economic", grace_limits={"invoices_per_month": 0}):
			with enforce, self.assertRaises(plans.PlanLimitError):
				plans.before_insert_invoice(frappe._dict(doctype="Sales Invoice"))

	def test_travel_invoices_are_never_capped(self):
		travel_invoice = frappe._dict(doctype="Sales Invoice", travel_reference_doctype="Air Ticket")
		with site_config(grace_license="subscription", grace_plan="economic", grace_limits={"invoices_per_month": 0}):
			with enforce:
				plans.before_insert_invoice(travel_invoice)

	def test_travel_invoices_are_not_counted(self):
		calls = []

		def fake_count(doctype, filters):
			calls.append(filters)
			return 0

		with patch.object(plans, "_has_travel_reference", return_value=True), patch.object(
			frappe.db, "count", side_effect=fake_count
		):
			plans.count_invoices_this_month()
		self.assertTrue(calls)
		self.assertTrue(all(f.get("travel_reference_doctype") == ("is", "not set") for f in calls))

	def test_boot_tells_the_desk_which_model_applies(self):
		for licence in ("subscription", "lifetime"):
			with site_config(grace_license=licence, grace_plan="basic"):
				bootinfo = frappe._dict()
				plans.boot_session(bootinfo)
				self.assertEqual(bootinfo.grace_license, licence)
