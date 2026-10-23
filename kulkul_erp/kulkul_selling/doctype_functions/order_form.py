import frappe

@frappe.whitelist()
def get_reserve_order(name):
    ro = frappe.db.get_all('Reserve Order',fields = ['*'], filters = {'order_form': name}, order_by='creation DESC', limit=1)

    if len(ro) > 0:
        return ro[0]
    else:
        return ''