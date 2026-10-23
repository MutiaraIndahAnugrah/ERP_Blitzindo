# Copyright (c) 2022, Kulkul and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ResultDocument(Document):
	def validate(self):
		self.update_work_order_item()

	def after_insert(self):
		if self.visa_type == "RPTKA" and self.docstatus == 0:
			rptka = frappe.new_doc("RPTKA")
			rptka.nomor_rptka = self.no_rptka
			rptka.customer = self.customer
			rptka.customer_name = self.customer_name
			rptka.tanggal_terbit = self.issue_date
			rptka.tanggal_expired = self.expired_date 
			rptka.save(ignore_permissions=True)

			self.rptka = self.no_rptka
			self.submit()

	def on_submit(self):
		frappe.db.set_value("Result Document", self.name, "status", 'Completed')
		if self.work_order_detail:
			row = frappe.get_doc("Result of Work Item", self.work_order_detail)
			row.db_set("status", 'Completed')

		if self.visa_type == "Visa":
			if self.rptka:
				rptka = frappe.get_doc("RPTKA", self.rptka)

				rptka_terpakai = 0
				for row in rptka.data_jabatan_rptka:
					if row.nama_jabatan == self.jabatan_rptka:
						row.jumlah_jabatan_terpakai += 1
						row.jumlah_jabatan_sisa -= 1
						rptka_terpakai+= 1

				if rptka_terpakai > rptka.jumlah_rptka:
					frappe.throw("Sisa jabatan tidak mencukupi") 

				rptka.rptka_terpakai += rptka_terpakai
				
				# update Data Pengguna RPTKA
				if self.visa_type == "Visa":
					tka = frappe.get_doc("Tenaga Kerja",self.tka)
					rptka.append("data_pengguna_rptka",{
							"customer": tka.company,
							"no_passport": tka.no_passport,
							"nama_latin": tka.full_name,
							"visa": self.visa,
							"tanggal_awal_visa": self.issue_date,
							"tanggal_expired_visa": self.expired_date,
							"jabatan": self.jabatan_rptka

						})

				rptka.save(ignore_permissions=True)



	def on_cancel(self):
		frappe.db.set_value("Result Document", self.name, "status", 'In-Progress')
		if self.work_order_detail:
			row = frappe.get_doc("Result of Work Item", self.work_order_detail)
			row.db_set("status", 'In-Progress')

		if self.rptka:
			rptka = frappe.get_doc("RPTKA", self.rptka)
			rptka_terpakai = 0
			for row in rptka.data_jabatan_rptka:
				if row.nama_jabatan == self.jabatan_rptka:
					row.jumlah_jabatan_terpakai -= 1
					row.jumlah_jabatan_sisa += 1
			rptka.rptka_terpakai -= rptka_terpakai
			rptka.save(ignore_permissions=True)

			if self.visa_type != "RPTKA":
				tka = frappe.get_doc("Tenaga Kerja",self.tka)


				frappe.db.sql("""
						DELETE FROM `tabData Pengguna RPTKA` where parent = "{}" and nama_latin = "{}" and no_passport = "{}" and "jabatan" = "{}"
					""".format(self.rptka, tka.full_name, tka.no_passport, self.jabatan_rptka))


	
	def on_update(self):
		if self.work_order_detail:
			row = frappe.get_doc("Result of Work Item", self.work_order_detail)
			row.db_set("status", self.status)

	def update_work_order_item(self):
		if self.work_order_detail:
			row = frappe.get_doc("Result of Work Item", self.work_order_detail)
			row.db_set("status", self.status if self.status else '')
			row.db_set("type", self.type if self.type else '')
			row.db_set("visa_type", self.visa_type if self.visa_type else '')
			row.db_set("jenis_visa", self.visa if self.visa else '')
			row.db_set("legal_type", self.jenis_legal if self.jenis_legal else '')
			row.db_set("rptka", self.rptka if self.rptka else '')
			row.db_set("no_rptka", self.no_rptka if self.no_rptka else '')
			if self.issue_date:
				row.db_set("issue_date", self.issue_date if self.issue_date else '')
			
			if self.expired_date:
				row.db_set("expired_date", self.expired_date if self.expired_date else '')

			row.db_set("result_document", self.result_document if self.result_document else '')

@frappe.whitelist()
def query_jabatan_rptka(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""
			SELECT
				`nama_jabatan`, CONCAT("sisa jabatan=",`jumlah_jabatan_sisa`)
			FROM `tabData Jabatan RPTKA` where parent = "{}" AND jumlah_jabatan_sisa > 0
		""".format(filters.get("rptka")))