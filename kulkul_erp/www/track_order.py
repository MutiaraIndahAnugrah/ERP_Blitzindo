from __future__ import unicode_literals

import frappe
from jinja2 import utils
from frappe.utils import sanitize_html

def get_context(context):
    context.request_get = frappe.form_dict.s or ''
    context.is_single = True
    if context.request_get and context.request_get != '':
        if frappe.db.exists('Project', context.request_get):
            wo = frappe.get_doc('Project', context.request_get) 
            context.wo = wo
            if wo.status == 'Open':
                context.color_status = 'orange'
            elif wo.status == 'Completed':
                context.color_status = 'green'
            elif wo.status == 'In-Progress':
                context.color_status = 'blue'
            else:
                context.color_status = 'red'
        else:
            doi_parents = frappe.db.get_list('Detail Order Items', filters={'no_passport_tka' : context.request_get}, fields=['name', 'parent'])
            if not doi_parents:
                doi_parents = frappe.db.get_list('Detail Order Items', filters={'nama_tka' : context.request_get}, fields=['name', 'parent'])

            if not doi_parents:
                context.wo = None
                context.color_status = None
            else:
                context.is_single = None
                arr_results = []
                for dp in doi_parents:
                    do_wo = frappe.db.get_value('Detail Order', dp.parent, 'wo_number')
                    if do_wo not in arr_results:
                        arr_results.append(do_wo)

                if len(arr_results) > 0:
                    context.wo = arr_results
                else:
                    context.wo = None
