# Copyright (c) 2022, Kulkul and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns, data = [], []
	columns = [
		"Document Number:Data:250",
		"Orders:Data:150"
	]

	group_by = filters.get("group_by") or 'Customer'
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	
	if from_date and to_date:
		if from_date > to_date:
			frappe.msgprint("To Date should gether than From Date!")
		between = "WHERE creation BETWEEN '{}' AND '{}' AND docstatus = 1".format(from_date, to_date)
	else:
		between = "WHERE docstatus = 1"

	if group_by in ['Customer', 'PIC', 'Workflow_state']:
		if group_by in ['Customer', 'Workflow_state']:
			label = "si.{} as `x_axis_name`".format(group_by.lower())
		else:
			label = 'CONCAT(si.pic_name, " - ", si.pic) as `x_axis_name`'

		query = frappe.db.sql("""
				SELECT 
					COUNT(si.{0}) as `count_group`,
					{1}
				FROM `tabReserve Order` si
				{2} 
				GROUP BY si.{0}
				ORDER BY count_group DESC
			""".format(group_by.lower(), label, between), as_dict=1)
		
		for s in query:
			data.append([s.x_axis_name, s.count_group])
		# si = frappe.get_list("Sales Invoice", fields=['name','customer','total'])

		# name = frappe.get_list("Sales Invoice", pluck='name')
		# customer = frappe.get_list("Sales Invoice", pluck='customer')
		# site = frappe.get_list("Sales Invoice", pluck='territory')
	
	elif group_by == 'Item':
		query = frappe.db.sql("""
				SELECT 
					COUNT(i.name) as `count_group`, 
					CASE 
						WHEN itm.has_variants = 0 AND itm.variant_of IS NOT NULL THEN itm.variant_of
						WHEN itm.has_variants = 0 AND itm.variant_of IS NULL THEN itm.name
						WHEN itm.has_variants = 1 AND itm.variant_of IS NULL THEN itm.name
						WHEN itm.has_variants = 1 AND itm.variant_of IS NOT NULL THEN itm.variant_of
						ELSE itm.name END AS `x_axis_name` 
				FROM `tabOrder Form Items` i 
				JOIN `tabReserve Order` ro on ro.name=i.parent
				JOIN `tabItem` itm on itm.name=i.item_code
				WHERE i.parenttype = 'Reserve Order' {0}
				GROUP BY x_axis_name
				ORDER BY count_group DESC
			""".format(between.replace('WHERE', 'AND').replace('creation','ro.creation').replace('docstatus','ro.docstatus')), as_dict=1)
		
		for s in query:
			data.append([s.x_axis_name, s.count_group])
	
	return columns, data
