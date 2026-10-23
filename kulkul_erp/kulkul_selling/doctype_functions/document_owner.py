import frappe

def sync_record(doc, method):
	if not frappe.db.exists('Document Owner', doc.name):
		doc_owner = frappe.new_doc('Document Owner')
		doc_owner.user_email = doc.name
		doc_owner.insert()

def insert_old_data():
	emails = frappe.db.get_list('User', pluck='name')
	for email in emails:
		doc_owner = frappe.new_doc('Document Owner')
		doc_owner.user_email = email
		doc_owner.insert()

def rename_document_owner(doc, method, old_name, new_name, old_title):
	# frappe.msgprint("{} - {} - {} - {}".format(doc, method, old_name, new_name))
	document_owner = frappe.get_last_doc('Document Owner', filters={"user_email": new_name})
	if document_owner.name != new_name:
		frappe.rename_doc('Document Owner', document_owner.name, new_name, merge=False)