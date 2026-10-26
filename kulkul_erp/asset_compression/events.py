"""Durable outbox: the upload only inserts a job, with no compression or Redis call."""
import frappe

JOB = "Asset Compression Job"


def enabled():
    from frappe.utils import cint
    return bool(cint(frappe.conf.get("asset_compression_enabled")))


def after_insert(doc, method=None):
    if not enabled() or doc.is_folder or not doc.file_url or not doc.file_url.startswith(("/files/", "/private/files/")):
        return
    if not frappe.db.table_exists(JOB):
        return
    frappe.db.savepoint("asset_compression_outbox")
    try:
        frappe.get_doc({"doctype": JOB, "file": doc.name, "status": "Pending"}).insert(ignore_permissions=True)
    except Exception:
        frappe.db.rollback(save_point="asset_compression_outbox")
        # Failing bookkeeping must not roll back an otherwise successful upload.
        frappe.logger("asset_compression").error("Could not record compression task")


def dispatch():
    """Scheduler/cron dispatcher; heavy work only runs on asset_compression queue."""
    if not enabled():
        return
    from frappe.utils import add_to_date, now_datetime
    cutoff = add_to_date(now_datetime(), minutes=-30)
    rows = frappe.db.sql("""select name from `tabAsset Compression Job`
        where status='Pending' or (status in ('Queued','Processing','Failed')
        and modified < %s and attempts < 3) order by creation limit 20""", (cutoff,), as_dict=True)
    for row in rows:
        try:
            frappe.enqueue("kulkul_erp.asset_compression.worker.process", queue="asset_compression",
                           timeout=180, job_name="asset-compression:" + row.name, job=row.name)
            # Only mark after enqueue succeeds. Duplicate delivery is safe under the worker lock.
            frappe.db.sql("""update `tabAsset Compression Job` set status='Queued',modified=now()
                where name=%s and status in ('Pending','Failed','Queued','Processing')""", row.name)
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            frappe.logger("asset_compression").error("Compression dispatch unavailable; task retained")
            break
