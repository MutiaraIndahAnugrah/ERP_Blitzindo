frappe.listview_settings['Tenaga Kerja'] = {
	get_indicator: function (doc) {
		
		let future_date = frappe.datetime.add_months(frappe.datetime.nowdate(),18);

	

		if (doc.passport_expired_date < frappe.datetime.nowdate()){
			return [__("Expired"), "red", "passport_expired_date,>,"+frappe.datetime.nowdate()];
			
		} else if (doc.passport_expired_date < future_date){
			return [__("Expired less than 18 months"), "red", "passport_expired_date,<,"+future_date];
		}
	}
}