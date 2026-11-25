import xml.etree.ElementTree as ET
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from grace_accounting import branding
from grace_accounting.branding import BRAND_NAME, HR_NAME, brand_translations, rebrand_text

IMAGES = Path(__file__).resolve().parent.parent / "public" / "images"
SVG_NS = "{http://www.w3.org/2000/svg}"
ANIMATED = ("grace-logo.svg", "grace-wordmark.svg", "grace-wordmark-light.svg", "grace-hr-logo.svg")


class TestRebrandText(UnitTestCase):
	def test_replaces_product_names_inside_text(self):
		self.assertEqual(rebrand_text("ERPNext"), BRAND_NAME)
		self.assertEqual(rebrand_text("Welcome to ERPNext"), f"Welcome to {BRAND_NAME}")
		self.assertEqual(rebrand_text("Frappe HR"), HR_NAME)
		self.assertEqual(rebrand_text("إعدادات ERPNext"), f"إعدادات {BRAND_NAME}")

	def test_bare_frappe_only_replaced_as_a_whole(self):
		self.assertEqual(rebrand_text("Frappe"), BRAND_NAME)
		self.assertEqual(rebrand_text("Frappe Cloud"), "Frappe Cloud")

	def test_brand_name_is_stable(self):
		self.assertEqual(rebrand_text(BRAND_NAME), BRAND_NAME)
		self.assertEqual(rebrand_text(HR_NAME), HR_NAME)


class TestBrandTranslations(UnitTestCase):
	def test_derives_from_upstream_translation(self):
		result = brand_translations(
			"fr",
			["Welcome to ERPNext", "ERPNext"],
			{"Welcome to ERPNext": "Bienvenue sur ERPNext", "ERPNext": "ERPNext"},
		)
		self.assertEqual(result["Welcome to ERPNext"], f"Bienvenue sur {BRAND_NAME}")
		self.assertEqual(result["ERPNext"], BRAND_NAME)

	def test_falls_back_to_english_source(self):
		result = brand_translations("de", ["ERPNext Settings"], {})
		self.assertEqual(result["ERPNext Settings"], f"{BRAND_NAME} Settings")

	def test_skips_text_that_does_not_change(self):
		# A translator left the product name out: nothing to override.
		result = brand_translations("fr", ["Get to know ERPNext"], {"Get to know ERPNext": "Découvrez"})
		self.assertNotIn("Get to know ERPNext", result)

	def test_hand_written_text_wins_and_covers_variants(self):
		for language in ("ar", "ar-SA"):
			result = brand_translations(language, ["Welcome to ERPNext"], {"Welcome to ERPNext": "x ERPNext"})
			self.assertEqual(result["Welcome to ERPNext"], f"مرحبًا بك في {BRAND_NAME}")
			self.assertIn("Let's give your business a home.", result)


class TestBrandAssets(UnitTestCase):
	def test_svgs_are_valid_and_named(self):
		for name in (*ANIMATED, "grace-favicon.svg"):
			root = ET.parse(IMAGES / name).getroot()
			title = root.find(f"{SVG_NS}title")
			expected = HR_NAME if name == "grace-hr-logo.svg" else BRAND_NAME
			self.assertEqual(title.text, expected, name)
			self.assertEqual(root.get("aria-label"), expected, name)

	def test_animated_logos_respect_reduced_motion(self):
		for name in ANIMATED:
			svg = (IMAGES / name).read_text()
			self.assertIn("@keyframes", svg, name)
			self.assertIn("prefers-reduced-motion: reduce", svg, name)

	def test_favicon_is_static(self):
		svg = (IMAGES / "grace-favicon.svg").read_text()
		self.assertNotIn("@keyframes", svg)

	def test_email_logo_is_a_png(self):
		data = (IMAGES / "grace-email-logo.png").read_bytes()
		self.assertTrue(data.startswith(b"\x89PNG"))


class TestApplyBranding(IntegrationTestCase):
	def test_site_settings_carry_the_brand(self):
		branding.apply_branding()
		self.assertEqual(frappe.db.get_single_value("System Settings", "app_name"), BRAND_NAME)
		self.assertEqual(frappe.db.get_single_value("Website Settings", "app_name"), BRAND_NAME)
		self.assertEqual(frappe.db.get_single_value("Website Settings", "favicon"), branding.BRAND_FAVICON)

	def test_product_names_translated_in_english_and_arabic(self):
		branding.apply_branding()
		for language in ("en", "ar"):
			self.assertEqual(_translation(language, "ERPNext"), BRAND_NAME, language)
			self.assertEqual(_translation(language, "Frappe HR"), HR_NAME, language)

	def test_catalog_strings_naming_erpnext_are_rebranded(self):
		sources = branding.get_branded_sources()
		self.assertIn("ERPNext Settings", sources)
		self.assertTrue(all(branding.needs_rebrand(s) for s in sources))

	def test_new_user_language_gets_branded(self):
		language = "fr"
		frappe.db.delete("Translation", {"language": language})
		user = frappe.get_doc("User", "Administrator")
		original = user.language
		try:
			user.language = language
			user.save(ignore_permissions=True)
			self.assertEqual(_translation(language, "ERPNext"), BRAND_NAME)
		finally:
			frappe.db.set_value("User", "Administrator", "language", original)

	def test_old_brand_is_replaced_on_upgrade(self):
		# What a site set up by the previous version of this app holds.
		frappe.db.delete("Translation", {"language": "en", "source_text": "ERPNext Settings"})
		frappe.get_doc(
			{
				"doctype": "Translation",
				"language": "en",
				"source_text": "ERPNext Settings",
				"translated_text": "G.R.A.C.E accounts Settings",
			}
		).insert(ignore_permissions=True)
		branding.apply_branding()
		self.assertEqual(_translation("en", "ERPNext Settings"), f"{BRAND_NAME} Settings")
		self.assertFalse(frappe.db.exists("Translation", {"translated_text": ("like", "%G.R.A.C.E%")}))


def _translation(language: str, source: str) -> str | None:
	return frappe.db.get_value("Translation", {"language": language, "source_text": source}, "translated_text")
