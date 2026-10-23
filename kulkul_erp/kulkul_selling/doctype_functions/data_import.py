import frappe
import json

@frappe.whitelist()
def update_expired_date_result_document(import_log):
    data = json.loads(import_log)

    for d in data:
        # set RD status_expired = Non-Active
        if d['success'] == True:
            frappe.db.sql(
                """
                UPDATE `tabResult Document` SET status_expired = 'Non-Active' where `expired_date` < NOW() AND `name` = "{}"
                
                """.format(d['docname'])
            )

            # set RD status_expired = Active
            frappe.db.sql(
                """
                UPDATE `tabResult Document` SET status_expired = 'Active' where `expired_date` >= NOW() AND `name` = "{}"
                
                """.format(d['docname'])
            )
            
            frappe.db.sql(
                """
                UPDATE `tabResult Document` SET status_chart_expired = '' WHERE `name` = "{}"
                
                """.format(d['docname'])
            )

            frappe.db.sql(
                """
                UPDATE `tabResult Document` SET status_chart_expired = 'Expired in 3 Months' where `expired_date` BETWEEN NOW() AND NOW() + INTERVAL 3 MONTH
                AND status_expired = 'Active' AND `name` = "{}"

                """.format(d['docname'])
            )

            frappe.db.sql(
                """
                UPDATE `tabResult Document` SET status_chart_expired = 'Expired in 1 Month' where `expired_date` BETWEEN NOW() AND NOW() + INTERVAL 1 MONTH
                AND status_expired = 'Active' AND `name` = "{}"

                """.format(d['docname'])
            )

            frappe.db.sql(
                """
                UPDATE `tabResult Document` SET status_chart_expired = 'Expired in 2 Weeks' where `expired_date` BETWEEN NOW() AND NOW() + INTERVAL 2 WEEK
                AND status_expired = 'Active' AND `name` = "{}"

                """.format(d['docname'])
            )

            frappe.db.sql(
                """
                UPDATE `tabResult Document` SET status_chart_expired = 'Expired in 1 Week' where `expired_date` BETWEEN NOW() AND NOW() + INTERVAL 1 WEEK
                AND status_expired = 'Active' AND `name` = "{}"
                
                """.format(d['docname'])
            )

            frappe.db.sql(
                """
                UPDATE `tabResult Document` SET status_chart_expired = 'Expired in 3 Days' where `expired_date` BETWEEN NOW() AND NOW() + INTERVAL 3 DAY
                AND status_expired = 'Active' AND `name` = "{}"
                
                """.format(d['docname'])
            )

            frappe.db.commit()