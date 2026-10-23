# Copyright (c) 2022, Kulkul and contributors
# For license information, please see license.txt

from dataclasses import fields
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import add_days, flt, nowdate
from erpnext.setup.utils import get_exchange_rate



class ReserveOrder(Document):
	def validate(self):
		if len(self.items) > 0:
			for item in self.items:
				if item.detail_order:
					do = frappe.get_doc('Detail Order', item.detail_order)
					do.type = item.type
					if do.qty != len(do.details) and do.type == 'Visa' and self.workflow_state == 'Approved by Sales Supervisor / Manager':
						frappe.throw("Quantity and Detail Order Quantity do not match for Detail Order Item {}".format(item.item_code))

		self.profit_loss = []
		self.validate_prices()
		self.generate_exchange_rates()
		self.calculate_profit()

	def on_update(self):
		for item in self.items:
			if item.detail_order:
				if frappe.db.exists('Detail Order', item.detail_order):
					do = frappe.get_doc('Detail Order', item.detail_order)
					if do.docstatus == 0:
						do.order_form_item = item.name
						do.item_code = item.item_code
						do.item_name = item.item_name
						do.qty = item.qty
						do.type = item.type
						do.rate = item.rate
						do.amount = item.qty * item.rate
						do.save()
		if self.workflow_state == 'Rejected':
			self.action_on_cancel_and_rejected()

	def generate_exchange_rates(self):
		if len(self.exchange_rates) == 0:
			
			list_of_currency = list(set(d.currency for d in self.items))
			list_of_currency.extend(list(set(d.currency for d in self.order_cost)))

			list_of_currency = set(list_of_currency)

			for cur in list_of_currency:
				if cur != "IDR":
					rate = get_exchange_rate(cur,"IDR")
					self.append("exchange_rates",{"currency":cur,"rate":rate})					

	def calculate_profit(self):
		list_of_currency = list(set(d.currency for d in self.items))
		list_of_currency.extend(list(set(d.currency for d in self.order_cost)))

		list_of_currency = set(list_of_currency)

		self.profit_loss = []
		for cur in list_of_currency:
			amount = 0
			
			for item in self.items:
				if item.currency == cur:
					amount += item.amount

			self.append("profit_loss",{
					"currency": cur,
					"type": "Sales",
					"amount": amount
				})

			cost = 0
			for item in self.order_cost:
				if item.currency == cur:
					cost += item.amount

			self.append("profit_loss",{
					"currency":cur,
					"type": "Cost",
					"amount": cost
				})

			self.append("profit_loss",{
					"currency":cur,
					"type": "Margin",
					"amount": amount - cost
				})

		total_order_val = 0
		total_cost_val = 0
		profit_val = 0
		for row in self.profit_loss:
			if row.type == "Sales":
				ex_rate = 1
				if row.currency != "IDR":
					for ex_row in self.exchange_rates:
						if ex_row.currency == row.currency:
							ex_rate = float(ex_row.rate) if ex_row.rate else 0

				# frappe.throw("{} | {} | {}".format(ex_rate,row.amount,self.total_order))
				# self.total_order += float(row.amount) * (ex_rate if ex_rate else 1)
				total_order_val += row.amount * ex_rate

			if row.type == "Cost":
				ex_rate = 1
				if row.currency != "IDR":
					for ex_row in self.exchange_rates:
						if ex_row.currency == row.currency:
							ex_rate = float(ex_row.rate) if ex_row.rate else 0
	
				total_cost_val += row.amount * ex_rate

			if row.type == "Margin":
				ex_rate = 1
				if row.currency != "IDR":
					for ex_row in self.exchange_rates:
						if ex_row.currency == row.currency:
							ex_rate = float(ex_row.rate) if ex_row.rate else 0

				profit_val += row.amount * ex_rate	

		self.total_order = total_order_val
		self.total_cost = total_cost_val
		self.profit = profit_val
				

	def before_submit(self):
		list_of_currency = set(d.currency for d in self.profit_loss)
		# for cur in list_of_currency:
		# 	cost = 0

		# 	for row in self.profit_loss:
		# 		if row.type == "Cost" and row.currency == cur:
		# 			cost += row.amount

		# if self.total_cost == 0:
			# frappe.throw("Cost must be larger than 0 for Currency {}".format(cur))
			# frappe.throw("Cost must be larger than 0 for Currency")
		if len(self.order_cost) == 0:
			frappe.throw('Please add Order Cost first!')

		for item in self.items:
			if not item.detail_order:
				frappe.throw("Detail Order for Item {} is not set".format(item.item_code))
			if not item.site:
				frappe.throw("Site for Item {} is not set".format(item.item_code))
		
		self.delivery_date = nowdate()

	def on_submit(self):

		# list_of_pricelist = set(d.price_list for d in self.items)
		projectName = self.create_work_orders()
		
		list_of_currency = set(d.currency for d in self.profit_loss)

		for pr in list_of_currency:
			salesOrderName = self.create_sales_order(projectName,pr)
			frappe.db.set_value("Sales Order",salesOrderName, "work_orders", projectName)

	def create_sales_order(self, projectName,currency):

		def set_missing_values(source,target):
			target.currency = currency

		so = get_mapped_doc("Reserve Order", self.name, {
		"Reserve Order": {
			"doctype": "Sales Order",
			"field_map": {
					"transaction_date":"reserve_date",
					"work_orders": self.work_orders,
					# "delivery_date": self.expected_delivery_date,
					"customer": self.customer,
					"customer_name": self.customer_name,
					"expected_delivery_date": "delivery_date",
					"custom_order_type": self.order_type
				}
			},
			"Order Form Items": {
				"doctype" : "Sales Order Item",
				"field_map": {
					"item_code": "item_code",
					"item_name": "item_name",
					"qty":"qty",
					"rate":"rate",
					"amount":"amount",
					"detail_order":"detail_order"
				}
				,"condition": lambda doc:doc.currency == currency
			}
		}, None, set_missing_values)
		
		so.order_type = "Sales"
		
		if len(so.get("items")) > 0:
			so.selling_price_list = self.items[0].price_list
			so.save(ignore_permissions=True)

			# update SO to Detail Order
			for item in so.items:
				frappe.set_value("Detail Order",item.detail_order,"sales_order",so.name)

			so.submit()
			frappe.set_value("Reserve Order",self.name,"sales_order",so.name)
			# frappe.db.set_value("Project", self.work_orders,"sales_order",so.name)
			frappe.db.set_value("Project", projectName,"sales_order",so.name)

			frappe.db.set_value("Sales Order", so.name,"reserve_order",self.name)

			return so.name

	def create_work_orders(self):
		doc = get_mapped_doc("Reserve Order", self.name, {
		"Reserve Order": {
			"doctype": "Project",
			"field_map": {
				# "delivery_date":"delivery_date",
				# "expected_delivery_date":"expected_delivery_date",
				"total_order_custome":"total_order",
				"total_cost_custome":"total_cost",
				"total_profit_custome":"profit",
				"reserve_date":"expected_start_date",
				"expected_delivery_date":"expected_end_date",
				"order_form": self.name,
				"order_type": self.order_type,
				"pic": self.pic,
				"pic_name":self.pic_name,
				"sponsor_company": "sponsor_company"
				}
			},
			"Order Form Items":{
				"doctype": "Order Form Items",
				"field_map": {}
			},
			"Order Cost": {
				"doctype" : "Order Cost",
				"field_map": {
					"item_code": "item_code",
					"item_name": "item_name",
					"qty":"qty",
					"rate":"rate",
					"amount":"amount",
					"detail_order": "detail_order"
				}
			}
		}, None, None)

		doc.project_name = self.customer + " " + self.order_type + " " + self.name

		# generate summary Sales and Costs
		for item in self.profit_loss:
			# if item.type != "Margin":
			doc.append("sales_and_costs",{
				"currency": item.currency,
				"type": item.type,
				"amount": item.amount
			})
		
		order_form = frappe.get_doc("Order Form", self.order_form)

		doc.akta_dan_sk = order_form.akta_dan_sk
		doc.nib = order_form.nib
		doc.npwp = order_form.npwp
		doc.wajib_lapor = order_form.wajib_lapor
		doc.kop_surat_dan_cap_perusahaan = order_form.kop_surat_dan_cap_perusahaan
		doc.ktp_hrd = order_form.ktp_hrd
		doc.izin_usaha = order_form.izin_usaha
		doc.sertifikat_bpjs_perusahaan = order_form.sertifikat_bpjs_perusahaan
		doc.passport_atau_ktp_pimpinan_tertinggi_atau_direktur = order_form.passport_atau_ktp_pimpinan_tertinggi_atau_direktur
		doc.optional_form_1 = order_form.optional_form_1
		doc.optional_form_2 = order_form.optional_form_2
		doc.optional_form_3 = order_form.optional_form_3
				
		doc.save(ignore_permissions=True)

		# update WO number to Detail Order
		for item in doc.order_items:
			frappe.set_value("Detail Order",item.detail_order,"wo_number",doc.name)
			


		frappe.set_value("Reserve Order",self.name,"work_orders",doc.name)
		frappe.db.set_value("Project", doc.name,"reserve_order",self.name)
		return doc.name

	def before_cancel(self):
		self.action_on_cancel_and_rejected()

	def validate_prices(self):
		for item in self.items:
			if frappe.db.exists('Item Default', {'parent' : item.item_code, 'idx' : 1}):
				item_default_price = frappe.get_doc('Item Default', {'parent' : item.item_code, 'idx' : 1})
				if item_default_price and item_default_price.default_price_list:
					if not item.currency or not item.price_list:
						frappe.throw('Table Items: Please set Item Price for item code {} at row #{}'.format(item.item_code, item.idx))		

		# Skip Validation for price 0 or dont have price
		# for item in self.order_cost:
		# 	if frappe.db.exists('Item Default', {'parent' : item.item_code, 'idx' : 1}):
		# 		item_default_price = frappe.get_doc('Item Default', {'parent' : item.item_code, 'idx' : 1})
		# 		if item_default_price and item_default_price.default_price_list:
		# 			if not item.currency or not item.price_list:
		# 				frappe.throw('Table Order Cost: Please set Item Price for item code {} at row #{}'.format(item.item_code, item.idx))		

	def action_on_cancel_and_rejected(self):
		# remove link
		so_list = frappe.db.get_all("Sales Order", {"reserve_order":self.name},["name"])
		wo = frappe.db.get_all("Project",{"reserve_order":self.name},["name"])
		
		for row in self.items:
			# frappe.db.set_value("Order Form Items", row.name,"detail_order", "")
			row_do = frappe.get_doc('Detail Order', row.detail_order)
			if row_do.docstatus == 1:
				frappe.db.sql(
					"""
					UPDATE `tabDetail Order` SET docstatus = 0, workflow_state = 'Draft' where `name` = "{}"
					
					""".format(row.detail_order)
				)
				# frappe.get_doc("Detail Order", row.detail_order).cancel()
			

		for row in self.order_cost:
			frappe.db.set_value("Order Cost", row.name,"detail_order", "")
		
		for row in wo:
			frappe.db.set_value("Project", row.name, "reserve_order","")
			frappe.db.set_value("Project", row.name, "sales_order","")

			for rd in frappe.get_all('Result Document', filters={'work_orders':row.name}, fields=['name']):
				frappe.db.set_value("Result Document", rd.name, "work_order_detail","")
				frappe.db.set_value("Result Document", rd.name, "work_orders","")
			
			for item in frappe.get_doc("Project",row.name).order_items:
				frappe.db.set_value("Order Form Items", item.name, "detail_order","")
			
			for item in frappe.get_doc("Project",row.name).order_cost:
				frappe.db.set_value("Order Cost", item.name, "detail_order","")

			vouchers = frappe.get_all('Purchase Invoice', filters={'work_orders': row.name}, fields=['name','docstatus'])
			child_tables = ["Purchase Invoice Item","Pricing Rule Detail","Purchase Receipt Item Supplied","Purchase Taxes and Charges","Voucher Note Items","Purchase Invoice Advance","Advance Tax","Payment Schedule"]
			for ct in child_tables:
				for voc in vouchers:
					frappe.db.sql(
						"""
						DELETE FROM `tabVersion` WHERE `docname` = "{}"
						""".format(voc.name)
					)
					frappe.db.sql(
						"""
						DELETE FROM `tabComment` WHERE reference_name = "{}"
						""".format(voc.name)
					)
					frappe.db.sql(
						"""
						DELETE FROM `tabActivity Log` WHERE reference_name = "{}"
						""".format(voc.name)
					)
					names_child = frappe.db.get_list(ct, filters={'parent': voc.name}, fields=['name','parent'])
					if names_child:
						frappe.db.sql(
							"""
								DELETE FROM `tab{}` WHERE parent = "{}"
							""".format(ct, voc.name)
						)

			frappe.db.sql(
				"""
				DELETE FROM `tabPurchase Invoice` WHERE `work_orders` = "{}"
				""".format(row.name)
			)

		for row in so_list:
			frappe.db.set_value("Sales Order", row.name, "reserve_order","")
			frappe.db.set_value("Sales Order", row.name, "work_orders","")
			so = frappe.get_doc("Sales Order",row.name)

			for item in so.items:
				item.db_set("detail_order","")
			
			if so.docstatus == 1:
				so.cancel()
			
			do_list = frappe.db.get_all("Detail Order", {"sales_order":row.name},["name","docstatus"])

			for drow in do_list:
				frappe.db.set_value("Detail Order", drow.name, "sales_order","")
				frappe.db.set_value("Detail Order", drow.name, "wo_number","")
				if drow.docstatus == 1:
					frappe.get_doc("Detail Order",drow.name).cancel()
				
				# frappe.delete_doc("Detail Order",drow.name)
			
		for row in so_list:
			frappe.delete_doc("Sales Order", row.name)

		for row in wo:
			frappe.db.delete("Purchase Order", {
				"work_orders" : row.name
			})
			frappe.delete_doc("Project", row.name)

@frappe.whitelist()
def add_to_cost(item_code, qty, order_type, site=""):

	data = []

	pricelist = frappe.db.get_single_value("Buying Settings", "buying_price_list")
	
	pb = None
	if frappe.db.exists("Product Bundle", item_code):
		pb = frappe.get_doc("Product Bundle", item_code)
		
	if pb:
		for item in pb.items:
			has_variant = frappe.get_value("Item", item.item_code, "has_variants")
			item_site = frappe.get_doc("Item",item.item_code)
			rate = frappe.get_value("Item Price",{"item_code":item.item_code,"buying":1},"price_list_rate")
			price_list = frappe.get_value("Item Price",{"item_code":item.item_code,"buying":1},"price_list")
			currency = frappe.get_value("Item Price",{"item_code":item.item_code,"buying":1},"currency")
			
			if site != "" and has_variant:

				item_site_code = frappe.get_value("Item Variant Attribute",{"variant_of":item.item_code, "attribute":"site", "attribute_value":site},"parent")
				if item_site_code:
					item_site = frappe.get_doc("Item",item_site_code)
					rate = frappe.get_value("Item Price",{"item_code":item_site.name,"buying":1},"price_list_rate")
					price_list = frappe.get_value("Item Price",{"item_code":item_site.item_code,"buying":1},"price_list")
					currency = frappe.get_value("Item Price",{"item_code":item_site.item_code,"buying":1},"currency")
					

			# if not rate:
			# 	rate = frappe.get_value("Item Price",{"item_code":item_code,"buying":1},"price_list_rate")

			data.append(frappe._dict({
					"item_code": item_site.item_code,
					"item_name": item_site.item_name,
					"qty" : flt(qty) * item.qty,
					"rate" : 0 if not rate else rate,
					"amount" : flt(rate) * flt(qty) * item.qty,
					"price_list" : price_list,
					"currency" : currency,
					"site": site,
					"type": order_type
				}))	
	else:
		item_price = frappe.get_value("Item Price",{"item_code":item_code,"buying":1,"price_list":pricelist},["price_list_rate","price_list","currency"], as_dict=1)
		if not item_price:
			item_price = frappe.get_value("Item Price",{"item_code":item_code,"buying":1},["price_list_rate","price_list","currency"], as_dict=1)
		
		if not item_price:
			price_list = ""
			currency = ""
			rate = 0
		else:
			price_list = item_price.price_list or ""
			currency = item_price.currency or ""
			rate = item_price.price_list_rate or 0

		if price_list == "":
			frappe.msgprint("Item {} doesn't have Buying Price List".format(item_code))
		if rate == 0:
			frappe.msgprint("Item {} doesn't have Buying Price List Rate".format(item_code))
		if currency == "":
			frappe.msgprint("Item {} doesn't have Buying Currency".format(item_code))

		data.append(frappe._dict({
			"item_code": item_code,
			"item_name": frappe.get_value("Item",item_code,"item_name"),
			"qty" : flt(qty),
			"rate" : rate,
			"amount" : flt(rate) * flt(qty),
			"price_list" : price_list,
			"currency" : currency,
			"site": site or "",
			"type": order_type
		}))

	return data