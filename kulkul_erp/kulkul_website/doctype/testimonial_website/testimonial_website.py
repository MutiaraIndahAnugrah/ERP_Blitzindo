# Copyright (c) 2022, Kulkul and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TestimonialWebsite(Document):
	pass

def replace_naming(doc,method):
	doc.naming_series = "TTWS-.YY.-.#####"
