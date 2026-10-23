frappe.ui.form.on("Quotation", {
	refresh: function(frm){
		if (frm.doc.docstatus == 1 && frm.doc.valid_till >= frappe.datetime.nowdate()){
			if(frm.doc.__islocal){
				frappe.throw('Save document first!')
			} else {
				frm.add_custom_button(__("Order Form"), 
					function(){
						frappe.model.open_mapped_doc({
							method: "kulkul_erp.kulkul_selling.doctype_functions.quotation.create_order_form",
							frm: cur_frm
						})
					},__("Create"));
			}
		}
		
		if (frappe.user.has_role("Editor - Quotation") || frm.doc.docstatus === 0){
			frm.add_custom_button(__("Product Bundle"), function(){
				erpnext.utils.map_current_doc({
					method: "kulkul_erp.kulkul_selling.doctype_functions.quotation.get_product_bundle",
					source_doctype: "Product Bundle",
					target: cur_frm,
					setters: {
						description : me.frm.doc.description
					},
					get_query_filters: {
						
					}
				})
			},__("Get Items From"));
		}
		
		if(frm.doc.__islocal){
			cur_frm.set_value('valid_till', frappe.datetime.add_months(frm.doc.transaction_date, 12))
		}
	},
	valid_till(frm){
		if(frm.doc.valid_till >= frappe.datetime.nowdate()){
			cur_frm.set_value('quotation_status', 'Active')
		} else {
			cur_frm.set_value('quotation_status', 'Expired')
		}
	},
	transaction_date(frm){
		cur_frm.set_value('valid_till', frappe.datetime.add_months(frm.doc.transaction_date, 12))
	},
	items_add: function(frm){
		// console.log(frappe.user_roles)
		let rowCount = frm.doc.items.length
	    if (!frappe.user.has_role("Editor - Quotation") && frm.doc.docstatus === 1){
			cur_frm.get_field('items').grid.grid_rows[rowCount - 1].remove();
	        frappe.throw("Only Supervisor/Manager Sales & Marketing or User with role Editor - Quotation can add items when doc status is Deal!")
	    }
	},
})