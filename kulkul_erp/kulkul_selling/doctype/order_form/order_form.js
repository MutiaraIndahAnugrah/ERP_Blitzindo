// Copyright (c) 2022, Kulkul and contributors
// For license information, please see license.txt

frappe.ui.form.on('Order Form', {
	refresh: function(frm) {
		if (frm.doc.docstatus == 1){
			// console.log(frappe.user_roles)
			if (frappe.user.has_role("01. Senior - Sales & Marketing") || frappe.user.has_role("01. Supervisor - Sales and Marketing")){
				cur_frm.fields_dict.items.grid.update_docfield_property("rate", "read_only", 0)
			} else {
				cur_frm.fields_dict.items.grid.update_docfield_property("rate", "read_only", 1)
			}

			// frm.add_custom_button(__("Reserve Order"), 
			// 	function(){
			// 		frappe.model.open_mapped_doc({
			// 			method: "kulkul_erp.kulkul_selling.doctype.order_form.order_form.create_reserve_order",
			// 			frm: cur_frm
			// 		})
			// },__("Create"));

			// frm.add_custom_button(__("Customer"), function () {
			// 	frappe.model.open_mapped_doc({
			// 		method: "kulkul_erp.kulkul_selling.doctype.order_form.order_form.make_customer",
			// 		frm: cur_frm
			// 	});
			// }, __("Create"));
		}

		if (frm.doc.docstatus == 0){
			cur_frm.add_custom_button(__("Quotation"), 
				function(){
					if(frm.doc.__islocal){
						frm.save()
					}
					erpnext.utils.map_current_doc({
						method: "kulkul_erp.kulkul_selling.doctype_functions.quotation.create_order_form",
						source_doctype: "Quotation",
						target: cur_frm,
						setters: [
							{
								label: "Customer",
								fieldname: "party_name",
								fieldtype: "Link",
								options: "Customer",
								default: me.frm.doc.customer
							},
							{
								label: "Contact Display",
								fieldname: "contact_display",
								fieldtype: "Link",
								options: "Contact",
								hidden: 1
							},
						],
						get_query_filters: {
							status: ["not in", ["Lost", "Closed"]],
							workflow_state: 'Deal',
							order_type: me.frm.doc.order_type,
							company: me.frm.doc.company,
							quotation_to: "Customer",
							valid_till: ['>=', frappe.datetime.nowdate()]
						},
					})
			},__("Get items from"));

			if(frm.doc.order_type && frm.doc.order_type !== ''){
				let triggerSave = false
				frm.doc.items.forEach((val) => {
					if(frm.doc.order_type !== val.type){
						val.type = frm.doc.order_type
						triggerSave = true
					}
				})
				frm.refresh_field('items')
				if(triggerSave){
					frm.save()
				}
			}
		}

		if(frm.doc.docstatus == 2){
			$('button.btn.btn-primary.btn-sm.primary-action[data-label="Amend"]').remove()
			cur_frm.remove_custom_button("Amend")

			frm.add_custom_button(__("Update"), () => {
				frappe.confirm(
					'Are you sure to Update this Document?',
					function(){
						frappe.call({
							method:"kulkul_erp.kulkul_selling.doctype.order_form.order_form.update_document_to_draft",
							args : {
								name : frm.doc.name
							},
							callback: function(r){
								if(r.message){
									msgprint('Success Update Document. Page will automatically refresh in 3 seconds.')
									setTimeout(() => {
										location.reload();
									}, 3000)
								} else {
									frappe.throw('Failed Update Document')
								}
							}
						})
					},
					function(){
						
					}
				)
			}).addClass("btn-primary");;
		}

		frm.set_query("item_code","items",function(){
			return {
				filters: {
					"is_sales_item":1
				}
			}
		})
		
	},
	validate: function(frm){
		if(frm.doc.items){
			frm.doc.items.forEach(function(row){
				frappe.db.get_value("Item",row.item_code,"item_name").then(function(r){
					row.item_name = r.message.item_name;
					row.amount = row.qty * row.rate;
					if(frm.doc.order_type && frm.doc.order_type !== row.type){
						row.type = frm.doc.order_type;
					}
				})
			})
		} else {
			// frappe.msgprint('Order Items can\'t be empty!')
			// frappe.validated = false;
		}
	},

	order_type(frm){
		if(frm.doc.order_type && frm.doc.order_type !== ''){
			let triggerSave = false
			frm.doc.items.forEach((val) => {
				if(frm.doc.order_type !== val.type){
					val.type = frm.doc.order_type
					triggerSave = true
				}
			})
			frm.refresh_field('items')
			if(triggerSave){
				frm.save()
			}
		}
	},

	onload(frm){
		if(frm.doc.docstatus == 2){
			$('button.btn.btn-primary.btn-sm.primary-action[data-label="Amend"]').remove()
			cur_frm.remove_custom_button("Amend")
		}
	}
});

frappe.ui.form.on("Order Form Items",{
	item_code: function(frm,cdt,cdn){
		var row = locals[cdt][cdn];

		if (!frm.doc.default_price_list){
			frappe.msgprint("Please input Default Price List to fetch price")
		}

		if (row.item_code){
			frappe.db.get_doc("Item", row.item_code).then(function(r){
				frappe.model.set_value(cdt,cdn, "item_name",r.item_name);
				frappe.model.set_value(cdt,cdn, "price_list",r.item_defaults[0].default_price_list);

				frappe.db.get_value("Item Price", {"item_code":row.item_code,"price_list":r.item_defaults.default_price_list,"selling":1},["price_list_rate","currency"]).then(function(rr){
					frappe.model.set_value(cdt,cdn,"rate",rr.message.price_list_rate);
					frappe.model.set_value(cdt,cdn,"currency",rr.message.currency);
					if (!row.qty) frappe.model.set_value(cdt,cdn,"qty",1);
				})
			})
		}
	},
	qty: function(frm,cdt,cdn){
		var row = locals[cdt][cdn];

		if (row.qty > 0 && row.rate > 0)
		frappe.model.set_value(cdt,cdn,"amount", row.qty * row.rate)
		frm.save()
	},
	rate: function(frm,cdt,cdn){

		var row = locals[cdt][cdn];
		if (row.qty > 0 && row.rate > 0)
		frappe.model.set_value(cdt,cdn,"amount", row.qty * row.rate)
		frm.save()
	},
	items_add: function(frm){
		// console.log(frappe.user_roles)
		let rowCount = frm.doc.items.length
	    if (!frappe.user.has_role("01. Manager - Sales & Marketing")){
			cur_frm.get_field('items').grid.grid_rows[rowCount - 1].remove();
	        frappe.throw("Can't add row manually, please use Get Items from Quotation instead!")
	    } else {
			if(frm.doc.order_type && frm.doc.order_type !== ''){
				frm.doc.items.forEach((val) => {
					if(frm.doc.order_type !== val.type){
						val.type = frm.doc.order_type
					}
				})
				frm.refresh_field('items')
			}
			frm.save()
	    }
	},
	site(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		if(row.site && row.site != ''){
			frm.save()
		}
	},
	create_detail_order: function(frm, cdt, cdn) {

		var row = locals[cdt][cdn];
		if(!row.site){
			frappe.msgprint('Please select Site!')
		} else if(!row.item_code){
			frappe.msgprint('Please select Item first!')
		} else if(!frm.doc.customer){
			frappe.msgprint('Please select Customer!')
		} else if(frm.doc.__islocal === 1 || frm.doc.__unsaved === 1) {
			frappe.msgprint('Save document first!')
		} else if (row.detail_order){
			frappe.throw('Detail Order already created!')
		} else {
			let sponsor_company = null
			if(frm.doc.sponsor_company){
				sponsor_company = frm.doc.sponsor_company
			}
			frappe.call({
				method: "kulkul_erp.kulkul_selling.doctype.detail_order.detail_order.create_detail_order",
				args: {
					"item_code":row.item_code,
					"item_name":row.item_name,
					"order_type":row.type,
					"qty":row.qty,
					"rate":row.rate,
					"amount":row.amount,
					"customer": frm.doc.customer,
					"customer_name": frm.doc.customer_name,
					"parent_name": frm.doc.name,
					"row_name":row.name,
					"type":row.order_form_type,
					"doc_type": frm.doc.doctype,
					"order_category": frm.doc.order_category,
					"sponsor_company": sponsor_company ?? null,
					"site": row.site
				},
				callback: function(r) {
					frappe.model.set_value(cdt,cdn,"detail_order", r.message.name)
					frm.refresh();
					frm.save();
					setTimeout(() => {
						frappe.set_route("Form", "Detail Order", r.message.name)
					}, 1100)
				}
			})
		}
	},
})