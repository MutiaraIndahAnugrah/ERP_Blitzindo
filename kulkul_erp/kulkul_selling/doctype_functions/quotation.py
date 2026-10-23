import frappe
from frappe import _
from frappe.desk.form.load import get_attachments
from frappe.model.mapper import get_mapped_doc
import json
from erpnext.setup.utils import get_exchange_rate

# def send_default_pricelist(doc,method):
# 	if doc.send_default_pricelist == 1:

# 		email_id = frappe.get_value(doc.quotation_to,doc.party_name,"email_id")
# 		if not email_id:
# 			frappe.throw("Make sure party have email_id.")

# 		attachments = [{"fid":d.name} for d in frappe.get_all("File", fields=["name"],
# 		filters = {"file_url": frappe.db.get_single_value("ERP Settings","default_pricelist_path")})]

# 		frappe.sendmail(
# 			recipients=email_id,
# 			subject=_("Quotation Blitzindo {}").format(doc.name),
# 			message="Please check on attachment our pricelist",
# 			reference_doctype = doc.doctype,
# 			reference_name = doc.name,
# 			attachments=attachments
# 		)

@frappe.whitelist()
def create_order_form(source_name,target_doc=None):
	def set_missing_values(source,target):
		pass
		# target.run_method("set_missing_values")
		# target.run_method("calculate_taxes_and_totals")
		
	def update_item(source, target, source_parent):
		pass
		# target.item_name = frappe.get_value("Item",target.item_code,"item_name")
		# bundle_pricelist = frappe.db.get_single_value("ERP Settings","bundle_pricelist")
		# target.rate = frappe.get_value("Item Price",{"price_list":bundle_pricelist, "item_code":target.item_code, "selling":1},"price_list_rate")

	doclist = get_mapped_doc("Quotation", source_name, {
		"Quotation": {
			"doctype": "Order Form",
			"field_map": {
				"party_name": "customer",
				"customer_name":"customer_name",
				"name": "from_quotation",
				"selling_price_list":"default_price_list",
				"currency":"default_currency"
				# "lead_owner":"account_manager"
			}
		},
		"Quotation Item": {
			"doctype" : "Order Form Items",
			"field_map": {
				"item_code": "item_code",
				"item_name": "item_name",
				"description": "description",
				"qty": "qty",
				"rate": "rate",
				"amount": "amount",
				"uom": "uom",
				"site":"site"
			},
			"postprocess":update_item
		}
	}, target_doc, set_missing_values)

	for item in doclist.items:
		item.currency = doclist.default_currency
		item.price_list = doclist.default_price_list

	doclist.account_manager = frappe.get_value("Customer", doclist.customer, "lead_owner")

	doclist.save(ignore_permissions=True)

	return doclist	

@frappe.whitelist()
def get_product_bundle(source_name, target_doc=None):
	
	def set_missing_values(source,target):
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")
		
	def update_item(source, target, source_parent):
		target.item_name = frappe.get_value("Item",target.item_code,"item_name")
		bundle_pricelist = frappe.db.get_single_value("ERP Settings","bundle_pricelist")
		target.rate = frappe.get_value("Item Price",{"price_list":bundle_pricelist, "item_code":target.item_code, "selling":1},"price_list_rate")

	doclist = get_mapped_doc("Product Bundle", source_name, {
		"Product Bundle": {
			"doctype": "Quotation",
			"field_map": {
				
			}
		},
		"Product Bundle Item": {
			"doctype" : "Quotation Item",
			"field_map": {
				"item_code": "item_code",
				"description": "description",
				"qty": "qty",
				"uom": "uom"
			},
			"postprocess":update_item
		}
	}, target_doc, set_missing_values)

	item_row_one = frappe.get_doc('Item', doclist.items[0].item_code)
	pl_row_one = frappe.get_doc('Price List', item_row_one.item_defaults[0].default_price_list)
	# frappe.msgprint(frappe.as_json((pl_row_one.currency)))
		
	if pl_row_one.currency:
		doclist.currency = pl_row_one.currency
		if pl_row_one.currency != 'IDR':
			rate = get_exchange_rate(pl_row_one.currency, "IDR")
			doclist.conversion_rate = rate
			doclist.price_list_currency = pl_row_one.currency
			doclist.plc_conversion_rate = rate
		else:
			doclist.conversion_rate = 1
			doclist.price_list_currency = 'IDR'
			doclist.plc_conversion_rate = 1

	if item_row_one.item_defaults[0].default_price_list:
		doclist.selling_price_list = item_row_one.item_defaults[0].default_price_list

	for item in doclist.items:
		price_list_rate = frappe.get_value('Item Price', {'currency' : doclist.currency, 'item_code' : item.item_code, "selling":1}, 'price_list_rate')
		item.price_list_rate = price_list_rate
		item.rate = price_list_rate
		item.amount = price_list_rate or 0 * item.qty
		if doclist.currency != 'IDR':
			item.base_price_list_rate = price_list_rate * get_exchange_rate(doclist.currency, "IDR")

	return doclist

def custom_submit(doc,method):
	if len(doc.items) == 0:
		frappe.throw("Item required before submit Quotation")
	else:
		for item in doc.items:
			if not item.rate or item.rate == 0:
				frappe.throw('Please add item price at row #{}'.format(item.idx))

def validate_item_price(doc,method):
	if doc.workflow_state == 'Submitted for Approval':
		if len(doc.items) > 0:
			for item in doc.items:
				if not item.rate or item.rate == 0:
					frappe.throw('Please add item price at row #{}'.format(item.idx))
		else:
			frappe.throw("Item required before submit Quotation")
