from erpnext.setup.utils import get_exchange_rate
import frappe

def update_so(doc,method):
	so = frappe.get_value("Sales Order",{"work_orders": doc.name},"name")
	if so:
		update_result_of_work(doc.name, so)

def update_sum(doc,method):
	total_order_c = 0
	for item in doc.order_items:
		order_er = False
		if (item.qty and item.rate) and (item.qty > 0 and item.rate > 0):
			item.amount = item.qty * item.rate
		else:
			item.amount = 0

		if item.amount or item.amount > 0:
			if item.currency != "IDR":
				if doc.exchange_rates and len(doc.exchange_rates) > 0:
					for er in doc.exchange_rates:
						if er.currency == item.currency:
							total_order_c += item.qty * (item.rate * er.rate)
							order_er = True
				elif doc.reserve_order and doc.reserve_order != '':
					if frappe.db.exists('Reserve Order', doc.reserve_order):
						ro = frappe.get_doc('Reserve Order', doc.reserve_order)
						if ro and ro.exchange_rates and len(ro.exchange_rates) > 0:
							for er_ro in ro.exchange_rates:
								if er_ro.currency == item.currency:
									total_order_c += item.qty * (item.rate * er_ro.rate)
									order_er = True
				elif order_er == False:
					rate = get_exchange_rate(item.currency,"IDR")
					total_order_c += item.qty * (item.rate * rate)
			else:
				total_order_c += item.amount

	doc.total_order_custome = total_order_c

	total_cost_c = 0
	for item in doc.order_cost:
		order_er = False
		if (item.qty and item.rate) and (item.qty > 0 and item.rate > 0):
			item.amount = item.qty * item.rate
		else:
			item.amount = 0

		if item.amount or item.amount > 0:
			if item.currency != "IDR":
				if doc.exchange_rates and len(doc.exchange_rates) > 0:
					for er in doc.exchange_rates:
						if er.currency == item.currency:
							total_cost_c += item.qty * (item.rate * er.rate)
							order_er = True
				elif doc.reserve_order and doc.reserve_order != '':
					if frappe.db.exists('Reserve Order', doc.reserve_order):
						ro = frappe.get_doc('Reserve Order', doc.reserve_order)
						if ro and ro.exchange_rates and len(ro.exchange_rates) > 0:
							for er_ro in ro.exchange_rates:
								if er_ro.currency == item.currency:
									total_cost_c += item.qty * (item.rate * er_ro.rate)
									order_er = True
				elif order_er == False:
					rate = get_exchange_rate(item.currency,"IDR")
					total_cost_c += item.qty * (item.rate * rate)
			else:
				total_cost_c += item.amount

	doc.total_cost_custome = total_cost_c

	doc.total_profit_custome = doc.total_order_custome - doc.total_cost_custome

def update_result_of_work(source_doc, target_doc):
	
	wo = frappe.get_doc("Project", source_doc)
	so = frappe.get_doc("Sales Order", target_doc)
	if so.docstatus != 2:
		so.result_of_work = []
		
		frappe.db.sql("DELETE FROM `tabResult of Work Item` where parent = '{}'".format(so.name))

		for item in wo.result_of_work_item:
			so.append("result_of_work",{
				"document_name": item.document_name,
				"type": item.type,
				"visa_type": item.visa_type,
				"legal_type": item.legal_type or '',
				"tka": item.tka,
				"issue_date": item.issue_date,
				"expired_date": item.expired_date,
				"result_document": item.result_document
			})

			frappe.db.set_value("Result Document", item.document_name, "work_orders", source_doc)
			frappe.db.set_value("Result Document", item.document_name, "work_order_detail", item.name)
		so.save(ignore_permissions=True)

def update_status_work_item(doc, method):
	if frappe.db.exists("Project",doc.name):
		wo = frappe.get_doc('Project', doc.name)
		for item in wo.result_of_work_item:
			if item.document_name:
				frappe.db.set_value("Result Document", item.document_name, "status", item.status)

			if item.downloadable:
				frappe.db.set_value("Result Document", item.document_name, "downloadable", "Yes" if item.downloadable else "No")

def delete_rd_deleted_work_items(doc, method):
	if frappe.db.exists("Project", doc.name):
		result_documents = frappe.get_all('Result Document', filters={'work_orders':doc.name}, fields=['name','work_order_detail'])
		if result_documents:
			for rd in result_documents:
				if not frappe.db.exists('Result of Work Item', rd.work_order_detail):
					frappe.db.sql("""DELETE FROM `tabResult Document` WHERE name = "{}" """.format(rd.name))

def change_status_validation(doc, method):
	if doc.status == 'Cancelled':
		sales_invoices = frappe.get_all('Sales Invoice', filters={'work_orders': doc.name}, fields=['name','docstatus'])
		if len(sales_invoices) > 0:
			for si in sales_invoices:
				if si.docstatus != 2:
					frappe.throw('There is a Sales Invoice that has been Created, Cancel or Delete it first!')

		sales_orders = frappe.get_all('Sales Order', filters={'work_orders': doc.name}, fields=['name','docstatus'])
		for so in sales_orders:
			frappe.db.sql(
				"""
					UPDATE `tabSales Order` SET status = "Cancelled", docstatus = 2 WHERE name = "{}"
				""".format(so.name)
			)

		frappe.db.commit()

		vouchers = frappe.get_all('Purchase Invoice', filters={'work_orders': doc.name}, fields=['name','docstatus'])
		if len(vouchers) > 0:
			for voc in vouchers:
				if voc.docstatus != 2:
					frappe.throw('There is a Voucher that has been Created, Cancel or Delete it first!')
		
		purchase_orders = frappe.get_all('Purchase Order', filters={'work_orders': doc.name}, fields=['name','docstatus'])
		for po in purchase_orders:
			frappe.db.sql(
				"""
					UPDATE `tabPurchase Order` SET status = "Cancelled", docstatus = 2 WHERE name = "{}"
				""".format(po.name)
			)
			
		frappe.db.commit()

@frappe.whitelist()
def create_result_document(row_name,row_status,row_type,row_visa_type,row_legal_type,row_rptka,row_no_rptka,row_tka,row_issue_date,row_expired_date,row_result_document,wo_name):
	doc = frappe.new_doc("Result Document")
	doc.work_order_detail = row_name
	doc.status = row_status
	doc.type = row_type

	doc.visa_type = row_visa_type
	doc.jenis_legal = row_legal_type

	doc.rptka = row_rptka
	doc.no_rptka = row_no_rptka
	doc.tka = row_tka
	doc.issue_date = row_issue_date
	doc.expired_date = row_expired_date
	doc.result_document = row_result_document
	doc.work_orders = wo_name

	wo = frappe.get_value("Project", wo_name, "customer")
	
	if wo:
		doc.wo_company = wo
		if row_visa_type == 'RPTKA':
			doc.customer = wo

	doc.save(ignore_permissions=True)

	row = frappe.get_doc("Result of Work Item",row_name)
	row.db_set("document_name", doc.name)
	return doc
	# return {
	# 	"row_name": row_name,
	# 	"row_status": row_status,
	# 	"row_type": row_type,
	# 	"row_visa_type": row_visa_type,
	# 	"row_rptka": row_rptka,
	# 	"row_tka": row_tka,
	# 	"row_issue_date": row_issue_date,
	# 	"row_expired_date": row_expired_date,
	# 	"row_result_document": row_result_document,
	# 	"wo_name" : wo_name
	# }