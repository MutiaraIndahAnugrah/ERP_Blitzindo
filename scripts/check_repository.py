"""Validate repository source without connecting to an ERP site."""
import ast
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    failures = []
    counts = {"python": 0, "json": 0}
    for path in sorted((ROOT / "kulkul_erp").rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(ROOT)
        try:
            if path.suffix == ".py":
                ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(relative))
                counts["python"] += 1
            elif path.suffix == ".json":
                json.loads(path.read_text(encoding="utf-8-sig"))
                counts["json"] += 1
        except (SyntaxError, ValueError, UnicodeError) as error:
            failures.append(str(relative) + ": " + type(error).__name__)
    for path in [ROOT / "invoice_print/install.py", ROOT / "invoice_print/self_test.py"]:
        ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path.relative_to(ROOT)))
    template = (ROOT / "invoice_print/items.html").read_text(encoding="utf8")
    if "blitz-dynamic-source-items-v1" not in template or "Harga /" not in template:
        failures.append("Invoice template marker or unit-price column missing")
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    for name in filter(None, tracked):
        parts = Path(name).parts
        if any(part in {"sites", "previews", "backups", "__pycache__", "outputs", "work"} for part in parts):
            failures.append("Private/runtime path tracked: " + name)
        if name.endswith((".pdf", ".sql", ".sql.gz", ".pem", ".key")) or Path(name).name in {"site_config.json", "common_site_config.json", ".env"}:
            failures.append("Private/runtime file tracked: " + name)
    if failures:
        raise SystemExit("\n".join(failures))
    print("Source checks passed:", counts, "; invoice template and tracked paths checked")


if __name__ == "__main__":
    main()
