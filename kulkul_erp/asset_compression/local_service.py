"""Local-only dispatcher + single burst worker, without enabling unrelated schedulers."""
import time
import fcntl
import os
from pathlib import Path


def run():
    import frappe
    from rq import Worker
    from frappe.utils.background_jobs import get_queue
    from .events import dispatch
    site = frappe.local.site
    if site != "blitz.local":
        raise RuntimeError("Local service is restricted to blitz.local")
    state = Path(frappe.get_site_path("private", "asset_compression"))
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    service_lock = open(state / "local-service.lock", "a")
    fcntl.flock(service_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    (state / "local-service.pid").write_text(str(os.getpid()))
    while True:
        try:
            dispatch()
            queue = get_queue("asset_compression")
            Worker([queue], connection=queue.connection).work(burst=True)
        finally:
            frappe.destroy()
        time.sleep(15)
        frappe.init(site=site)
        frappe.connect()
        frappe.set_user("Administrator")
