"""Background-only processing with per-URL locking and a recoverable filesystem swap."""
import fcntl
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from urllib.parse import unquote

import frappe

from .engine import isolated
from .events import JOB, enabled


def digest(path):
    hasher = hashlib.md5()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def file_path(url):
    root = Path(frappe.get_site_path()).resolve()
    relative = unquote(url)
    if relative.startswith("/private/files/"):
        base, name = root / "private/files", relative[len("/private/files/"):]
    elif relative.startswith("/files/"):
        base, name = root / "public/files", relative[len("/files/"):]
    else:
        raise ValueError("non_local_file")
    path = base / name
    # External storage and symlinks require a separate storage adapter.
    if not name or Path(name).name != name or path.is_symlink() or base.resolve() != base or not path.is_file():
        raise ValueError("unavailable_or_nonstandard_storage")
    if path.resolve().parent != base:
        raise ValueError("unsafe_file_path")
    return path


def status(job, state, reason, original=None, result=None):
    values = {"status": state, "reason": reason}
    if original is not None:
        values["original_bytes"] = original
    if result is not None:
        values["result_bytes"] = result
    frappe.db.set_value(JOB, job, values)


def finish_swap(job, url, path, journal):
    """Idempotent replay after a worker crash between rename and DB commit."""
    record = json.loads(journal.read_text())
    backup = journal.with_suffix(".original")
    current = digest(path)
    if current == record["old"]:
        # Rename never occurred, or a failed attempt restored the original.
        backup.unlink(missing_ok=True)
        journal.unlink()
        return False
    if current != record["new"]:
        raise ValueError("recovery_requires_review")
    references = frappe.db.sql("select name from `tabFile` where file_url=%s for update", url, as_dict=True)
    frappe.db.sql("update `tabFile` set content_hash=%s,file_size=%s where file_url=%s",
                  (record["new"], path.stat().st_size, url))
    status(job, "Done", record["reason"], record["original_bytes"], path.stat().st_size)
    frappe.db.commit()
    for reference in references:
        frappe.clear_document_cache("File", reference.name)
    backup.unlink(missing_ok=True)
    journal.unlink()
    return True


def install_result(job, url, source, result, old_hash, reason, state_dir):
    # Hold matching metadata rows while swapping; all shared URL references follow the same bytes.
    frappe.db.sql("select name from `tabFile` where file_url=%s for update", url)
    if not source.is_file() or source.is_symlink() or digest(source) != old_hash:
        raise ValueError("source_changed")
    journal = state_dir / (job + ".json")
    backup = journal.with_suffix(".original")
    if backup.exists():
        if digest(backup) != old_hash:
            raise ValueError("recovery_requires_review")
        backup.unlink()
    os.link(source, backup)
    record = {"old": old_hash, "new": digest(result), "reason": reason,
              "original_bytes": source.stat().st_size}
    pending = journal.with_suffix(".pending")
    with open(pending, "w", encoding="utf8") as stream:
        json.dump(record, stream)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, journal)
    os.chmod(result, source.stat().st_mode & 0o777)
    with open(result, "rb") as stream:
        os.fsync(stream.fileno())
    os.replace(result, source)
    try:
        finish_swap(job, url, source, journal)
    except Exception:
        frappe.db.rollback()
        # Restore only if the metadata transaction did not commit.
        stored = frappe.db.get_value("File", {"file_url": url}, "content_hash")
        if stored != record["new"] and backup.exists() and digest(source) == record["new"]:
            os.replace(backup, source)
            journal.unlink(missing_ok=True)
        # Otherwise keep the recovery journal for the next attempt.
        raise


def process(job):
    if not enabled() or not frappe.db.exists(JOB, job):
        return
    row = frappe.get_doc(JOB, job)
    file = frappe.db.get_value("File", row.file, ["file_url", "is_private"], as_dict=True)
    if not file:
        status(job, "Skipped", "file_removed")
        return
    state_dir = Path(frappe.get_site_path("private", "asset_compression")).resolve()
    state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(state_dir, 0o700)
    key = hashlib.sha256(file.file_url.encode()).hexdigest()
    with open(state_dir / (key + ".lock"), "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        try:
            path = file_path(file.file_url)
            journal = state_dir / (job + ".json")
            if journal.exists() and finish_swap(job, file.file_url, path, journal):
                return
            row.reload()
            if row.status in {"Done", "Skipped"} or row.attempts >= 3:
                return
            frappe.db.set_value(JOB, job, {"status": "Processing", "attempts": row.attempts + 1})
            frappe.db.commit()
            size = path.stat().st_size
            target = int(frappe.conf.get("asset_compression_target_bytes") or 2 * 1024**2)
            maximum = int(frappe.conf.get("asset_compression_max_input_bytes") or 100 * 1024**2)
            if size <= target:
                status(job, "Skipped", "already_small", size, size)
                return
            if size > maximum:
                status(job, "Skipped", "processing_input_limit", size, size)
                return
            if shutil.disk_usage(state_dir).free < size * 3 + 64 * 1024**2:
                raise OSError("insufficient_processing_space")
            old_hash = digest(path)
            with tempfile.TemporaryDirectory(prefix="work-", dir=state_dir) as work:
                source = Path(work) / ("input" + path.suffix)
                result = Path(work) / ("output" + path.suffix)
                shutil.copyfile(path, source)
                reason = isolated(source, result, target)
                if not result.exists() or result.stat().st_size >= size:
                    status(job, "Skipped", reason, size, size)
                    return
                if not enabled():
                    status(job, "Skipped", "disabled_before_swap", size, size)
                    return
                install_result(job, file.file_url, path, result, old_hash, reason, state_dir)
        except ValueError as error:
            frappe.db.rollback()
            # Only fixed internal reason codes, no parser/document text.
            safe = str(error) if str(error) in {"source_changed", "unsafe_file_path", "non_local_file", "unavailable_or_nonstandard_storage", "recovery_requires_review"} else "invalid_result"
            status(job, "Skipped", safe)
        except Exception:
            frappe.db.rollback()
            status(job, "Failed", "processing_failed_original_retained_or_recovery_pending")
