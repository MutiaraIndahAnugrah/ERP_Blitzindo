import frappe
from erpnext.setup.utils import get_exchange_rate
import json
import pandas as pd

def patch_gl():
	# list_sinv = frappe.db.sql("""
	# 		select
	# 		sinv.name, count(gle.name) `gls`
	# 		from `tabSales Invoice` sinv
	# 		left join `tabGL Entry` gle on gle.voucher_no = sinv.name
	# 		where sinv.docstatus = 1
	# 		group by sinv.name
	# 		having `gls` = 0
	# 	""", as_dict=1)
	list_sinv = ["VOC-VIS-0622-0015",
				"VOC-VIS-0622-0016",
				"VOC-VIS-0622-0017",
				"VOC-VIS-0622-0018",
				"VOC-VIS-0622-0019",
				"VOC-VIS-0622-0020",
				"VOC-VIS-0622-0021",
				"VOC-VIS-0622-0022",
				"VOC-VIS-0622-0023",
				"VOC-VIS-0622-0024",
				"VOC-VIS-0622-0025",
				"VOC-VIS-0622-0026",
				"VOC-VIS-0622-0027",
				"VOC-VIS-0622-0028",
				"VOC-VIS-0622-0028",
				"VOC-VIS-0622-0029",
				"VOC-VIS-0622-0031",
				"VOC-VIS-0622-0032",
				"VOC-VIS-0622-0033",
				"VOC-VIS-0622-0034",
				"VOC-VIS-0722-0006",
				"VOC-VIS-0722-0010",
				"VOC-VIS-0722-0012"]

	for row in list_sinv:
		# doc = frappe.get_doc("Sales Invoice", row.name)
		frappe.db.sql("DELETE FROM `tabGL Entry` where voucher_no = '{}'".format(row))
		doc = frappe.get_doc("Purchase Invoice", row)
		doc.make_gl_entries()
		frappe.db.commit()

def update_sinv():

	for row in frappe.get_all("Sales Invoice",{"remarks":"Update tax Juni","taxes_and_charges":["!=",""]}):
		doc = frappe.get_doc("Sales Invoice",row.name)
		doc.payment_schedule = []
		doc.set_missing_values()
		try:
			doc.save()
		except Exception as e:
			print(e)

def fix_account_pe():
	no_acc = []
	for row in no_acc:
	
		frappe.db.sql("""
			UPDATE `tabPayment Entry` set _user_tags = "Closing 2021" where name = "{}"
		""".format(row))

		# frappe.db.sql("""
		# 		DELETE FROM `tabGL Entry` where voucher_no = "{}"
		# 	""".format(row))

		# frappe.get_doc("Payment Entry",row).make_gl_entries()
		frappe.db.commit()