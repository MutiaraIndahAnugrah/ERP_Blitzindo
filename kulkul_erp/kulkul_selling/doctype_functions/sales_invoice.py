import frappe
import datetime
from frappe.model.workflow import apply_workflow
import kulkul_erp.kulkul_selling.doctype_functions.function_helpers as fh

def check_draft(doc, method):
    if doc.work_orders:
        list_invoice = frappe.db.sql("""
				SELECT
					`name`
				FROM `tabSales Invoice`
				WHERE name != "{}"
				and docstatus = 0
				and work_orders = "{}"
			""".format(doc.name, doc.work_orders), as_dict=1)

    # if len(list_invoice) > 0:
    # 	frappe.throw("This Invoice still Draft {} for WO {} ".format(list_invoice[0].name,doc.work_orders))

@frappe.whitelist()
def custom_submit(docname):
    prof_inv = frappe.get_doc("Sales Invoice", docname)

    new_sinv = frappe.get_doc(frappe.copy_doc(prof_inv))

    new_sinv.naming_series = new_sinv.naming_series.replace("PROF-", "")
    new_sinv.workflow_state = ""
    new_sinv.save(ignore_permissions=True)

    new_sinv = apply_workflow(new_sinv, "Save")

    new_sinv.submit()

    frappe.delete_doc("Sales Invoice", docname)

    return new_sinv.name


@frappe.whitelist()
def change_naming_series(name):
	# frappe.msgprint('Doc Name : {}'.format(name))
	doc = frappe.get_doc('Sales Invoice', name)
	if doc.docstatus == 0 and (not doc.amended_from or doc.amended_from == ''):
		posting_date = datetime.datetime.strptime(doc.posting_date.strftime('%Y-%m-%d'), '%Y-%m-%d')
		month_and_year = "{:02d}{}".format(posting_date.month, str(posting_date.year)[2:4])
		naming = None

		# if month_and_year == doc.name[-9:][0:4]:
		# 	return {'error': 'Same Month and Year!'}

		if doc.naming_series == 'PROF-DPKK-.MM.YY.-.####':
			naming = "PROF-DPKK-{}".format(month_and_year)
		elif doc.naming_series == 'PROF-KWT-.MM.YY.-.####':
			naming = "PROF-KWT-{}".format(month_and_year)
		elif doc.naming_series == 'PROF-PBU-.MM.YY.-.####':
			naming = "PROF-PBU-{}".format(month_and_year)
		elif doc.naming_series == 'PROF-CN-.MM.YY.-.####':
			naming = "PROF-CN-{}".format(month_and_year)
		elif doc.naming_series == 'DPKK-.MM.YY.-.####':
			naming = "DPKK-{}".format(month_and_year)
		elif doc.naming_series == 'KWT-.MM.YY.-.####':
			naming = "KWT-{}".format(month_and_year)
		elif doc.naming_series == 'PBU-.MM.YY.-.####':
			naming = "PBU-{}".format(month_and_year)
		elif doc.naming_series == 'CN-.MM.YY.-.####':
			naming = "CN-{}".format(month_and_year)

		if naming:
            # frappe.msgprint('Date : {} | Type : {} | Name : {} | Format : {}'.format(month_and_year, doc.voucher_type, doc.name, naming))
            # frappe.msgprint('Doc Status : {}'.format(doc.docstatus))
			all_series = frappe.db.sql("""
				SELECT CAST(SUBSTRING_INDEX(name,'-', -1) AS SIGNED) AS name FROM `tabSales Invoice` 
				WHERE amended_from IS NULL AND name LIKE "{}%" 
				ORDER BY CAST(SUBSTRING_INDEX(name,'-', -1) AS SIGNED) ASC
			""".format(naming), as_dict=1)

			missing_number_one = False
			fix_new_name = None
			
			if len(all_series) > 0:
				array_series = fh.pluck(all_series, 'name')

				if int(array_series[0]) != 1:
					array_series.insert(0, 1)
					missing_number_one = True

				missing_series = fh.find_missing(array_series)

				if len(missing_series) > 0:
					fix_new_name = "{}-{:04d}".format(naming, int(missing_series[0]))
				else:
					if month_and_year != doc.name[-9:][0:4]:
						fix_new_name = "{}-{:04d}".format(naming, int(array_series[len(array_series) - 1]) + 1)
					elif missing_number_one == False:
						fix_new_name = doc.name
						return {'name':fix_new_name, 'same':'All Document Number for {} already sorted correctly'.format(doc.doctype)}
                
				if month_and_year == doc.name[-9:][0:4] and len(missing_series) > 0 and missing_number_one == False:
					if int(missing_series[0]) > int(doc.name[-4:]):
						fix_new_name = doc.name
						return {'name':fix_new_name, 'same':'This document is sorted correctly, but the {} Document still has a gap!'.format(doc.doctype)}

				if missing_number_one == True:
					fix_new_name = "{}-0001".format(naming)

				if not fix_new_name:
					return {'error': 'Something went wrong! Call IT Support.'}
			else:
				fix_new_name = "{}-0001".format(naming)
				missing_series = []
				array_series = []
			# frappe.msgprint('last Doc : {} | New Last Doc : {}'.format(int(all_series[0].name[-9:][5:9]) if len(all_series) > 0 else '0001'), fix_new_name)

			frappe.db.sql("""
				UPDATE `tabSales Invoice` SET name = "{}" WHERE name = "{}"
			""".format(fix_new_name, doc.name))

			child_tables = ["Sales Invoice Item",
							"Pricing Rule Detail",
							"Packed Item",
							"Sales Invoice Timesheet",
							"Sales Taxes and Charges",
							"Sales Invoice Advance",
							"Payment Schedule",
							"Sales Invoice Payment",
							"Sales Team"
							]

			for ct in child_tables:
				names_child = frappe.db.get_list(ct, filters={'parent': doc.name}, fields=['name', 'parent'])
				if names_child:
					frappe.db.sql(
						"""
							UPDATE `tab{}` SET parent = "{}" WHERE parent = "{}"
						""".format(ct, fix_new_name, doc.name)
					)

			frappe.db.sql(
                """
                UPDATE `tabVersion` SET docname = "{}" WHERE docname = "{}"
                """.format(fix_new_name, doc.name)
            )
			frappe.db.sql(
                """
                UPDATE `tabComment` SET reference_name = "{}" WHERE reference_name = "{}"
                """.format(fix_new_name, doc.name)
            )
			frappe.db.sql(
                """
                UPDATE `tabActivity Log` SET reference_name = "{}" WHERE reference_name = "{}"
                """.format(fix_new_name, doc.name)
            )

			frappe.db.commit()

			return {'name':fix_new_name, 'missing':missing_series, 'all_list':array_series}

def update_current_series_before_insert(doc, method):
    fh.update_current_value_series(doc)

def update_gl_entries(doc, method):
	frappe.db.sql(
		"""
			DELETE FROM `tabGL Entry` WHERE voucher_no = "{}"
		""".format(doc.name)
	)

	doc = frappe.get_doc("Sales Invoice", doc.name)
	doc.make_gl_entries()
	frappe.db.commit()