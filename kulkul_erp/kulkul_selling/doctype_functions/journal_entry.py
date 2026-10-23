import frappe
import datetime
import kulkul_erp.kulkul_selling.doctype_functions.function_helpers as fh

@frappe.whitelist()
def change_naming_series(name):
	doc = frappe.get_doc('Journal Entry', name)
	if doc.docstatus == 0 and (not doc.amended_from or doc.amended_from == ''):
		posting_date = datetime.datetime.strptime(doc.posting_date.strftime('%Y-%m-%d'), '%Y-%m-%d')
		month_and_year = "{:02d}{}".format(posting_date.month, str(posting_date.year)[2:4])

		if len(doc.naming_series) == 16:
			find_length = -9
		elif len(doc.naming_series) == 20:
			find_length = -9
		elif len(doc.naming_series) == 22:
			find_length = -11
		elif len(doc.naming_series) == 24:
			find_length = -11
		else:
			return {'error': 'Naming Series not found! Call IT Support.'}

		naming = None

		if doc.naming_series == 'JU-.MM.YY.-.####':
			naming = "JU-{}".format(month_and_year)

		elif doc.naming_series == 'JU-.CN-.MM.YY.-.####':
			naming = "JU-CN-{}".format(month_and_year)
		elif doc.naming_series == 'JU-.KB-.MM.YY.-D-.####':
			naming = "JU-KB-{}-D".format(month_and_year)
		elif doc.naming_series == 'JU-.KS-.MM.YY.-D-.####':
			naming = "JU-KS-{}-D".format(month_and_year)
		elif doc.naming_series == 'JU-.KB-.MM.YY.-C-.####':
			naming = "JU-KB-{}-C".format(month_and_year)
		elif doc.naming_series == 'JU-.KS-.MM.YY.-C-.####':
			naming = "JU-KS-{}-C".format(month_and_year)

		elif doc.naming_series == 'JU-.BCAD-.MM.YY.-D-.####':
			naming = "JU-BCAD-{}-D".format(month_and_year)
		elif doc.naming_series == 'JU-.BCAB-.MM.YY.-D-.####':
			naming = "JU-BCAB-{}-D".format(month_and_year)
		elif doc.naming_series == 'JU-.BCAS-.MM.YY.-D-.####':
			naming = "JU-BCAS-{}-D".format(month_and_year)
		elif doc.naming_series == 'JU-.KRMB-.MM.YY.-D-.####':
			naming = "JU-KRMB-{}-D".format(month_and_year)
		elif doc.naming_series == 'JU-.KSGD-.MM.YY.-D-.####':
			naming = "JU-KSGD-{}-D".format(month_and_year)
			
		elif doc.naming_series == 'JU-.BCAD-.MM.YY.-C-.####':
			naming = "JU-BCAD-{}-C".format(month_and_year)
		elif doc.naming_series == 'JU-.BCAB-.MM.YY.-C-.####':
			naming = "JU-BCAB-{}-C".format(month_and_year)
		elif doc.naming_series == 'JU-.BCAS-.MM.YY.-C-.####':
			naming = "JU-BCAS-{}-C".format(month_and_year)
		elif doc.naming_series == 'JU-.KRMB-.MM.YY.-C-.####':
			naming = "JU-KRMB-{}-C".format(month_and_year)
		elif doc.naming_series == 'JU-.KSGD-.MM.YY.-C-.####':
			naming = "JU-KSGD-{}-C".format(month_and_year)

		if naming:
			all_series = frappe.db.sql("""
				SELECT CAST(SUBSTRING_INDEX(name,'-', -1) AS SIGNED) AS name FROM `tabJournal Entry`
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
					if month_and_year != doc.name[find_length:][0:4]:
						fix_new_name = "{}-{:04d}".format(naming, int(array_series[len(array_series) - 1]) + 1)
					elif missing_number_one == False:
						fix_new_name = doc.name
						return {'name':fix_new_name, 'same':'All Document Number for {} already sorted correctly'.format(doc.doctype)}
                
				if month_and_year == doc.name[find_length:][0:4] and len(missing_series) > 0 and missing_number_one == False:
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

			frappe.db.sql("""
				UPDATE `tabJournal Entry` SET name = "{}" WHERE name = "{}"
			""".format(fix_new_name, doc.name))

			child_tables = ["Journal Entry Account"]

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