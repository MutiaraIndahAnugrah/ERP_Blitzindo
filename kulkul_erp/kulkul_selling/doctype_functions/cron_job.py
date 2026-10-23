from dataclasses import fields
from erpnext.setup.utils import get_exchange_rate
import frappe

def update_passport_expired_tka():
    # set null Tenaga Kerja passport_expired_status
    frappe.db.sql(
        """
        UPDATE `tabTenaga Kerja` SET passport_expired_status = ''
        
        """
    )

    # set passport_expired_status with condition passport_expired_date < now + 18 month
    frappe.db.sql(
        """
        UPDATE `tabTenaga Kerja` SET passport_expired_status = 'Expired less than 18 months' where `passport_expired_date` < NOW() + INTERVAL 18 MONTH

        """
    )


def update_status_expired_result_document():
    # set RD status_expired = Non-Active
    frappe.db.sql(
        """
        UPDATE `tabResult Document` SET status_expired = 'Non-Active' where `expired_date` < NOW()
        
        """
    )

    # set RD status_expired = Active
    frappe.db.sql(
        """
        UPDATE `tabResult Document` SET status_expired = 'Active' where `expired_date` >= NOW()
        
        """
    )

def update_status_expired_chart_result_document():
    frappe.db.sql(
        """
        UPDATE `tabResult Document` SET status_chart_expired = ''
        
        """
    )

    frappe.db.sql(
        """
        UPDATE `tabResult Document` SET status_chart_expired = 'Expired in 3 Months' where `expired_date` BETWEEN NOW() AND NOW() + INTERVAL 3 MONTH
        AND status_expired = 'Active'

        """
    )

    frappe.db.sql(
        """
        UPDATE `tabResult Document` SET status_chart_expired = 'Expired in 1 Month' where `expired_date` BETWEEN NOW() AND NOW() + INTERVAL 1 MONTH
        AND status_expired = 'Active'

        """
    )

    frappe.db.sql(
        """
        UPDATE `tabResult Document` SET status_chart_expired = 'Expired in 2 Weeks' where `expired_date` BETWEEN NOW() AND NOW() + INTERVAL 2 WEEK
        AND status_expired = 'Active'

        """
    )

    frappe.db.sql(
        """
        UPDATE `tabResult Document` SET status_chart_expired = 'Expired in 1 Week' where `expired_date` BETWEEN NOW() AND NOW() + INTERVAL 1 WEEK
        AND status_expired = 'Active'
        
        """
    )

    frappe.db.sql(
        """
        UPDATE `tabResult Document` SET status_chart_expired = 'Expired in 3 Days' where `expired_date` BETWEEN NOW() AND NOW() + INTERVAL 3 DAY
        AND status_expired = 'Active'
        
        """
    )

def update_quotation_status():
    # set RD quotation_status = Expired
    frappe.db.sql(
        """
        UPDATE `tabQuotation` SET quotation_status = 'Expired' WHERE `valid_till` < NOW()
        
        """
    )

    # set RD quotation_status = Active
    frappe.db.sql(
        """
        UPDATE `tabQuotation` SET quotation_status = 'Active' WHERE `valid_till` >= NOW()
        
        """
    )

# def update_order_form_order_type():
#     order_form_all = frappe.get_all('Order Form',fields=['name','from_quotation'])
#     for of in order_form_all:
#         if of.from_quotation:
#             qou_order_type = frappe.get_value('Quotation', of.from_quotation,'order_type')
#             frappe.db.sql(
#                 """
#                     UPDATE `tabOrder Form` SET order_type = "{0}" WHERE from_quotation = "{1}"
#                 """.format(qou_order_type, of.from_quotation)
#             )

# def update_fetch_tka():
#     purchase_invoice_item = frappe.get_all('Purchase Invoice Item', fields=['name','tka'])
#     for pii in purchase_invoice_item:
#         if pii.tka:
#             tenaga_kerja = frappe.get_value('Tenaga Kerja', pii.tka, ['no_passport','nama_asing','full_name'], as_dict=1)
#             if tenaga_kerja and tenaga_kerja.no_passport and tenaga_kerja.nama_asing and tenaga_kerja.full_name:
#                 frappe.db.sql(
#                     """
#                         UPDATE `tabPurchase Invoice Item` SET nama_tka = "{0}", foreign_name = "{1}", no_passport = "{2}" WHERE tka = "{3}"
#                     """.format(tenaga_kerja.full_name, tenaga_kerja.nama_asing, tenaga_kerja.no_passport, pii.tka)
#                 )

#     purchase_order_item = frappe.get_all('Purchase Order Item', fields=['name','tka'])
#     for poi in purchase_order_item:
#         if poi.tka:
#             tenaga_kerja = frappe.get_value('Tenaga Kerja', poi.tka, ['no_passport','nama_asing','full_name'], as_dict=1)
#             if tenaga_kerja and tenaga_kerja.no_passport and tenaga_kerja.nama_asing and tenaga_kerja.full_name:
#                 frappe.db.sql(
#                     """
#                         UPDATE `tabPurchase Order Item` SET nama_tka = "{0}", foreign_name = "{1}", no_passport = "{2}" WHERE tka = "{3}"
#                     """.format(tenaga_kerja.full_name, tenaga_kerja.nama_asing, tenaga_kerja.no_passport, poi.tka)
#                 )

# Fix sum of field in Work Orders
# def update_wo_cost_order_profit():
#     work_orders = frappe.get_all('Project', fields=['*'])
#     for wos in work_orders:
#         wo = frappe.get_doc('Project', wos.name)
#         total_order_c = 0
#         for item in wo.order_items:
#             order_er = False
#             if (item.qty and item.rate) and (item.qty > 0 and item.rate > 0):
#                 item.amount = item.qty * item.rate
#             else:
#                 item.amount = 0

#             if item.amount or item.amount > 0:
#                 if item.currency != "IDR":
#                     if wo.exchange_rates and len(wo.exchange_rates) > 0:
#                         for er in wo.exchange_rates:
#                             if er.currency == item.currency:
#                                 total_order_c += item.qty * (item.rate * er.rate)
#                                 order_er = True
#                     elif wo.reserve_order and wo.reserve_order != '':
#                         if frappe.db.exists('Reserve Order', wo.reserve_order):
#                             ro = frappe.get_doc('Reserve Order', wo.reserve_order)
#                             if ro and ro.exchange_rates and len(ro.exchange_rates) > 0:
#                                 for er_ro in ro.exchange_rates:
#                                     if er_ro.currency == item.currency:
#                                         total_order_c += item.qty * (item.rate * er_ro.rate)
#                                         order_er = True
#                     elif order_er == False:
#                         rate = get_exchange_rate(item.currency,"IDR")
#                         total_order_c += item.qty * (item.rate * rate)
#                 else:
#                     total_order_c += item.amount

#         total_order_custome = total_order_c

#         total_cost_c = 0
#         for item in wo.order_cost:
#             order_er = False
#             if (item.qty and item.rate) and (item.qty > 0 and item.rate > 0):
#                 item.amount = item.qty * item.rate
#             else:
#                 item.amount = 0

#             if item.amount or item.amount > 0:
#                 if item.currency != "IDR":
#                     if wo.exchange_rates and len(wo.exchange_rates) > 0:
#                         for er in wo.exchange_rates:
#                             if er.currency == item.currency:
#                                 total_cost_c += item.qty * (item.rate * er.rate)
#                                 order_er = True
#                     elif wo.reserve_order and wo.reserve_order != '':
#                         if frappe.db.exists('Reserve Order', wo.reserve_order):
#                             ro = frappe.get_doc('Reserve Order', wo.reserve_order)
#                             if ro and ro.exchange_rates and len(ro.exchange_rates) > 0:
#                                 for er_ro in ro.exchange_rates:
#                                     if er_ro.currency == item.currency:
#                                         total_cost_c += item.qty * (item.rate * er_ro.rate)
#                                         order_er = True
#                     elif order_er == False:
#                         rate = get_exchange_rate(item.currency,"IDR")
#                         total_cost_c += item.qty * (item.rate * rate)
#                 else:
#                     total_cost_c += item.amount

#         total_cost_custome = total_cost_c

#         total_profit_custome = total_order_custome - total_cost_custome

#         frappe.db.sql(
#             """
#             UPDATE `tabProject` SET total_profit_custome = {}, total_order_custome = {}, total_cost_custome = {}, total_order = {} WHERE name = "{}"
#             """.format(total_profit_custome, total_order_custome, total_cost_custome, total_order_custome, wos.name)
#         )