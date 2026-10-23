// Copyright (c) 2022, Kulkul and contributors
// For license information, please see license.txt

frappe.ui.form.on('Result Document', {
	refresh: function(frm) {
	
	},
	visa_type: function(frm){
		if (frm.doc.visa_type == "RPTKA"){
			frm.toggle_display("visa",false);
			frm.toggle_display("tka",false);
			frm.toggle_display("no_passport",false);
			frm.toggle_display("jabatan_rptka",false);
			frm.toggle_display("no_kitas",false);
			frm.toggle_display("no_notifikasi",false);
			frm.toggle_display("no_evisa",false);
			frm.toggle_display("customer",true);
			frm.toggle_display("no_rptka",true);
			frm.toggle_display("rptka",false);

		} else {
			frm.toggle_display("rptka",true);
			frm.toggle_display("customer",false);
			frm.toggle_display("no_rptka",false);
			frm.toggle_display("visa",true);
			frm.toggle_display("tka",true);
			frm.toggle_display("no_passport",true);
			frm.toggle_display("jabatan_rptka",true);
			frm.toggle_display("no_kitas",true);
			frm.toggle_display("no_notifikasi",true);
			frm.toggle_display("no_evisa",true);
		}
	},
	visa:function(frm){
		frappe.db.get_value("Visa",frm.doc.visa, "status_rptka").then(function(r){
			if (r.message.status_rptka == "Non-Aktif"){
				frm.toggle_display("rptka",false);
				frm.toggle_display("customer_name",false);
				frm.toggle_display("jabatan_rptka",false);
			} else {
				frm.toggle_display("rptka",true);
				frm.toggle_display("customer_name",true);
				frm.toggle_display("jabatan_rptka",true);
			}
		})
	},
	customer: function(frm){
		frappe.db.get_value("Customer",frm.doc.customer, "customer_name").then(function(r){
			frm.set_value("customer_name",r.message.customer_name)
		})
	},
	rptka: function(frm){
		frm.set_query("jabatan_rptka",function(){
			return {
				query: "kulkul_erp.kulkul_selling.doctype.result_document.result_document.query_jabatan_rptka",
				filters: {
					"rptka": frm.doc.rptka 
				}
			}
		})
	}
});
