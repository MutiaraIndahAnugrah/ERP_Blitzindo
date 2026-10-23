# Copyright (c) 2022, Kulkul and contributors
# For license information, please see license.txt

import frappe
from erpnext.setup.utils import get_exchange_rate

def execute(filters=None):
	columns, data = [], []
	columns = [
		"Harga Jual IDR:Data:250",
		"Item HPP:Link/Item:250",
		"HPP:Data:150",
		"Exchange Rate:currency:150",
		"HPP IDR:Currency:150"
	]

	product_bundle = filters.get("product_bundle")

	harga_jual = frappe.get_value("Item Price",{"item_code":product_bundle,"selling":1}, ["currency","price_list_rate"])
	query = frappe.db.sql("""
			SELECT 
			pbi.item_code `item_code`
			, CONCAT(ipb.`currency`, " ", FORMAT(ipb.price_list_rate,2)) `hpp`, ipb.price_list_rate, ipb.currency
			FROM `tabProduct Bundle Item` pbi
			LEFT JOIN `tabItem Price` ipb ON pbi.item_code = ipb.item_code AND ipb.buying = 1
			WHERE pbi.parent = "{}"
		""".format(product_bundle), as_dict=1)

	first_idx = True
	harga_jual_formatted = "IDR 0"
	harga_jual_idr = 0
	sum_hpp = 0
	if harga_jual:
		harga_jual_idr = harga_jual[1]
		if harga_jual[0] != "IDR":
			harga_jual_idr = harga_jual[1] * get_exchange_rate(harga_jual[0],"IDR")

		harga_jual_formatted = "{} {:,.2f}".format("IDR",harga_jual_idr)
	
	for row in query:
		hpp_idr = row.price_list_rate or 0
		ex_rate = 1

		if row.currency != "IDR" and row.currency:
			ex_rate = get_exchange_rate(row.currency,"IDR")
			hpp_idr = (row.price_list_rate or 0) * ex_rate

		if first_idx:
			first_idx = False
		else:
			harga_jual_formatted = ""

		sum_hpp += hpp_idr
		data.append([harga_jual_formatted,row.item_code,row.hpp, ex_rate,hpp_idr])
			
	data.append(["Margin Profit/Loss","IDR {:,.2f}".format(harga_jual_idr - sum_hpp),"","",""])
	return columns, data

@frappe.whitelist()
def get_bundle_items(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""
			SELECT
				item.`item_code`, item.`item_name`
			FROM `tabItem` item
			JOIN `tabProduct Bundle` pb on pb.new_item_code = item.name
			WHERE item.item_code LIKE "%{0}%"
			or item.item_name LIKE "%{0}%"
		""".format(txt))