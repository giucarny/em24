#!/usr/bin/env python3
"""Convert documents in data/EM2024/pdf to markdown using marker batch converter."""

import subprocess
import sys
import tempfile
from pathlib import Path

PDF_ROOT = Path("data/EM2024/pdf")
MD_ROOT = Path("data/EM2024/markdown")

# All extensions marker can handle
SUPPORTED_EXTS = {
    ".pdf",
    ".docx", ".doc",
    ".xlsx", ".xls",
    ".pptx", ".ppt",
    ".epub",
    ".html",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp",
}


def has_supported_files(directory: Path) -> bool:
    return any(f.suffix.lower() in SUPPORTED_EXTS for f in directory.iterdir() if f.is_file())


def repair_pdf(pdf: Path) -> bool:
    """Try to open pdf with pypdfium2; if it fails, repair in-place with Ghostscript."""
    try:
        import pypdfium2 as pdfium
        pdfium.PdfDocument(str(pdf))
        return True  # fine as-is
    except Exception:
        pass

    print(f"  Repairing malformed PDF: {pdf.name}")
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    result = subprocess.run(
        [
            "gs", "-dNOPAUSE", "-dBATCH", "-dQUIET",
            "-sDEVICE=pdfwrite",
            f"-sOutputFile={tmp_path}",
            str(pdf),
        ],
        capture_output=True,
    )
    if result.returncode != 0 or not tmp_path.exists():
        print(f"  WARNING: Ghostscript could not repair {pdf.name}, skipping.")
        tmp_path.unlink(missing_ok=True)
        return False

    tmp_path.replace(pdf)
    print(f"  Repaired: {pdf.name}")
    return True


def repair_directory(directory: Path) -> None:
    for pdf in directory.glob("*.pdf"):
        repair_pdf(pdf)


def main():
    # Collect every directory (at any depth) that directly contains convertible files
    doc_dirs = sorted(
        p for p in PDF_ROOT.rglob("*") if p.is_dir() and has_supported_files(p)
    )
    if not doc_dirs:
        print("No directories with supported documents found.")
        sys.exit(1)

    print(f"Found {len(doc_dirs)} director(ies) containing documents.")

    for pdf_dir in doc_dirs:
        files = [f for f in pdf_dir.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS]
        rel = pdf_dir.relative_to(PDF_ROOT)
        out_dir = MD_ROOT / rel
        out_dir.mkdir(parents=True, exist_ok=True)

        repair_directory(pdf_dir)

        by_ext = {}
        for f in files:
            by_ext.setdefault(f.suffix.lower(), 0)
            by_ext[f.suffix.lower()] += 1
        summary = ", ".join(f"{n} {ext}" for ext, n in sorted(by_ext.items()))
        print(f"\n[{rel}] Converting {summary} -> {out_dir}")

        cmd = [
            "uv", "run", "marker",
            str(pdf_dir),  # marker auto-detects format per file via provider_from_filepath
            "--output_dir", str(out_dir),
            "--output_format", "markdown",
            "--skip_existing",
            "--disable_image_extraction",
            "--workers", "1",              # one GPU worker at a time
            "--max_tasks_per_worker", "5", # recycle worker every 5 PDFs to free memory
        ]

        result = subprocess.run(cmd, capture_output=False)
        if result.returncode != 0:
            print(f"  ERROR: marker exited with code {result.returncode} for {rel}")

    print("\nDone.")


if __name__ == "__main__":
    main()
