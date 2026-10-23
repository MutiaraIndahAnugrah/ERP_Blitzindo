// Copyright (c) 2022, Kulkul and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Product Bundle Price Comparison"] = {
	"filters": [
		{
			"fieldname":"product_bundle",
			"fieldtype":"Link",
			"label":"Product Bundle",
			"options":"Item",
			"get_query": () => {
				return {
					query : "kulkul_erp.kulkul_selling.report.product_bundle_price_comparison.product_bundle_price_comparison.get_bundle_items" 
				}
			},
			"reqd":1
		}
	]
};
