#!/usr/bin/env python3
"""Find all .doc files under data/EM2024/pdf and convert them to .docx using LibreOffice."""

import subprocess
import sys
from pathlib import Path

DOC_ROOT = Path("data/EM2024/pdf")


def main():
    doc_files = sorted(DOC_ROOT.rglob("*.doc"))
    # Exclude files already named .docx (rglob "*.doc" won't match .docx, but be safe)
    doc_files = [f for f in doc_files if f.suffix.lower() == ".doc"]

    if not doc_files:
        print("No .doc files found.")
        sys.exit(0)

    print(f"Found {len(doc_files)} .doc file(s).")

    errors = []
    for doc in doc_files:
        docx = doc.with_suffix(".docx")
        if docx.exists():
            print(f"  Skipping (already exists): {docx}")
            continue

        print(f"  Converting: {doc}")
        result = subprocess.run(
            [
                "libreoffice", "--headless",
                "--convert-to", "docx",
                "--outdir", str(doc.parent),
                str(doc),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  ERROR: {result.stderr.strip()}")
            errors.append(doc)
        else:
            print(f"  -> {docx.name}")

    if errors:
        print(f"\n{len(errors)} file(s) failed:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
