# Copyright (c) 2022, Kulkul and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document

class DetailOrder(Document):
	pass

	def before_submit(self):
		rowCount = len(self.details)
		if rowCount != self.qty and self.type == 'Visa':
			frappe.throw('Item Quantity and Detail Order Quantity do not match')

		if rowCount > 0 and self.type == 'Visa':
			for item in self.details:
				if not item.data_tka or item.data_tka == '':
					frappe.throw('You have item detail with empty TKA!')

	def validate(self):
		# pass
		if len(self.details) > 0 and self.type == 'Visa':
			for d in self.details:
				if d.data_tka:
					tka = frappe.get_doc('Tenaga Kerja', d.data_tka)
					if self.order_category_hidden == 'Sponsor':
						tka.sponsor_company = self.sponsor_company_hidden
					else:
						tka.sponsor_company = ''
					tka.save()


		if self.workflow_state == 'Submitted':
			rowCount = len(self.details)
			if rowCount != self.qty and self.type == 'Visa':
				frappe.throw('Item Quantity and Detail Order Quantity do not match')
		
	

@frappe.whitelist()
def create_detail_order(item_code, item_name, order_type, qty,rate,amount, customer, customer_name, row_name, parent_name, doc_type, order_category = None, sponsor_company = None, site = None):

	doc = frappe.new_doc("Detail Order")
	doc.customer = customer
	doc.customer_name = customer_name
	doc.item_code = item_code
	doc.item_name = item_name
	doc.type = order_type
	doc.qty = qty
	doc.rate = rate
	doc.amount = amount
	doc.order_form_item = row_name
	doc.order_category_hidden = order_category or ''
	doc.sponsor_company_hidden = sponsor_company or ''
	# doc.reserve_order = parent_name
	if site :
		doc.order_site_hidden = site

	if(doc_type == 'Reserve Order'):
		if frappe.db.exists("Reserve Order", parent_name):
			doc.reserve_order = parent_name
	else:
		if frappe.db.exists("Order Form", parent_name):
			doc.order_form = parent_name

	doc.currency = frappe.get_value('Order Form Items', row_name, 'currency')
	
	doc.save(ignore_permissions=True)

	row = frappe.get_doc("Order Form Items",row_name)
	row.db_set("detail_order", doc.name)

	# frappe.db.set_value("Order Form Items",row_name,"detail_order",doc.name)

	return doc

@frappe.whitelist()
def create_tenaga_kerja(fields, company, sponsor_company, row_name):
	field = json.loads(fields)

	doc = frappe.new_doc("Tenaga Kerja")
	doc.full_name = field['full_name']
	doc.foreign_name = field['foreign_name']
	doc.company = company
	doc.sponsor_company = sponsor_company
	doc.no_passport = field['no_passport']
	doc.passport_expired_date = field['passport_expired_date']
	doc.document_passport = field['document_passport']
	doc.document_vaccine = field['document_vaccine']
	doc.kewarganegaraan = field['kewarganegaraan']
	doc.notes = field['notes']
	doc.residential_address = field['residential_address']
	doc.tanggal_lahir = field['tanggal_lahir']
	doc.passport_expired_status = 'Expired less than 18 months' if field['passport_expired_status'] == 1 else ''
	doc.save(ignore_permissions=True)

	row = frappe.get_doc("Detail Order Items",row_name)
	row.db_set("data_tka", doc.name)

	return doc