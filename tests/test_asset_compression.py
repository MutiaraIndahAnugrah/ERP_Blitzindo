"""Local-only integration tests. Run with bench's Python from sites/."""
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import frappe
from PIL import Image, ImageDraw
from werkzeug.datastructures import FileStorage, MultiDict

from kulkul_erp.asset_compression import engine, events, worker


def png_bytes():
    image = Image.new("RGB", (1800, 1200), "white")
    draw = ImageDraw.Draw(image)
    for y in range(30, 1160, 40):
        draw.text((40, y), "SYNTHETIC TEST DOCUMENT 1234567890 ABCDEFGHIJ", fill="black")
    output = io.BytesIO()
    image.save(output, "PNG", compress_level=0)
    return output.getvalue()


class CompressionTests(unittest.TestCase):
    def setUp(self):
        self.files = []
        frappe.set_user("Administrator")
        frappe.conf.asset_compression_enabled = 1
        frappe.conf.asset_compression_target_bytes = engine.TARGET
        frappe.clear_cache(doctype="File")
        frappe.form_dict = frappe._dict()

    def tearDown(self):
        frappe.db.rollback()
        for name in self.files:
            for task in frappe.get_all(events.JOB, filters={"file": name}, pluck="name"):
                frappe.delete_doc(events.JOB, task, ignore_permissions=True, force=True)
            if frappe.db.exists("File", name):
                frappe.delete_doc("File", name, ignore_permissions=True, force=True)
        frappe.db.commit()
        frappe.form_dict = frappe._dict()

    def upload(self, data=None, suffix=".png", private=1):
        from frappe.handler import upload_file
        data = png_bytes() if data is None else data
        filename = "compression-test-" + frappe.generate_hash(length=12) + suffix
        frappe.request = SimpleNamespace(files=MultiDict({"file": FileStorage(io.BytesIO(data), filename=filename)}))
        frappe.form_dict = frappe._dict(is_private=str(private), folder="Home/Attachments")
        result = upload_file()
        self.files.append(result.name)
        return result

    def job(self, file):
        return frappe.db.get_value(events.JOB, {"file": file.name}, "name")

    def run_job(self, file):
        frappe.db.commit()
        worker.process(self.job(file))
        frappe.db.commit()
        return frappe.get_doc(events.JOB, self.job(file))

    def test_actual_redis_queue_separate_worker(self):
        import subprocess
        file = self.upload()
        original_size = Path(file.get_full_path()).stat().st_size
        frappe.db.commit()
        events.dispatch()
        command = "import frappe; frappe.init(site='blitz.local'); frappe.connect(); from frappe.utils.background_jobs import get_queue; from rq import Worker; q=get_queue('asset_compression'); Worker([q],connection=q.connection).work(burst=True); frappe.destroy()"
        result = subprocess.run([sys.executable, "-c", command], capture_output=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout.decode(errors="replace")[-2000:] + result.stderr.decode(errors="replace")[-2000:])
        frappe.db.rollback()
        task = frappe.get_doc(events.JOB, self.job(file))
        self.assertEqual(task.status, "Done")
        self.assertLess(Path(file.get_full_path()).stat().st_size, original_size)

    def test_recover_after_rename_before_database_commit(self):
        file = self.upload()
        real_finish = worker.finish_swap
        class SimulatedWorkerDeath(BaseException):
            pass
        with patch.object(worker, "finish_swap", side_effect=SimulatedWorkerDeath):
            with self.assertRaises(SimulatedWorkerDeath):
                self.run_job(file)
        frappe.db.rollback()
        # Filesystem already contains the smaller result; the journal repairs metadata.
        task = self.run_job(file)
        self.assertEqual(task.status, "Done")
        file.reload()
        self.assertEqual(file.content_hash, worker.digest(Path(file.get_full_path())))

    def test_animated_png_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.png"; output = Path(directory) / "output.png"
            frames = [Image.new("RGB", (100, 100), color) for color in ["red", "blue"]]
            frames[0].save(source, save_all=True, append_images=frames[1:])
            self.assertEqual(engine.optimize(source, output, target=1), "unsupported_image")
            self.assertFalse(output.exists())

    def test_bounded_retry(self):
        file = self.upload()
        with patch.object(worker, "isolated", side_effect=RuntimeError("simulated")) as optimizer:
            for attempt in range(5):
                task = self.run_job(file)
        self.assertEqual(task.attempts, 3)
        self.assertEqual(optimizer.call_count, 3)

    def test_user_can_delete_file_with_pending_job(self):
        file = self.upload()
        task = self.job(file)
        frappe.db.commit()
        frappe.delete_doc("File", file.name, ignore_permissions=True)
        frappe.db.commit()
        worker.process(task)
        self.assertEqual(frappe.db.get_value(events.JOB, task, "reason"), "file_removed")

    def test_low_disk_keeps_original(self):
        file = self.upload()
        original = Path(file.get_full_path()).read_bytes()
        with patch.object(worker.shutil, "disk_usage", return_value=SimpleNamespace(free=0)):
            self.assertEqual(self.run_job(file).status, "Failed")
        self.assertEqual(Path(file.get_full_path()).read_bytes(), original)

    def test_transparent_png_preserved_and_above_target_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.png"; result = Path(directory) / "output.png"
            Image.new("RGBA", (100, 100), (200, 100, 20, 0)).save(source, compress_level=0)
            self.assertEqual(engine.optimize(source, result, target=1), "optimized_above_target")
            with Image.open(result) as image:
                self.assertEqual(image.mode, "RGBA")
                self.assertEqual(image.getpixel((0, 0))[3], 0)

    def test_pdf_searchable_text_preserved(self):
        from PyPDF2 import PdfFileWriter, PdfFileReader
        from PyPDF2.generic import NameObject, DictionaryObject, DecodedStreamObject
        pdf = PdfFileWriter(); page = pdf.addBlankPage(300, 300)
        pdf._root_object.pop(NameObject("/AcroForm"), None)
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})
        content = DecodedStreamObject()
        content.setData(b"BT /F1 12 Tf 30 40 Td (SYNTHETIC TEXT SEARCH) Tj ET\n" + b" " * (engine.TARGET + 100))
        page[NameObject("/Contents")] = content
        output = io.BytesIO(); pdf.write(output)
        file = self.upload(output.getvalue(), ".pdf")
        self.assertEqual(self.run_job(file).status, "Done")
        text = PdfFileReader(file.get_full_path()).getPage(0).extractText()
        self.assertIn("SYNTHETIC TEXT SEARCH", text)

    def test_upload_never_calls_optimizer_or_redis(self):
        with patch.object(engine, "isolated", side_effect=AssertionError("upload must not compress")), patch.object(frappe, "enqueue", side_effect=AssertionError("upload must not enqueue Redis")):
            file = self.upload()
        self.assertEqual(Path(file.get_full_path()).read_bytes(), png_bytes())
        self.assertEqual(frappe.db.get_value(events.JOB, self.job(file), "status"), "Pending")

    def test_upload_rollback_also_removes_outbox(self):
        file = self.upload()
        name = self.job(file)
        frappe.db.rollback()
        self.assertFalse(frappe.db.exists(events.JOB, name))
        self.assertFalse(frappe.db.exists("File", file.name))

    def test_private_image_url_and_hash_remain_consistent(self):
        file = self.upload()
        url = file.file_url
        task = self.run_job(file)
        file.reload()
        self.assertEqual(task.status, "Done")
        self.assertLess(task.result_bytes, task.original_bytes)
        self.assertEqual(file.file_url, url)
        self.assertEqual(file.is_private, 1)
        self.assertEqual(file.file_size, os.path.getsize(file.get_full_path()))
        self.assertEqual(file.content_hash, worker.digest(Path(file.get_full_path())))
        with Image.open(file.get_full_path()) as image:
            self.assertEqual(image.size, (1800, 1200))
            image.verify()

    def test_public_upload_and_duplicate_url_references(self):
        first = self.upload(private=0)
        second = self.upload(private=0)
        self.assertEqual(first.file_url, second.file_url)
        self.run_job(first)
        first.reload(); second.reload()
        self.assertEqual(first.content_hash, second.content_hash)
        self.assertEqual(first.file_size, second.file_size)
        self.assertEqual(second.is_private, 0)
        self.assertEqual(self.run_job(second).status, "Skipped")

    def test_optimizer_failure_keeps_original(self):
        file = self.upload()
        original = Path(file.get_full_path()).read_bytes()
        with patch.object(worker, "isolated", side_effect=RuntimeError("simulated")):
            task = self.run_job(file)
        self.assertEqual(task.status, "Failed")
        self.assertEqual(Path(file.get_full_path()).read_bytes(), original)

    def test_database_failure_restores_original(self):
        file = self.upload()
        original = Path(file.get_full_path()).read_bytes()
        real_status = worker.status
        def fail_finish(job, state, *args):
            if state == "Done":
                raise RuntimeError("simulated DB failure")
            return real_status(job, state, *args)
        with patch.object(worker, "status", side_effect=fail_finish):
            task = self.run_job(file)
        self.assertEqual(task.status, "Failed")
        self.assertEqual(Path(file.get_full_path()).read_bytes(), original)
        file.reload()
        self.assertEqual(file.content_hash, worker.digest(Path(file.get_full_path())))

    def test_disabled_upload_has_no_job(self):
        frappe.conf.asset_compression_enabled = 0
        file = self.upload()
        self.assertFalse(self.job(file))

    def test_small_and_unsupported_and_corrupt_files(self):
        for data, suffix, expected in [(b"small", ".txt", "Skipped"), (b"z" * (engine.TARGET + 1), ".zip", "Skipped"), (b"broken" * 400000, ".png", "Failed")]:
            file = self.upload(data=data, suffix=suffix)
            self.assertEqual(self.run_job(file).status, expected)
            self.assertEqual(Path(file.get_full_path()).read_bytes(), data)

    def test_input_limit_preserves_file(self):
        file = self.upload()
        frappe.conf.asset_compression_max_input_bytes = 1024
        try:
            self.assertEqual(self.run_job(file).reason, "processing_input_limit")
        finally:
            frappe.conf.asset_compression_max_input_bytes = 104857600

    def test_deleted_file_and_duplicate_delivery(self):
        file = self.upload()
        task = self.run_job(file)
        attempts = task.attempts
        task = self.run_job(file)
        self.assertEqual(task.attempts, attempts)
        missing = self.upload()
        frappe.db.commit()
        Path(missing.get_full_path()).unlink()
        self.assertEqual(self.run_job(missing).reason, "unavailable_or_nonstandard_storage")

    def test_dispatch_outage_retains_task(self):
        file = self.upload()
        frappe.db.commit()
        with patch.object(frappe, "enqueue", side_effect=ConnectionError("queue unavailable")):
            events.dispatch()
        self.assertEqual(frappe.db.get_value(events.JOB, self.job(file), "status"), "Pending")

    def test_protected_encrypted_and_animated_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.pdf"; output = Path(directory) / "output.pdf"
            source.write_bytes(b"%PDF-1.4 /ByteRange [0 1 2 3]" + b" " * engine.TARGET)
            self.assertEqual(engine.optimize(source, output), "protected_or_interactive_pdf")
            self.assertFalse(output.exists())
            from PyPDF2 import PdfFileWriter
            pdf = PdfFileWriter(); pdf.addBlankPage(100, 100); pdf.encrypt("synthetic-password")
            with open(source, "wb") as stream: pdf.write(stream)
            self.assertIn(engine.optimize(source, output, target=1), {"encrypted_pdf", "protected_or_interactive_pdf"})

    def test_path_traversal_and_symlink_rejected(self):
        for url in ["/files/../site_config.json", "/private/files/%2e%2e%2fsite_config.json", "https://example.org/file.pdf"]:
            with self.assertRaises(ValueError): worker.file_path(url)
        file = self.upload(); path = Path(file.get_full_path())
        temporary = path.with_suffix(".link-target"); path.rename(temporary)
        try:
            path.symlink_to(temporary)
            with self.assertRaises(ValueError): worker.file_path(file.file_url)
        finally:
            path.unlink(); temporary.rename(path)

    def test_pdf_scan_compression_keeps_pages(self):
        image = Image.effect_noise((2400, 1800), 80).convert("RGB")
        output = io.BytesIO(); image.save(output, "PDF", resolution=300, quality=95)
        data = output.getvalue()
        self.assertGreater(len(data), engine.TARGET)
        file = self.upload(data, ".pdf")
        task = self.run_job(file)
        self.assertEqual(task.status, "Done")
        from PyPDF2 import PdfFileReader
        self.assertEqual(PdfFileReader(file.get_full_path()).getNumPages(), 1)
        self.assertLess(task.result_bytes, task.original_bytes)


if __name__ == "__main__":
    frappe.init(site="blitz.local"); frappe.connect()
    assert frappe.conf.mute_emails and not frappe.db.count("Webhook")
    try:
        unittest.main(verbosity=2)
    finally:
        frappe.db.rollback(); frappe.destroy()
