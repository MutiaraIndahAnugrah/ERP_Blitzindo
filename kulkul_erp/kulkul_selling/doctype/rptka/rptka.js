// Copyright (c) 2022, Kulkul and contributors
// For license information, please see license.txt

frappe.ui.form.on('RPTKA', {
	refresh: function(frm) {

	},
	validate: function(frm){
		
			var total = 0;
			var sisa = 0;
			frm.doc.data_jabatan_rptka.forEach(function(data){
				total = data.jumlah_jabatan + total;
				sisa = data.jumlah_jabatan_terpakai + sisa;
			})
			frm.set_value('jumlah_rptka', total);
			frm.set_value('rptka_terpakai', sisa);

	}
});

frappe.ui.form.on('Data Jabatan RPTKA', {
	jumlah_jabatan: function(frm,cdt,cdn){
		var row = locals[cdt][cdn];
		var terpakai = row.jumlah_jabatan_terpakai;

		if (!terpakai) terpakai = 0;
		
		frappe.model.set_value(cdt,cdn,"jumlah_jabatan_sisa",row.jumlah_jabatan - terpakai);
	}
});