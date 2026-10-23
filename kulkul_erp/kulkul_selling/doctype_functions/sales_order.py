import frappe

def custom_prefix(doc,method):
	pass

def change_status_validation(doc, method):
	pass
	# if doc.status == 'Cancelled':
	# 	sales_invoices = frappe.get_all('Sales Invoice', filters={'work_orders': doc.name}, fields=['name','docstatus'])
	# 	for si in sales_invoices:
	# 		if si.docstatus == 1:
	# 			frappe.throw('There is a Sales Invoice that has been Submitted, Cancel it first!')