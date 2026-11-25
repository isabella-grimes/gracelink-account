// GraceERP Solution: desk branding that can't be done with settings or CSS.
(function () {
	const BRAND = "GraceERP Solution"; // never translated: the same in every language
	const WORDMARK = "/assets/grace_accounting/images/grace-wordmark.svg";
	const WORDMARK_LIGHT = "/assets/grace_accounting/images/grace-wordmark-light.svg";
	const is_dark = () => document.documentElement.getAttribute("data-theme") === "dark";

	function grace_version() {
		const versions = (frappe.boot && frappe.boot.versions) || {};
		return versions.grace_accounting || "";
	}

	// Replace the stock About dialog (framework logo, links and versions).
	function about() {
		const support = frappe.boot.grace_support_url;
		const LICENSES = {
			subscription: __("Monthly subscription · Hosted and supported 24/7 by GraceERP"),
			lifetime: __("Lifetime licence · Self-hosted"),
		};
		const license = LICENSES[frappe.boot.grace_license] || "";
		const dialog = new frappe.ui.Dialog({ title: __("About") });
		$(dialog.body).html(`
			<div class="grace-about" style="display:flex;flex-direction:column;align-items:center;gap:14px;padding:12px 0 6px;text-align:center">
				<img src="${is_dark() ? WORDMARK_LIGHT : WORDMARK}" alt="${BRAND}" style="height:56px">
				<p class="text-muted" style="margin:0">${__("ZATCA-compliant ERP and accounting for Saudi and Gulf businesses.")}</p>
				${license ? `<p class="small" style="margin:0;color:var(--grace-gold, #b88020);font-weight:600">${license}</p>` : ""}
				${grace_version() ? `<p class="text-muted small" style="margin:0">${__("Version")} ${frappe.utils.escape_html(grace_version())}</p>` : ""}
				${
					support
						? `<a class="btn btn-primary btn-sm" href="${encodeURI(support)}" target="_blank" rel="noopener">${__("Contact Support")}</a>`
						: ""
				}
				<p class="text-muted small" style="margin:6px 0 0">© ${new Date().getFullYear()} ${BRAND}</p>
			</div>`);
		dialog.show();
	}

	// Rename/re-logo the underlying apps before the desk draws the app switcher,
	// sidebar header and apps screen (frappe.boot is already set when this runs).
	const TILES = {
		erpnext: { title: BRAND, logo: "/assets/grace_accounting/images/grace-logo.svg" },
		hrms: { title: "GraceERP HR", logo: "/assets/grace_accounting/images/grace-hr-logo.svg" },
		frappe: { title: __("System"), logo: "/assets/grace_accounting/images/grace-logo.svg" },
	};
	function rebrand_boot(boot) {
		if (!boot) return;
		(boot.app_data || []).forEach((app) => {
			const t = TILES[app.app_name];
			if (t) Object.assign(app, { app_title: t.title, app_logo_url: t.logo });
		});
		((boot.apps_data && boot.apps_data.apps) || []).forEach((app) => {
			const t = TILES[app.name];
			if (t) Object.assign(app, { title: t.title, logo: t.logo });
		});
		(boot.desktop_icons || []).forEach((icon) => {
			const t = TILES[icon.app] && /erpnext|frappe/i.test(icon.label || "") ? TILES[icon.app] : null;
			if (t) Object.assign(icon, { label: t.title, logo_url: t.logo });
		});
	}
	rebrand_boot(window.frappe && frappe.boot);

	frappe.provide("frappe.ui.misc");
	frappe.provide("frappe.ui.toolbar");
	frappe.ui.misc.about = about;
	frappe.ui.toolbar.show_about = about;
})();
