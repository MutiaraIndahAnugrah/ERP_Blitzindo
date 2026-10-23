// Copyright (c) 2022, Kulkul and contributors
// For license information, please see license.txt

frappe.ui.form.on('Voucher Type Accessible', {
	refresh: function(frm) {
		frm.set_read_only();
		frm.disable_save();
	}
});
