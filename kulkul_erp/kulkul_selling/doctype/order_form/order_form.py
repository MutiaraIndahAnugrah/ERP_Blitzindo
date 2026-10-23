# Copyright (c) 2022, Kulkul and contributors
# For license information, please see license.txt

import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document

class OrderForm(Document):
	def validate(self):
		if len(self.items) > 0:
			for item in self.items:
				if item.detail_order:
					do = frappe.get_doc('Detail Order', item.detail_order)
					do.type = item.type
					if do.qty != len(do.details) and do.type == 'Visa' and do.workflow_state == 'Submitted':
						frappe.throw("Quantity and Detail Order Quantity do not match for Detail Order Item {}".format(item.item_code))

					do.order_category_hidden = self.order_category
					if self.order_category == 'Sponsor':
						do.sponsor_company_hidden = self.sponsor_company
					else:
						do.sponsor_company_hidden = ''

					if do.docstatus == 0:
						do.save()

						do_after_save = frappe.get_doc('Detail Order', item.detail_order)
						if len(do_after_save.details) > 0 and do_after_save.type == 'Visa':
							for d in do_after_save.details:
								if d.data_tka:
									tka = frappe.get_doc('Tenaga Kerja', d.data_tka)
									if do_after_save.order_category_hidden == 'Sponsor':
										tka.sponsor_company = do_after_save.sponsor_company_hidden
									else:
										tka.sponsor_company = ''
									tka.save()

	def before_submit(self):
		if not self.items:
			frappe.throw('Order Items can\'t be empty!')
		
		i = 1
		for item in self.items:
			if item.detail_order:
				do = frappe.get_doc('Detail Order', item.detail_order)
				do.type = item.type

				if do.docstatus == 0:
					do.save()

				if do.qty != len(do.details) and do.type == 'Visa' and item.type == 'Visa':
					frappe.throw("Quantity and Detail Order Quantity do not match for Detail Order Item {}".format(item.item_code))

				if do.workflow_state not in ['Submitted','Completed']:
					frappe.throw('You have not submitted detail order at row #{} item {}!'.format(i, item.item_code))

				for item_do in do.details:
					if (not item_do.data_tka or item_do.data_tka == '') and (do.type == 'Visa' and item.type == 'Visa'):
						frappe.throw('You have detail order with empty TKA at row #{} item {}!'.format(i, item.item_code))

			if not item.detail_order:
				frappe.throw("Detail Order for Item {} is not set".format(item.item_code))

			if not item.site:
				frappe.throw("Site for Item {} is not set".format(item.item_code))

			i =+ 1

	def on_submit(self):
		ro = get_mapped_doc("Order Form", self.name, {
			"Order Form": {
				"doctype": "Reserve Order",
				"field_map": {
					# "delivery_date":"reserve_date",
					"customer": "customer",
					"delivery_date": "delivery_date",
					"order_form_type": "type",
					"account_manager": "pic",
					"pic_name": "pic_name",
					"order_form": self.name,
					"delivery_date": "expected_delivery_date"
				}
			},
			"Order Form Items": {
				"doctype" : "Order Form Items",
				"field_map": {
				
				}
			}
		}, None, None)
		ro.save(ignore_permissions=True)
		frappe.db.set_value("Order Form",self.name,"reserve_order",ro.name)
	
	def on_update(self):
		for item in self.items:
			if item.detail_order:
				if frappe.db.exists('Detail Order', item.detail_order):
					do = frappe.get_doc('Detail Order', item.detail_order)
					if do.docstatus == 0:
						do.order_form_item = item.name
						do.qty = item.qty
						do.item_code = item.item_code
						do.item_name = item.item_name
						do.type = item.type
						do.rate = item.rate
						do.amount = item.qty * item.rate
						do.save()

	def before_cancel(self):
		self.delete_relation_doctype()

		frappe.db.sql("""
			UPDATE `tabDetail Order` SET docstatus = 2, workflow_state = 'Cancelled' WHERE order_form = "{}"
		""".format(self.name))

		frappe.db.sql("""
			UPDATE `tabOrder Form Items` SET docstatus = 2 WHERE parent = "{}"
		""".format(self.name))

		frappe.db.sql(
		"""
			UPDATE `tabDetail Order Items` SET docstatus = 2 WHERE parent = "{}"
		""".format(frappe.db.get_value('Detail Order', {'order_form' : self.name}, 'name'))
		)

		frappe.db.sql("""
			DELETE FROM `tabReserve Order` where order_form = "{}"
		""".format(self.name))

		# frappe.db.sql("""
		# 	UPDATE `tabReserve Order` SET workflow_state = 'Rejected', docstatus = 1 where order_form = "{}"
		# """.format(ro.name))

		self.refresh_child_table()

	def on_trash(self):
		self.delete_relation_doctype()

		frappe.db.sql("""
				DELETE FROM `tabOrder Form Items` where parent = "{}"
			""".format(self.name))
		
		frappe.db.sql("""
			DELETE FROM `tabOrder Form Items` WHERE parenttype = 'Order Form' AND name IN (
			SELECT items.name FROM `tabOrder Form Items` items
			LEFT JOIN `tabOrder Form` parent on parent.name = items.parent
			WHERE parent.name is null)
		""")

		frappe.db.sql("""
			DELETE FROM `tabReserve Order` where order_form = "{}"
		""".format(self.name))

		self.refresh_child_table()

	def delete_relation_doctype(self):
		reserve_order = frappe.db.get_list('Reserve Order', filters={'order_form' : self.name}, fields=['name', 'docstatus'])
		for ro in reserve_order:
			# if ro.docstatus == 1:
			# 	frappe.msgprint('Please Cancel then Delete Reverse Order <a href="/app/reserve-order/{0}" target="blank">{0}</a> first!'.format(ro.name))
			# 	continue
			frappe.db.sql("""
					DELETE FROM `tabSales Order` where reserve_order = "{}"
				""".format(ro.name))

			work_orders = frappe.db.get_list('Project', filters={'reserve_order' : ro.name}, fields=['name'])
			for wo in work_orders:
				frappe.db.sql("""
						DELETE FROM `tabPurchase Order` where work_orders = "{}"
					""".format(wo.name))

				vouchers = frappe.get_all('Purchase Invoice', filters={'work_orders': wo.name}, fields=['name','docstatus'])
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

				frappe.db.sql("""
						DELETE FROM `tabPurchase Invoice` where work_orders = "{}"
					""".format(wo.name))

				frappe.db.sql("""
						DELETE FROM `tabPayment Entry` where project = "{}"
					""".format(wo.name))

				frappe.db.sql("""
						DELETE FROM `tabSales Invoice` where work_orders = "{}"
					""".format(wo.name))
					
			frappe.db.sql("""
					DELETE FROM `tabProject` where reserve_order = "{}"
				""".format(ro.name))

	def refresh_child_table(self):
		frappe.db.sql("""
			DELETE FROM `tabOrder Form Items` WHERE parenttype = 'Project' AND name IN (
			SELECT items.name FROM `tabOrder Form Items` items
			LEFT JOIN `tabProject` parent on parent.name = items.parent
			WHERE parent.name is null)
		""")
		frappe.db.sql("""
			DELETE FROM `tabOrder Form Items` WHERE parenttype = 'Reserve Form' AND name IN (
			SELECT items.name FROM `tabOrder Form Items` items
			LEFT JOIN `tabReserve Order` parent on parent.name = items.parent
			WHERE parent.name is null)
		""")
		frappe.db.sql("""
			DELETE FROM `tabDetail Order Items` where name IN (
			SELECT doi.name
			FROM `tabDetail Order Items` doi
			LEFT JOIN `tabDetail Order` parent on parent.name = doi.parent
			where parent.name is null)
		""")
		frappe.db.sql("""
			DELETE from `tabGL Entry` where name IN (
			SELECT gle.name 
			FROM `tabGL Entry` gle
			left join `tabPurchase Invoice` si on si.name = gle.voucher_no
			where si.name is null
			and (gle.voucher_type = "Voucher" or gle.voucher_type = "Purchase Invoice"))
		""")
		frappe.db.sql("""
			DELETE from `tabGL Entry` where name IN (
			SELECT gle.name FROM `tabGL Entry` gle left join `tabSales Invoice` si on si.name = gle.voucher_no
			where si.name is null
			and (gle.voucher_type = "Sales Invoice"))
		""")


@frappe.whitelist()
def create_reserve_order(source_name, target_doc=None):
	
	doclist = get_mapped_doc("Order Form", source_name, {
		"Order Form": {
			"doctype": "Reserve Order",
			"field_map": {
				# "delivery_date":"reserve_date",
				"customer": "customer",
				"delivery_date": "delivery_date",
				"delivery_date": "expected_delivery_date",
				"order_form_type": "type",
				"account_manager": "pic",
				"pic_name": "pic_name",
				"order_form": source_name
			}
		},
		"Order Form Items": {
			"doctype" : "Order Form Items",
			"field_map": {
			
			}
		}
	}, target_doc, None)
	doclist.save(ignore_permissions=True)
	frappe.db.set_value("Order Form",source_name,"reserve_order",doclist.name)
	return doclist

@frappe.whitelist()
def make_customer(source_name, target_doc=None):
	return _make_customer(source_name, target_doc)

@frappe.whitelist()
def update_document_to_draft(name):
	docstatus = frappe.db.get_value('Order Form', name, 'docstatus')

	if docstatus != 2:
		frappe.throw('Document status not 2 / Cancelled')

	frappe.db.sql(
		""" 
		UPDATE `tabOrder Form` SET docstatus = 0 WHERE name = "{}"
		""".format(name)
	)

	frappe.db.sql(
	"""
		UPDATE `tabOrder Form Items` SET docstatus = 0 WHERE parent = "{}"
	""".format(name)
	)

	frappe.db.sql(
	"""
		UPDATE `tabDetail Order` SET docstatus = 0, workflow_state = 'Draft' WHERE order_form = "{}"
	""".format(name)
	)

	frappe.db.sql(
	"""
		UPDATE `tabDetail Order Items` SET docstatus = 0 WHERE parent = "{}"
	""".format(frappe.db.get_value('Detail Order', {'order_form' : name}, 'name'))
	)

	frappe.db.commit()

	return True

def _make_customer(source_name, target_doc=None):

	doclist = get_mapped_doc("Order Form", source_name,
		{"Order Form": {
			"doctype": "Customer",
			"field_map": {
				
			}
		}}, target_doc, None)

	return doclist