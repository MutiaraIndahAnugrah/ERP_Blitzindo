// Copyright (c) 2022, Kulkul and contributors
// For license information, please see license.txt
// frappe.ui.form.on('Detail Order', {
// 	onload : function(frm){
// 		frappe.db.get_doc('Order Form', frm.doc.order_form).then(res => {
// 			if(frm.doc.order_category_hidden != res.order_category || frm.doc.sponsor_company_hidden != res.sponsor_company){
// 				// console.log('res', res)
// 				frappe.model.set_value('Detail Order', frm.doc.name, 'order_category_hidden', res.order_category)
// 				if(frm.doc.order_category_hidden == 'Sponsor'){
// 					frappe.model.set_value('Detail Order', frm.doc.name, 'sponsor_company_hidden', res.sponsor_company)
// 				} else {
// 					frappe.model.set_value('Detail Order', frm.doc.name, 'sponsor_company_hidden', '')
// 				}
// 				frm.save()
// 			}
// 		})
// 	}
// })
frappe.ui.form.on('Detail Order', {
	refresh: function(frm){
		if (frm.doc.order_form){	
			frm.add_custom_button("Order Form",function(){
				frappe.set_route("Form", "Order Form", frm.doc.order_form);
			},"Back To")
		}

		if (frm.doc.reserve_order){	
			frm.add_custom_button("Reserve Order",function(){
				frappe.set_route("Form", "Reserve Order", frm.doc.reserve_order);
			},"Back To")
		}

		if(frm.doc.type == "Visa" && frm.doc.legal_sku_code){
            frm.set_value('legal_sku_code', '')
            cur_frm.refresh_field('legal_sku_code')
        }
		
		if(frm.doc.item_code && frm.doc.type == 'Legal' && !frm.doc.legal_sku_code){
			frappe.db.get_value("Legal SKU Code",frm.doc.item_code,"name").then(function(r){
				// console.log(r.message.name);
				if(r.message.name && r.message.name != frm.doc.legal_sku_code){
					frm.set_value('type', 'Legal')
					frm.set_value('legal_sku_code', r.message.name)
					cur_frm.refresh_field('legal_sku_code')
				}
			})
		}
	},
	item_code: function(frm){
		if(frm.doc.item_code){
			frappe.db.get_value("Legal SKU Code",frm.doc.item_code,"name").then(function(r){
				// console.log(r.message.name);
				if(r.message.name){
					frm.set_value('type', 'Legal')
					frm.set_value('legal_sku_code', r.message.name)
				} else {
					frm.set_value('type', 'Visa')
					frm.set_value('legal_sku_code', '')
				}
				cur_frm.refresh_field('legal_sku_code')
			})
		}
	},
	type(frm){
        // console.log('an')
        if(frm.doc.type == "Visa" && frm.doc.legal_sku_code != ''){
            frm.set_value('legal_sku_code', '')
            cur_frm.refresh_field('legal_sku_code')
        } else if (frm.doc.item_code && frm.doc.type == 'Legal' && !frm.doc.legal_sku_code){
			frappe.db.get_value("Legal SKU Code",frm.doc.item_code,"name").then(function(r){
				// console.log(r.message.name);
				if(r.message.name && r.message.name != frm.doc.legal_sku_code){
					frm.set_value('type', 'Legal')
					frm.set_value('legal_sku_code', r.message.name)
					cur_frm.refresh_field('legal_sku_code')
				}
			})
		}
    },
	onload(frm){
		if(frm.doc.type == "Visa"){
			let address_order_form = frm.doc.order_site_hidden
			let length_details = 0
			if(frm.doc.details && frm.doc.details.length){
				length_details = frm.doc.details.length
			}
			let save = false
			let loop = 0
	
			if((frm.doc.qty - length_details) > 0){
				loop = (frm.doc.qty - length_details)
			}
	
			for(let i = 0; i < loop; i++){
				let row = frappe.model.add_child(frm.doc, "Detail Order Items", "details");
				row.address = address_order_form;
				save = true
			}
			
			if(save){
				frm.save()
			}
			cur_frm.refresh_field('details')
		}
	}
})

frappe.ui.form.on('Detail Order Items', 'details_add', function(frm){
	// frappe.msgprint('<pre>' + JSON.stringify(values, null, 2) + '</pre>');
	let rowCount = frm.doc.details.length
	// console.log(rowCount)
	if(rowCount > frm.doc.qty && frm.doc.type == 'Visa'){
		cur_frm.get_field('details').grid.grid_rows[rowCount - 1].remove();
		frappe.msgprint('Item Quantity and Detail Order Quantity do not match');
	} else {
		frm.save()
	}
});

frappe.ui.form.on('Detail Order Items', {
	form_render : function(frm,cdt,cdn){
		let item = locals[cdt][cdn]
		if(frm.doc.order_site_hidden && !item.address){
			item.address = frm.doc.order_site_hidden
		}
		if(frm.doc.order_category_hidden == 'Sponsor' && item.data_tka){
			item.sponsor_company = frm.doc.sponsor_company_hidden
		}
		frm.refresh_field('details')
	},
	data_tka: function(frm,cdt,cdn){
		let item = locals[cdt][cdn]
		if(frm.doc.order_category_hidden == 'Sponsor'){
			item.sponsor_company = frm.doc.sponsor_company_hidden
		} else {
			item.sponsor_company = ''
		}
	},
	create_tenaga_kerja: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if(!frm.doc.customer){
			frappe.msgprint('Please select customer!')
	 	} else if (!frm.doc.__islocal && row.name){
			let formNewTK = new frappe.ui.Dialog({
				title: 'Enter details',
				fields: [
					{
						label: 'Full Name',
						fieldname: 'full_name',
						fieldtype: 'Data',
						reqd: 1
					},
					{
						label: 'Foreign Name',
						fieldname: 'foreign_name',
						fieldtype: 'Data'
					},
					{
						label: 'Tanggal Lahir',
						fieldname: 'tanggal_lahir',
						fieldtype: 'Date'
					},
					{
						label: 'Residential Address',
						fieldname: 'residential_address',
						fieldtype: 'Data'
					},
					{
						label: 'Notes',
						fieldname: 'notes',
						fieldtype: 'Small Text'
					},
					{
						fieldname: 'column_break_1',
						fieldtype: 'Column Break'
					},
					{
						label: 'No Passport',
						fieldname: 'no_passport',
						fieldtype: 'Data',
						reqd: 1,
						unique: 1
					},
					{
						label: 'Passport Expired Date',
						fieldname: 'passport_expired_date',
						fieldtype: 'Date'
					},
					{
						label: 'Passport Expired Status',
						fieldname: 'passport_expired_status',
						fieldtype: 'Data',
						default: '-'
					},
					{
						label: 'Document Passport',
						fieldname: 'document_passport',
						fieldtype: 'Attach'
					},
					{
						label: 'Document Vaccine',
						fieldname: 'document_vaccine',
						fieldtype: 'Attach'
					},
					{
						label: 'Company',
						fieldname: 'company',
						fieldtype: 'Read Only',
						default: frm.doc.customer,
						reqd: 1
					},
					{
						label: 'Sponsor Company',
						fieldname: 'sponsor_company',
						fieldtype: frm.doc.order_category_hidden == 'Sponsor' &&  frm.doc.sponsor_company_hidden.length > 0 ? 'Read Only' : 'Data',
						default: frm.doc.order_category_hidden == 'Sponsor' ? frm.doc.sponsor_company_hidden : '',
						hidden: frm.doc.order_category_hidden == 'Sponsor' &&  frm.doc.sponsor_company_hidden.length > 0 ? 0 : 1
					},
					{
						label: 'Kewarganegaraan',
						fieldname: 'kewarganegaraan',
						fieldtype: 'Link',
						options: 'Country',
						default: 'China'
					},

				],
				primary_action_label: 'Submit',
				primary_action(values) {
					let expired = 0
					if(values.passport_expired_date){
						let date_input = values.passport_expired_date.split('-')
						expired = (monthDiff(new Date(date_input[2],date_input[1],date_input[0]), new Date()) < 18)
					}
					frappe.call({
						method: "kulkul_erp.kulkul_selling.doctype.detail_order.detail_order.create_tenaga_kerja",
						args: {
							"fields": {
								'full_name' : values.full_name,
								'foreign_name' : values.foreign_name ?? '',
								'no_passport' : values.no_passport,
								'passport_expired_date' : values.passport_expired_date ?? '',
								'document_passport' : values.document_passport ?? '',
								'document_vaccine' : values.document_vaccine ?? '',
								'kewarganegaraan' : values.kewarganegaraan ?? '',
								'notes' : values.notes ?? '',
								'tanggal_lahir' : values.tanggal_lahir ?? '',
								'residential_address' : values.residential_address ?? '',
								'passport_expired_status': expired
							},
							"company": frm.doc.customer,
							"sponsor_company": frm.doc.order_category_hidden == 'Sponsor' ? frm.doc.sponsor_company_hidden : '',
							"row_name": row.name
						},
						callback: function(r) {
							// console.log('Response',r.message);
							// console.log('Doc',frm.doc);
							// console.log(row);
							frappe.model.set_value(cdt,cdn,"data_tka", r.message.name)
							// frappe.model.sync(r.message);
							frm.refresh_field('details');
						}
					})
					// console.log('Dialog',values);
					formNewTK.hide();
				}
			});
			if(!row.__islocal){
				formNewTK.show();
				formNewTK.$wrapper.find("[data-fieldname='passport_expired_status']").prop("hidden", true);
				formNewTK.$wrapper.find("[data-fieldname='passport_expired_status']").prop("readonly", true);
				formNewTK.$wrapper.find('.modal-dialog').addClass("modal-lg");
				formNewTK.$wrapper.find("[data-fieldname='passport_expired_date']").change(function(){
					if($(this).val()){
						let date_input = $(this).val().split('-')
						if(monthDiff(new Date(date_input[2],date_input[1],date_input[0]), new Date()) < 18){
							// console.log(monthDiff(new Date(date_input[2],date_input[1],date_input[0]), new Date()))
							formNewTK.$wrapper.find("[data-fieldname='passport_expired_status']").prop("hidden", false);
							formNewTK.$wrapper.find("[data-fieldname='passport_expired_status']").val("Expired less than 18 months");
							// console.log($(this).val())
						} else {
							formNewTK.$wrapper.find("[data-fieldname='passport_expired_status']").prop("hidden", true);
							formNewTK.$wrapper.find("[data-fieldname='passport_expired_status']").val("");
						}
					}
				})
			} else {
				frappe.msgprint('Save document first!')
			}
		} else {
			frappe.msgprint('Save document first!')
		}
	},
});

function monthDiff(d2, d1) {
    let months;
    months = (d2.getFullYear() - d1.getFullYear()) * 12;
    months -= d1.getMonth();
    months += d2.getMonth();
    return months <= 0 ? 0 : months;
}