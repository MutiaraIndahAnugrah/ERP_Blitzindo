# Copyright (c) 2022, Kulkul and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document

class ModifyDocument(Document):
	pass

@frappe.whitelist()
def execute_docs(action, ids, doctype_target):
	arr_ids = json.loads(ids)
	if not action:
		frappe.throw('Empty Action!')

	if not doctype_target:
		frappe.throw('Empty Doctype!')

	if doctype_target == 'Work Orders':
		doctype_target = 'Project' 

	if doctype_target == 'Voucher':
		doctype_target = 'Purchase Invoice' 

	if len(arr_ids) > 0:
		if action == 'Cancel':
			for id_doc in arr_ids:
				if not id_doc or id_doc == '':
					frappe.throw('Invalid ID Document!')

				if frappe.db.exists('Workflow', {'document_type' : doctype_target, 'is_active' : 1}):
					workflow_doctype = frappe.get_last_doc('Workflow', filters={'document_type' : doctype_target, 'is_active' : 1})
					workflow_doctype_state = frappe.get_last_doc('Workflow Document State', filters={'parent' : workflow_doctype.name, 'doc_status' : '2'}, order_by="idx desc")
					if workflow_doctype_state and workflow_doctype_state.state:
						frappe.db.sql(
							"""
							UPDATE `tab{}` SET docstatus = 2, workflow_state = "{}" where `name` = "{}"
							
							""".format(doctype_target, workflow_doctype_state.state, id_doc)
						)
						frappe.db.commit()
					else:
						frappe.throw('Doctype {} don\'t have Workflow state Cancelled or Doc Status = 2!'.format(doctype_target))

				else:
					frappe.throw('Doctype {} don\'t have Workflow state Cancelled or Doc Status = 2!'.format(doctype_target))

		elif action == 'Delete':
			for id_doc in arr_ids:
				if not id_doc or id_doc == '':
					frappe.throw('Invalid ID Document!')

				frappe.db.delete(doctype_target, {
					"name" : id_doc
				})
				frappe.db.commit()
		else:
			frappe.throw('Error Action!')

		if doctype_target == 'Purchase Invoice' or doctype_target == 'Voucher':
			frappe.db.sql(
				"""
				DELETE from `tabGL Entry` where name IN (
					SELECT gle.name 
					FROM `tabGL Entry` gle
					left join `tabPurchase Invoice` si on si.name = gle.voucher_no
					where si.name is null
					and (gle.voucher_type = "Voucher" or gle.voucher_type = "Purchase Invoice")
				)
				"""
			)
			frappe.db.commit()

		if doctype_target == 'Sales Invoice':
			frappe.db.sql(
				"""
				DELETE from `tabGL Entry` where name IN (
					SELECT gle.name FROM `tabGL Entry` gle left join `tabSales Invoice` si on si.name = gle.voucher_no
					where si.name is null
					and (gle.voucher_type = "Sales Invoice")
				)
				"""
			)
			frappe.db.commit()

	else:
		frappe.throw('Empty ID Document!')

	return True
