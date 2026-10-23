import frappe
import json
from frappe.utils import nowdate, getdate, add_days
from frappe.model.mapper import get_mapped_doc

def validate_multi_currency(doc,method):
	if doc.currency != doc.price_list_currency:
		frappe.throw("Multi Currency Transaction against Price List")

def update_wo_detail(doc,method):
	# Amended checking if work order detail is exist then check if PO already created
	if doc.work_order_cost_detail and doc.work_orders:
		po_exist = frappe.db.get_value("Order Cost",doc.work_order_cost_detail,"purchase_order")
		if po_exist:
			frappe.throw("PO already created.")
		else:

		# Note by : Aan
		# Saya hilangkan karena PO jadi tidak bisa di submit, walau po itu baru pertama disubmit
			frappe.db.set_value("Order Cost",doc.work_order_cost_detail,"purchase_order",doc.name)
# frappe.datetime.add_days(nowdate(), 1)

def replace_naming(doc,method):
	if doc.voucher_type == 'Legal':
		doc.naming_series = 'PO-LEG-.MM.YY.-.####'
	elif doc.voucher_type == 'Visa':
		doc.naming_series = 'PO-VIS-.MM.YY.-.####'
	else:
		doc.naming_series = 'PO-INT-.MM.YY.-.####'

@frappe.whitelist()
def create_all_po(order_cost_param, order_type_param):
	order_cost = json.loads(order_cost_param)
	# frappe.msgprint(frappe.as_json(order_cost))
	# frappe.msgprint(order_type_param)
	# frappe.throw(nowdate())
	arr_results = []
	for oc in order_cost:
		# frappe.msgprint(oc['supplier'])


		supplier = oc['supplier']
		row_type = oc['type']

		order_type = order_type_param

		po = frappe.new_doc("Purchase Order")
		po.supplier = supplier
		po.voucher_type = row_type

		po.customer = frappe.get_value('Project', oc['parent'], 'customer')

		po.supplier_name = frappe.get_value("Supplier",supplier, "supplier_name")

		po.transaction_date = nowdate()
		po.schedule_date = add_days(nowdate(), 1)
		po.work_orders = oc['parent']
		po.work_order_cost_detail = oc['name']
		ord_c = frappe.get_doc("Order Cost",oc['name'])

		detail_order = frappe.get_doc("Detail Order", ord_c.detail_order)
		po.currency = ord_c.currency
		po.buying_price_list = ord_c.price_list
		total = 0
		if ord_c.price_list:
			price_list_rate = frappe.get_value("Item Price",{"price_list":ord_c.price_list, "item_code":ord_c.item_code, "buying":1},"price_list_rate") or 0
		else:
			price_list_rate = 0
			
		if detail_order.type == 'Visa':
			for detail in detail_order.details:
				if detail.data_tka:
					tka_data = detail.data_tka
					tka_no_passport = frappe.get_value("Tenaga Kerja", detail.data_tka,"no_passport")
					tka_description = detail.data_tka + "-" + frappe.get_value("Tenaga Kerja", detail.data_tka,"full_name")
					tka_foreign_name = frappe.get_value("Tenaga Kerja", detail.data_tka,"nama_asing")
				else:
					tka_data = None
					tka_no_passport = None
					tka_description = None
					tka_foreign_name = None

				po.append("items",{
						"item_code": ord_c.item_code,
						"item_name": ord_c.item_name,
						"schedule_date": add_days(nowdate(), 1),
						"qty": 1,
						"uom": frappe.get_value("Item", ord_c.item_code, "stock_uom"),
						"stock_uom": frappe.get_value("Item", ord_c.item_code, "stock_uom"),
						"rate": ord_c.rate,
						"price_list_rate": ord_c.rate,
						"amount": ord_c.rate * 1,
						"tka": tka_data,
						"no_passport": tka_no_passport,
						"description": tka_description or 'Visa Item ' + ord_c.item_name,
						"foreign_name": tka_foreign_name
					})

		else:
			po.append("items",{
						"item_code": ord_c.item_code,
						"item_name": ord_c.item_name,
						"schedule_date": add_days(nowdate(), 1),
						"qty": ord_c.qty,
						"uom": frappe.get_value("Item", ord_c.item_code, "stock_uom"),
						"stock_uom": frappe.get_value("Item", ord_c.item_code, "stock_uom"),
						"rate": ord_c.rate,
						"price_list_rate": ord_c.rate,
						"description": 'Legal Item ' + ord_c.item_name,
						"amount": ord_c.rate * ord_c.qty
					})

		po.save()
		po.submit()

		arr_results.append({'po_name':po.name,'row_name':oc['name'], 'po':po})
		# frappe.msgprint('Success create Purchase Order for Item ' + ord_c.item_code)

	return arr_results

@frappe.whitelist()
def create_po(source_name, target_name=None):
	_args = frappe._dict(frappe.flags.args)
	supplier = _args.supplier
	order_type = _args.order_type
	row_type = _args.row_type

	po = frappe.new_doc("Purchase Order")
	po.supplier = supplier
	po.voucher_type = row_type

	po.customer = frappe.get_value('Project', source_name, 'customer')

	po.supplier_name = frappe.get_value("Supplier",supplier, "supplier_name")
	po.transaction_date = nowdate()
	po.work_orders = source_name
	po.work_order_cost_detail = _args.row_name
	oc = frappe.get_doc("Order Cost",_args.row_name)

	detail_order = frappe.get_doc("Detail Order", oc.detail_order)
	po.currency = oc.currency
	po.buying_price_list = oc.price_list

	if oc.price_list:
		price_list_rate = frappe.get_value("Item Price",{"price_list":oc.price_list, "item_code":oc.item_code, "buying":1},"price_list_rate") or 0
	else:
		price_list_rate = 0

	if detail_order.type == 'Visa':
		for detail in detail_order.details:
			if detail.data_tka:
				tka_data = detail.data_tka
				tka_no_passport = frappe.get_value("Tenaga Kerja", detail.data_tka,"no_passport")
				tka_description = detail.data_tka + "-" + frappe.get_value("Tenaga Kerja", detail.data_tka,"full_name")
				tka_foreign_name = frappe.get_value("Tenaga Kerja", detail.data_tka,"nama_asing")
			else:
				tka_data = None
				tka_no_passport = None
				tka_description = None
				tka_foreign_name = None

			po.append("items",{
					"item_code": oc.item_code,
					"item_name": oc.item_name,
					"qty": 1,
					"uom": frappe.get_value("Item", oc.item_code, "stock_uom"),
					"stock_uom": frappe.get_value("Item", oc.item_code, "stock_uom"),
					"rate": oc.rate,
					"price_list_rate": oc.rate,
					"amount": oc.rate * 1,
					"tka": tka_data,
					"no_passport": tka_no_passport,
					"description": tka_description,
					"foreign_name": tka_foreign_name
				})
	else:
		po.append("items",{
				"item_code": oc.item_code,
				"item_name": oc.item_name,
				"schedule_date": add_days(nowdate(), 1),
				"qty": oc.qty,
				"uom": frappe.get_value("Item", oc.item_code, "stock_uom"),
				"stock_uom": frappe.get_value("Item", oc.item_code, "stock_uom"),
				"rate": oc.rate,
				"price_list_rate": oc.rate,
				"description": 'Legal Item ' + oc.item_name,
				"amount": oc.rate * oc.qty
			})

	return po

@frappe.whitelist()
def get_items_from_wo(source_name,target_doc=None):
	def set_missing_values(source,target):
		target.work_order_cost_detail = source_name
		# target.run_method("set_missing_values")
		# target.run_method("calculate_taxes_and_totals")
		
	def update_item(source, target, source_parent):
		
		target.item_name = frappe.get_value("Item",target.item_code,"item_name")
		target.uom = frappe.get_value("Item",target.item_code,"stock_uom")
		target.description = frappe.get_value("Item",target.item_code,"description")
		target.stock_uom = frappe.get_value("Item",target.item_code,"stock_uom")
		target.conversion_factor = 1
		target.stock_qty = source.qty
		# target.rate = frappe.get_value("Item Price",{"price_list":bundle_pricelist, "item_code":target.item_code, "selling":1},"price_list_rate")

	doclist = get_mapped_doc("Project", source_name, {
		"Project": {
			"doctype": "Purchase Order",
			"field_map": {
				"name": "work_orders",
				"order_type": "order_type",
				"supplier":"supplier"
			}
		},
		"Order Cost": {
			"doctype" : "Purchase Order Item",
			"field_map": {
				"item_code": "item_code",
				"item_name": "item_name",
				"description": "description",
				"qty": "qty",
				"rate": "rate",
				"amount": "amount",
				"uom": "uom"
			},
			"postprocess":update_item
		}
	}, target_doc, set_missing_values)

	return doclist