"""Bounded image/PDF optimization. Run in an isolated worker subprocess."""
import io
import json
import os
import subprocess
import sys
import warnings
from pathlib import Path

from PIL import Image, ImageOps
from PyPDF2 import PdfFileReader

TARGET = 2 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 24000000


def optimize(source, destination, target=TARGET):
    source, destination = Path(source), Path(destination)
    if source.stat().st_size <= target:
        return "already_small"
    suffix = source.suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png"}:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(source) as original:
                expected = "PNG" if suffix == ".png" else "JPEG"
                if original.format != expected or getattr(original, "n_frames", 1) != 1:
                    return "unsupported_image"
                original.load()
                image = ImageOps.exif_transpose(original)
                if expected == "JPEG" and image.mode not in {"RGB", "L", "CMYK"}:
                    image = image.convert("RGB")
                best = None
                for edge, quality in [(3000, 85), (2400, 80), (1800, 75)]:
                    candidate = image.copy()
                    candidate.thumbnail((edge, edge), getattr(Image, "Resampling", Image).LANCZOS)
                    output = io.BytesIO()
                    options = {"optimize": True}
                    if expected == "JPEG":
                        options.update(quality=quality, progressive=True)
                    candidate.save(output, format=expected, **options)
                    data = output.getvalue()
                    if best is None or len(data) < len(best):
                        best = data
                    if len(best) <= target:
                        break
                if best and len(best) < source.stat().st_size:
                    with Image.open(io.BytesIO(best)) as check:
                        check.verify()
                    destination.write_bytes(best)
                    return "compressed" if len(best) <= target else "optimized_above_target"
                return "no_smaller_result"
    if suffix != ".pdf":
        return "unsupported_type"
    data = source.read_bytes()
    # Conservative exclusion: false positives preserve the original rather than rewrite it.
    if any(token in data.lower() for token in [b"/byterange", b"/acroform", b"/xfa", b"/embeddedfiles", b"/annots", b"pdfaid:"]):
        return "protected_or_interactive_pdf"
    reader = PdfFileReader(io.BytesIO(data), strict=False)
    if reader.isEncrypted:
        return "encrypted_pdf"
    root = reader.trailer["/Root"]
    if any(key in root for key in ["/AcroForm", "/OutputIntents"]):
        return "protected_or_interactive_pdf"
    names = root.get("/Names")
    if names and "/EmbeddedFiles" in names.getObject():
        return "protected_or_interactive_pdf"
    pages = reader.getNumPages()
    if not 1 <= pages <= 200:
        return "pdf_page_limit"
    if any(page.get("/Annots") for page in reader.pages):
        return "protected_or_interactive_pdf"
    # Keep text/vector content. No whole-page rasterization or /screen preset.
    subprocess.run([
        "gs", "-q", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite",
        "-dAutoRotatePages=/None", "-dDownsampleColorImages=true",
        "-dColorImageResolution=150", "-dDownsampleGrayImages=true",
        "-dGrayImageResolution=150", "-dDownsampleMonoImages=true",
        "-dMonoImageResolution=300", "-sOutputFile=" + str(destination), str(source),
    ], check=True, timeout=60, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    result = PdfFileReader(str(destination), strict=False)
    if result.isEncrypted or result.getNumPages() != pages:
        raise ValueError("invalid_pdf_result")
    if destination.stat().st_size >= source.stat().st_size:
        destination.unlink()
        return "no_smaller_result"
    return "compressed" if destination.stat().st_size <= target else "optimized_above_target"


def isolated(source, destination, target):
    result = subprocess.run(
        [sys.executable, "-m", __name__, str(source), str(destination), str(target)],
        capture_output=True, timeout=90, text=True,
    )
    if result.returncode:
        raise RuntimeError("optimizer_process_failed")
    return json.loads(result.stdout)["reason"]


if __name__ == "__main__":
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (768 * 1024**2, 768 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (70, 70))
    os.umask(0o077)
    try:
        print(json.dumps({"reason": optimize(sys.argv[1], sys.argv[2], int(sys.argv[3]))}))
    except Exception:
        # Never print parser messages containing document text or filesystem names.
        sys.exit(1)
