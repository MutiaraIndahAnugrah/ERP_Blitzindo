# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe

def get_context(context):

	context.blogs = frappe.get_all('Blog Post', 
						fields=['title', 'blog_intro', 'route','meta_image','blog_category','published_on'], 
						filters = {'published': 1},
						order_by='creation desc',
						limit=3)

	context.testimonials = frappe.get_all('Testimonial Website',fields=['customer_name','customer_company_name','reviews','customer_company_logo'], order_by='creation desc')
	context.testimonial_clients = frappe.get_all('Testimonial Website Clients',fields=['company_name','company_logo'], order_by='creation desc')
	context.slider_bottom = frappe.get_all('Website Slider',fields=['title','image'],filters={'type':'Bottom'}, order_by='creation desc')
	context.slider_top = frappe.get_all('Website Slider',fields=['*'],filters={'type':'Top'}, order_by='creation desc')

	context.card_working_visa = frappe.get_last_doc('Website Service Content',filters={'type':'Working Visa'})
	context.card_business_visa = frappe.get_last_doc('Website Service Content',filters={'type':'Business Visa'})
	context.card_company_establishment = frappe.get_last_doc('Website Service Content',filters={'type':'Company Establishment'})

	context.card_top = frappe.get_doc('Website Card Top')
	context.section_setting = frappe.get_doc('Website Section Setting')