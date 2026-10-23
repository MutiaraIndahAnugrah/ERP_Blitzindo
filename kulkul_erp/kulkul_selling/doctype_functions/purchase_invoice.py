import frappe
from frappe.model import document
import frappe.model.rename_doc as rd
import datetime
from frappe.utils.data import flt
import kulkul_erp.kulkul_selling.doctype_functions.function_helpers as fh

def check(doc, method):
    # pass
    if doc.workflow_state == 'Completed':
        i = 0
        if doc.items and len(doc.items) > 0:
            for item in doc.items:
                i =+ 1
                if not item.proof_of_payment or item.proof_of_payment == '':
                    frappe.throw('Items at row #{} required proof of payment!'.format(i))

    # if doc.workflow_state != 'Completed' and len(doc.payment_schedule) > 0:
    #     for d in doc.payment_schedule:
    #             # frappe.msgprint(doc.grand_total or 0 * flt(d.invoice_portion / 100))
    #             if d.invoice_portion:
    #                 d.payment_amount = flt(doc.grand_total or 0 * flt(50 / 100), d.precision('payment_amount'))
    #                 d.base_payment_amount = flt(doc.base_grand_total or 0 * flt(50 / 100), d.precision('base_payment_amount'))
    #                 d.outstanding = d.payment_amount
    #             elif not d.invoice_portion:
    #                 d.base_payment_amount = flt(d.payment_amount * doc.conversion_rate, d.precision('base_payment_amount'))

@frappe.whitelist()
def change_naming_series(name):
    doc = frappe.get_doc('Purchase Invoice', name)
    if doc.docstatus == 0 and (not doc.amended_from or doc.amended_from == ''):
        posting_date = datetime.datetime.strptime(doc.posting_date.strftime('%Y-%m-%d'), '%Y-%m-%d')
        month_and_year = "{:02d}{}".format(posting_date.month, str(posting_date.year)[2:4])
        naming = None
        
        # if month_and_year == doc.name[8:12]:
        #     return {'error':'Same Month and Year!'}

        if doc.voucher_type == 'Internal':
            naming = "VOC-INT-{}".format(month_and_year)
        elif doc.voucher_type == 'Visa':
            naming = "VOC-VIS-{}".format(month_and_year)
        elif doc.voucher_type == 'Legal':
            naming = "VOC-LEG-{}".format(month_and_year)

        if naming:
            all_series = frappe.db.sql("""
               SELECT CAST(SUBSTRING_INDEX(name,'-', -1) AS SIGNED) AS name 
               FROM `tabPurchase Invoice` 
               WHERE amended_from IS NULL AND name LIKE 
               "{}%" ORDER BY CAST(SUBSTRING_INDEX(name,'-', -1) AS SIGNED) ASC
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
                    if month_and_year != doc.name[8:12]:
                        fix_new_name = "{}-{:04d}".format(naming, int(array_series[len(array_series) - 1]) + 1)
                    elif missing_number_one == False:
                        fix_new_name = doc.name
                        return {'name':fix_new_name, 'same':'All Document Number for Voucher already sorted correctly'}
                
                if month_and_year == doc.name[8:12] and len(missing_series) > 0 and missing_number_one == False:
                    if int(missing_series[0]) > int(doc.name[-4:]):
                        fix_new_name = doc.name
                        return {'name':fix_new_name, 'same':'This document is sorted correctly, but the Voucher Document still has a gap!'}
                
                if missing_number_one == True:
                    fix_new_name = "{}-0001".format(naming)

                if not fix_new_name:
                    return {'error': 'Something went wrong! Call IT Support.'}
            else:
                fix_new_name = "{}-0001".format(naming)
                missing_series = []
                array_series = []

            frappe.db.sql("""
                UPDATE `tabPurchase Invoice` SET name = "{}" WHERE name = "{}"
            """.format(fix_new_name, doc.name))

            child_tables = ["Purchase Invoice Item","Pricing Rule Detail","Purchase Receipt Item Supplied","Purchase Taxes and Charges","Voucher Note Items","Purchase Invoice Advance","Advance Tax","Payment Schedule"]
            for ct in child_tables:
                names_child = frappe.db.get_list(ct, filters={'parent': doc.name}, fields=['name','parent'])
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

def update_workflow_state(doc, method):
    frappe.db.sql(
        """
        UPDATE `tabPurchase Invoice` SET docstatus = 2, workflow_state = "Cancelled", status = "Cancelled" where `name` = "{}"
        
        """.format(doc.name)
    )
    