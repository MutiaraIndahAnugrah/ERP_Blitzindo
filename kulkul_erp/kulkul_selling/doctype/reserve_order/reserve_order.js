// Copyright (c) 2022, Kulkul and contributors
// For license information, please see license.txt

frappe.ui.form.on('Reserve Order', {
	
	refresh: function(frm) {
		if (frm.doc.docstatus == 1){
			// console.log(frappe.user_roles)
			if (frappe.user.has_role("01. Senior - Sales & Marketing") 
				|| frappe.user.has_role("01. Supervisor - Sales and Marketing") 
				|| frappe.user.has_role("01. Manager - Sales & Marketing")){
				cur_frm.fields_dict.items.grid.update_docfield_property("rate", "read_only", 0)
				cur_frm.fields_dict.order_cost.grid.update_docfield_property("rate", "read_only", 0)
			} else {
				cur_frm.fields_dict.items.grid.update_docfield_property("rate", "read_only", 1)
				cur_frm.fields_dict.order_cost.grid.update_docfield_property("rate", "read_only", 1)
			}
		}
		
		frm.set_query("item_code","items",function(){
			return {
				filters: {
					"is_sales_item":1
				}
			}
		});

		frm.set_query("bank_account", function() {
            return {
                "filters": {
                    "account_type": "Bank",
                    "group_or_ledger": "Ledger"
                }
            };
        });

		frm.set_query("item_code","order_cost",function(){
			return {
				filters: {
					"is_purchase_item":1
				}
			}
		});

		frm.set_query("price_list","order_cost",function(frm,cdt,cdn){
			var row = locals[cdt][cdn];
			return {
				filters: {
					"buying":1,
					"currency": row.currency
				}
			}
		})
	},
	onload: function(frm){
		frm.set_query("sponsor_company", function() {
        return {
            "filters": {
                "customer_group": "Sponsor Company"
            }
        };
    	});
	}
});


frappe.ui.form.on("Order Cost", {
	item_code: function(frm,cdt,cdn){
		var row = locals[cdt][cdn];

		// if (!frm.doc.default_price_list){
		// 	frappe.msgprint("Please input Price List to fetch price")
		// }

		if (row.item_code){
			frappe.db.get_doc("Item", row.item_code).then(function(r){
				// console.log(r)
				frappe.model.set_value(cdt,cdn, "item_name",r.item_name);
				frappe.model.set_value(cdt,cdn, "price_list",r.item_defaults[0].default_price_list);

				frappe.db.get_value("Item Price", {"item_code":row.item_code,"price_list":r.item_defaults.default_price_list},["price_list_rate","currency"]).then(function(rr){
					frappe.model.set_value(cdt,cdn,"rate",rr.message.price_list_rate);
					frappe.model.set_value(cdt,cdn,"currency",rr.message.currency);
					if (!row.qty) frappe.model.set_value(cdt,cdn,"qty",1);
				})
			})



		}
	},qty: function(frm,cdt,cdn){
		var row = locals[cdt][cdn];

		if (row.qty > 0 && row.rate > 0)
		frappe.model.set_value(cdt,cdn,"amount", row.qty * row.rate)
		
	},
	rate: function(frm,cdt,cdn){

		var row = locals[cdt][cdn];
		if (row.qty > 0 && row.rate > 0)
		frappe.model.set_value(cdt,cdn,"amount", row.qty * row.rate)
	},
	price_list: function(frm,cdt,cdn){
		var row = locals[cdt][cdn];
		frappe.db.get_value("Item Price", {"item_code":row.item_code,"price_list":row.price_list},"price_list_rate").then(function(r){
			// console.log(r.message)
			frappe.model.set_value(cdt,cdn,"rate",r.message.price_list_rate);
		})
	},
	amount: function(frm,cdt,cdn){
		//
	},
	order_cost_remove: function(frm,cdt,cdn){
		//
	},
})

frappe.ui.form.on('Order Form Items', {
	
	items_remove: function(frm,cdt,cdn){
	
	},
	item_code: function(frm,cdt,cdn){
		var row = locals[cdt][cdn];

		// if (!frm.doc.default_price_list){
		// 	frappe.msgprint("Please input Price List to fetch price")
		// }

		if (row.item_code){

			frappe.db.get_doc("Item", row.item_code).then(function(r){
				frappe.model.set_value(cdt,cdn, "item_name",r.item_name);
				frappe.model.set_value(cdt,cdn, "price_list",r.item_defaults[0].default_price_list);

				frappe.db.get_value("Item Price", {"item_code":row.item_code,"price_list":r.item_defaults.default_price_list},["price_list_rate","currency"]).then(function(rr){
					frappe.model.set_value(cdt,cdn,"rate",rr.message.price_list_rate);
					frappe.model.set_value(cdt,cdn,"currency",rr.message.currency);
					if (!row.qty) frappe.model.set_value(cdt,cdn,"qty",1);
				})
			})


			// frappe.db.get_value("Item", row.item_code,"item_name").then(function(r){
			// 	frappe.model.set_value(cdt,cdn, "item_name",r.message.item_name);
			// 	if (!row.qty) frappe.model.set_value(cdt,cdn, "qty",1);

			// 	frappe.db.get_value("Item Price", {"item_code":row.item_code,"price_list":frm.doc.default_price_list},"price_list_rate").then(function(r){
			// 		frappe.model.set_value(cdt,cdn,"rate",r.message.price_list_rate);
			// 	})
			// })
		}
	},

	qty: function(frm,cdt,cdn){
		var row = locals[cdt][cdn];

		if (row.qty > 0 && row.rate > 0)
		frappe.model.set_value(cdt,cdn,"amount", row.qty * row.rate)
		//

	},
	rate: function(frm,cdt,cdn){

		var row = locals[cdt][cdn];
		if (row.qty > 0 && row.rate > 0)
		frappe.model.set_value(cdt,cdn,"amount", row.qty * row.rate)
		//
	},
	create_detail_order: function(frm, cdt, cdn) {

		var row = locals[cdt][cdn];
		if (!frm.doc.__islocal && !row.detail_order){
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
					"doc_type": frm.doc.doctype,
					"site" : row.site
				},
				callback: function(r) {
					// console.log(r.message);
					// console.log(frm.doc);
					frappe.model.set_value(cdt,cdn,"detail_order", r.message.name)
					// frappe.model.sync(r.message);
					frm.refresh();
				}
			})
		} else if(frm.doc.__islocal) {
			frappe.throw('Save document first!')
		} else {
			frappe.throw('Detail Order already created!')
		}
	},
	add_to_cost: function(frm,cdt,cdn){
		var row = locals[cdt][cdn];

		if(frm.doc.docstatus == 1){
			frappe.throw('Can\'t add to cost Submitted document!')
		}

		frappe.call({
			method:"kulkul_erp.kulkul_selling.doctype.reserve_order.reserve_order.add_to_cost",
			args : {
				"item_code":row.item_code,
				"site":row.site,
				"qty": row.qty,
				"rate": row.rate,
				"order_type": row.type
			},
			callback: function(r){
				// frm.save()
				r.message.forEach(function(item){
					let oc_items = frm.doc.order_cost
					let ignoreItems = true
					// console.log(oc_items)
					// console.log('detail order',row.detail_order)
					for (let prop in oc_items){
						if (oc_items[prop]['item_code'] === item["item_code"] &&
							oc_items[prop]['price_list'] === item["price_list"] &&
							oc_items[prop]['site'] === item["site"] &&
							oc_items[prop]['type'] === item["type"] &&
							oc_items[prop]['detail_order'] === row.detail_order &&
							oc_items[prop]['currency'] === item["currency"]){
								ignoreItems = false
								frappe.msgprint('Duplicate Order Cost Item ' + item["item_code"])
						}
					}
					if(ignoreItems){
						var child = frm.add_child("order_cost");
						child.item_code = item["item_code"];
						child.item_name = item["item_name"];
						child.qty = item["qty"];
						child.rate = item["rate"];
						child.amount = item["amount"];
						child.site = item["site"];
						child.type = item["type"];
						child.currency = item["currency"];
						child.price_list = item["price_list"];
						child.detail_order = row.detail_order;
						child.from_bundle = row.name;
					}
				})
				if (frappe.user.has_role("01. Staff - Sales & Marketing") && !frappe.user.has_role("System Manager")){
					cur_frm.fields_dict.order_cost.grid.set_column_disp("rate",false);
					cur_frm.fields_dict.order_cost.grid.set_column_disp("rate",false);
					cur_frm.fields_dict.order_cost.grid.set_column_disp("amount",false);
				}
				cur_frm.refresh_field("order_cost")
				// frm.save()
			}
		})

	}
});