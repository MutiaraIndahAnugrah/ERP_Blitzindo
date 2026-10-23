import frappe
import os

# kulkul_erp.kulkul_erp.custom_file.backup_attachment
def backup(doc):

	# /home/ubuntu/frappe-bench/sites/103.150.99.235/
	original_path = "/home/ubuntu/frappe-bench/sites/103.150.99.235/"
	is_private = "" if doc.is_private else "public"
	extra_storage_path = "/home/ubuntu/data_files_erp/"

	src_path = "{}{}{}".format(original_path, is_private, doc.file_url).replace(" ","\ ").replace("(","\(").replace(")","\)").replace("&","\&").replace("[","\[").replace("]","\]")

	target_path = "{}{}{}".format(extra_storage_path, is_private, doc.file_url).replace(" ","\ ").replace("(","\(").replace(")","\)").replace("&","\&").replace("[","\[").replace("]","\]")
	
	# 1. move file to block storage path
	# os.rename(src_path, target_path)
	# print("{} >> {} ".format(src_path, target_path))
	
	os.system("mv {} {}".format(src_path,target_path))
	# os.system("cp {} {}".format(src_path,target_path))
	# os.system("mv {} {}".format(target_path,src_path))
	
	# 3. create symlink file to block storage path
	os.system("ln -s {} {}".format(target_path, src_path))

def manual():
	doc = frappe.get_doc("File","0c06306b3d")
	backup(doc)

def backup_attachments():
	list_file = frappe.db.sql("""
			SELECT
				`name`
			FROM `tabFile`
			where DATE(modified) = DATE_ADD(DATE(NOW()), INTERVAL -1 DAY)
			AND file_url != ""

		""",as_dict=1)

	for x in list_file:
		try:
			doc = frappe.get_doc("File",x.name)
			backup(doc)
		except:
			pass

def spec_char():
	spec_char = """ !"#$&'()*,;<>?[]\^`{|} """