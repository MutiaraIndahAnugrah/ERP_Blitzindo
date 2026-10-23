from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "kulkul_erp"
app_title = "Kulkul Erp"
app_publisher = "Kulkul"
app_description = "Kulkul ERP Custom"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "Kulkul"
app_license = "MIT"
# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/kulkul_erp/css/custom.css"
# app_include_js = "/assets/kulkul_erp/js/kulkul_erp.js"

# include js, css files in header of web template
web_include_css = "/assets/css/kulkul_erp-web.css"
web_include_js = "/assets/js/kulkul_erp-web.js"
website_context = {
	"favicon": "/assets/kulkul_erp/costume/images/favicon.png",
	"splash_image": "/assets/kulkul_erp/costume/images/logo-only.png"
}
# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kulkul_erp/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Quotation" : "public/js/quotation.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "kulkul_erp.install.before_install"
# after_install = "kulkul_erp.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "kulkul_erp.uninstall.before_uninstall"
# after_uninstall = "kulkul_erp.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kulkul_erp.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	},

	# "File": {
		# "after_insert": "kulkul_erp.kulkul_erp.custom_file.backup_attachment",
	# },
	"User": {
		"after_insert": "kulkul_erp.kulkul_selling.doctype_functions.document_owner.sync_record",
		"after_rename": "kulkul_erp.kulkul_selling.doctype_functions.document_owner.rename_document_owner"
	},
	"Quotation": {
		"on_submit": "kulkul_erp.kulkul_selling.doctype_functions.quotation.custom_submit",
		"validate": "kulkul_erp.kulkul_selling.doctype_functions.quotation.validate_item_price"
	},
	"Testimonial Website": {
		# "autoname": "kulkul_erp.kulkul_website.doctype.testimonial_website.testimonial_website.replace_naming" 
	},
	"Project":{
		"validate": [
			"kulkul_erp.kulkul_selling.doctype_functions.work_orders.update_so",
			"kulkul_erp.kulkul_selling.doctype_functions.work_orders.update_sum",
			"kulkul_erp.kulkul_selling.doctype_functions.work_orders.update_status_work_item",
			"kulkul_erp.kulkul_selling.doctype_functions.work_orders.change_status_validation"
		],
		"on_update": [
			"kulkul_erp.kulkul_selling.doctype_functions.work_orders.delete_rd_deleted_work_items"
		]
	},
	"Purchase Order":{
		"validate": ["kulkul_erp.kulkul_selling.doctype_functions.purchase_order.validate_multi_currency"],
		"before_insert":"kulkul_erp.kulkul_selling.doctype_functions.purchase_order.update_wo_detail",
		"autoname": "kulkul_erp.kulkul_selling.doctype_functions.purchase_order.replace_naming" 
	},
	"Purchase Invoice":{
		"validate": [
			# "kulkul_erp.kulkul_selling.doctype_functions.purchase_order.validate_multi_currency",
			"kulkul_erp.kulkul_selling.doctype_functions.purchase_invoice.check"
		],
		"before_insert": "kulkul_erp.kulkul_selling.doctype_functions.purchase_invoice.update_current_series_before_insert",
		"on_submit": "kulkul_erp.kulkul_selling.doctype_functions.profit_loss.update_profit_loss_wo",
		"on_cancel": [
			"kulkul_erp.kulkul_selling.doctype_functions.profit_loss.update_profit_loss_wo",
			"kulkul_erp.kulkul_selling.doctype_functions.purchase_invoice.update_workflow_state"
		]
	},
	"Sales Invoice": {
		"before_insert": "kulkul_erp.kulkul_selling.doctype_functions.sales_invoice.update_current_series_before_insert",
		"on_submit": [
			"kulkul_erp.kulkul_selling.doctype_functions.profit_loss.update_profit_loss_wo",
			"kulkul_erp.kulkul_selling.doctype_functions.sales_invoice.check_draft"
		],
		"on_cancel": "kulkul_erp.kulkul_selling.doctype_functions.profit_loss.update_profit_loss_wo",
		"on_update_after_submit" : "kulkul_erp.kulkul_selling.doctype_functions.sales_invoice.update_gl_entries"
	},
	"Sales Order": {
		"validate": "kulkul_erp.kulkul_selling.doctype_functions.sales_order.change_status_validation"
	},
	"Payment Entry": {
		"before_insert": "kulkul_erp.kulkul_selling.doctype_functions.payment_entry.update_current_series_before_insert",
		"on_submit": ["kulkul_erp.kulkul_selling.doctype_functions.profit_loss.update_profit_loss_wo"],
		"on_cancel": "kulkul_erp.kulkul_selling.doctype_functions.profit_loss.update_profit_loss_wo"
	},
	"Journal Entry": {
		"before_insert": "kulkul_erp.kulkul_selling.doctype_functions.journal_entry.update_current_series_before_insert"
	}

}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"kulkul_erp.tasks.all"
# 	],
	# "daily": [
		# "kulkul_erp.kulkul_erp.custom_file.backup_attachments"
	# ],
# 	"hourly": [
# 		"kulkul_erp.tasks.hourly"
# 	],
# 	"weekly": [
# 		"kulkul_erp.tasks.weekly"
# 	]
# 	"monthly": [
# 		"kulkul_erp.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "kulkul_erp.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "kulkul_erp.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "kulkul_erp.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"kulkul_erp.auth.validate"
# ]

