import frappe

def update_profit_loss_wo(doc,method):
	ref_list = ["Sales Paid","Cost Paid"]
	ref_type = ""
	work_orders = ""
	amount = 0
	cur = ""
	
	if doc.doctype == "Payment Entry":
		for ref in doc.references:
			if ref.reference_doctype == "Purchase Invoice":
				ref_type = "Cost Paid"
				pinv = frappe.get_doc(ref.reference_doctype,ref.reference_name)
				work_orders = pinv.work_orders


			if ref.reference_doctype == "Sales Invoice":
				ref_type = "Sales Paid"
				sinv = frappe.get_doc(ref.reference_doctype,ref.reference_name)
				work_orders = sinv.work_orders

			cur = doc.paid_from_account_currency
			amount = ref.allocated_amount
	else:
		work_orders = doc.work_orders
		amount = doc.grand_total
		cur = doc.currency

	if work_orders != "" and frappe.db.exists("Project", work_orders):
		wo = frappe.get_doc("Project", work_orders)
		
		if doc.doctype == "Sales Invoice":
			ref_type = "Sales Invoiced"

		if doc.doctype == "Purchase Invoice":
			ref_type = "Cost Invoiced"
		
		update_done = False

		for row in wo.sales_and_costs:
			if row.currency == cur and row.type == ref_type:
				if method == "on_submit":
					row.amount += amount
				if method == "on_cancel":
					row.amount -= amount
				update_done = True

		if not update_done:
			if method == "on_submit":
				wo.append("sales_and_costs",{
					"currency": cur,
					"type": ref_type,
					"amount": amount
				})
			if method == "on_cancel":
				wo.append("sales_and_costs",{
					"currency": cur,
					"type": ref_type,
					"amount": 0
				})

		if wo.status == 'Cancelled':
			frappe.throw("There is a Work Orders {} that has been Cancelled, please check it first!".format(work_orders))

		wo.save()