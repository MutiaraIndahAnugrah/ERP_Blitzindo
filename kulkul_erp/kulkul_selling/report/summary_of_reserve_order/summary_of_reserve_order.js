// Copyright (c) 2022, Kulkul and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Summary of Reserve Order"] = {
	"filters": [
		// {
		// 	"fieldname":"period",
		// 	"label": __("Period"),
		// 	"fieldtype": "Select",
		// 	"options": [
		// 		{ "value": "Monthly", "label": __("Monthly") },
		// 		{ "value": "Quarterly", "label": __("Quarterly") },
		// 		{ "value": "Half-Yearly", "label": __("Half-Yearly") },
		// 		{ "value": "Yearly", "label": __("Yearly") }
		// 	],
		// 	"default": "Monthly"
		// },
		{
			"fieldname":"group_by",
			"label": __("Group By"),
			"fieldtype": "Select",
			"options": [
				{ "value": "Customer", "label": __("Customer") },
				{ "value": "PIC", "label": __("PIC") },
				{ "value": "Workflow_state", "label": __("Status") },
				{ "value": "Item", "label": __("Item") },
			],
			"default": "customer",
			"reqd":1
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"default": frappe.datetime.month_start(),
			"reqd":1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"default": frappe.datetime.month_end(),
			"reqd":1
		}
		// {
		// 	"fieldname":"based_on",
		// 	"label": __("Based On"),
		// 	"fieldtype": "Select",
		// 	"options": [
		// 		{ "value": "Item", "label": __("Item") },
		// 		{ "value": "Item Group", "label": __("Item Group") },
		// 		{ "value": "Customer", "label": __("Customer") },
		// 		{ "value": "Customer Group", "label": __("Customer Group") },
		// 		{ "value": "Territory", "label": __("Territory") },
		// 		{ "value": "Project", "label": __("Project") }
		// 	],
		// 	"default": "Item",
		// 	"dashboard_config": {
		// 		"read_only": 0
		// 	}
		// }
	]
};
