// Copyright (c) 2022, Kulkul and contributors
// For license information, please see license.txt


frappe.ui.form.on('Modify Document', {
	refresh(frm){
		frm.set_read_only();
		frm.disable_save();

		frm.add_custom_button(__("Submit"), 
				function(){
					if(!frappe.user.has_role('Administrator')){
						frappe.throw('Only Administrator can use this Doctype!')
					}
					if(frm.doc.action && frm.doc.doctype_target && frm.doc.id_document){
						let rand = Math.floor(Math.random() * 1000)
						frappe.prompt([
							{'fieldname': 'hidden_rand', 'fieldtype': 'Data', 'label': `Hidden Rand`, 'hidden': 1, 'default' : rand},
							{'fieldname': 'hidden_action', 'fieldtype': 'Text', 'label': `Hidden Action`, 'hidden': 1, 'default' : frm.doc.action},
							{'fieldname': 'hidden_ids', 'fieldtype': 'Text', 'label': `Hidden Ids`, 'hidden': 1, 'default' : frm.doc.id_document},
							{'fieldname': 'hidden_doctype_target', 'fieldtype': 'Data', 'label': `Hidden Doctype`, 'hidden': 1, 'default' : frm.doc.doctype_target},
							{'fieldname': 'confirm', 'fieldtype': 'Data', 'label': `Ketik <b>${rand}</b> untuk melanjutkan`, 'reqd': 1},
							{'fieldname': 'action', 'fieldtype': 'Data', 'label': `Action`, 'default' : frm.doc.action, 'read_only': 1},
							{'fieldname': 'doctype_target_preview', 'fieldtype': 'Data', 'label': `Doctype`, 'default' : frm.doc.doctype_target, 'read_only': 1},
							{'fieldname': 'list', 'fieldtype': 'Text', 'label': 'ID Dokumen', 'read_only': 1, 'default' : frm.doc.id_document}
						],
						function(values){
							if(values.confirm == values.hidden_rand){
								let ids_array = values.hidden_ids.split('\n')
								let new_ids_array = []
								ids_array.forEach((val) => {
									if(val.trim() != ''){
										new_ids_array.push(val.trim())
									}
								})
								if(new_ids_array.length < 1){
									frappe.throw('ID Document is mandatory!')
								}
								// console.log(values.hidden_action, new_ids_array, values.hidden_doctype_target)
								frappe.call({
									method:"kulkul_erp.kulkul_erp.doctype.modify_document.modify_document.execute_docs",
									args : {
										action : values.hidden_action,
										ids : new_ids_array,
										doctype_target : values.hidden_doctype_target
									},
									callback: function(r){
										if(r.message){
											msgprint('Success Modify Document')
										} else {
											frappe.throw('Failed Modify Document')
										}
									}
								})
							} else {
								frappe.throw('Incorrect Confirmation!')
							}
						},
						'Konfirmasi Modifikasi Dokumen',
						'Confirm'
						)
					} else {
						frappe.throw('Fill all mandatory fields!')
					}
			});
	},
	validate(frm){
		
	}
});


