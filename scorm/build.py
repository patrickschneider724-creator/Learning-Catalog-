#!/usr/bin/env python3
"""Build a SCORM 1.2 zip package from the canonical index.html.

Run from the repo root:  python3 scorm/build.py
Produces:                learning-catalog-scorm.zip in the repo root.

Steps:
  1. Stage index.html and solutions-data.js into build/.
  2. Download React, ReactDOM, and Babel UMD bundles into build/vendor/.
  3. Rewrite index.html script tags to point at the local vendor copies
     and insert the SCORM API wrapper.
  4. Copy imsmanifest.xml and scorm-api.js into the build.
  5. Zip the build/ contents (not the build/ folder itself — SCORM expects
     the manifest at the zip root).
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCORM = REPO / "scorm"
BUILD = REPO / "build-scorm"
OUT = REPO / "learning-catalog-scorm.zip"

VENDOR_FILES = {
    "react.production.min.js":      "https://unpkg.com/react@18.3.1/umd/react.production.min.js",
    "react-dom.production.min.js":  "https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js",
    "babel.min.js":                 "https://unpkg.com/@babel/standalone@7.29.0/babel.min.js",
}


def fetch(url: str, dest: Path) -> None:
    print(f"  fetching {url}")
    with urllib.request.urlopen(url, timeout=60) as resp:
        dest.write_bytes(resp.read())


def rewrite_index(html: str) -> str:
    """Replace CDN script tags with local vendor paths and insert the SCORM API."""
    # React, ReactDOM, Babel — match the whole tag including the integrity attr
    html = re.sub(
        r'<script src="https://unpkg\.com/react@[^"]*"[^>]*></script>',
        '<script src="vendor/react.production.min.js"></script>',
        html,
    )
    html = re.sub(
        r'<script src="https://unpkg\.com/react-dom@[^"]*"[^>]*></script>',
        '<script src="vendor/react-dom.production.min.js"></script>',
        html,
    )
    html = re.sub(
        r'<script src="https://unpkg\.com/@babel/[^"]*"[^>]*></script>',
        '<script src="vendor/babel.min.js"></script>\n  <script src="vendor/scorm-api.js"></script>',
        html,
    )
    return html


def main() -> int:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    (BUILD / "vendor").mkdir()

    # 1. Stage canonical files
    print("Staging content...")
    shutil.copy2(REPO / "index.html", BUILD / "index.html")
    shutil.copy2(REPO / "solutions-data.js", BUILD / "solutions-data.js")

    # 2. Vendor libraries
    print("Downloading vendor libraries...")
    for name, url in VENDOR_FILES.items():
        fetch(url, BUILD / "vendor" / name)

    # 3. Rewrite index.html
    print("Rewriting index.html...")
    idx = BUILD / "index.html"
    idx.write_text(rewrite_index(idx.read_text(encoding="utf-8")), encoding="utf-8")

    # 4. SCORM-specific files
    print("Adding SCORM manifest + API...")
    shutil.copy2(SCORM / "imsmanifest.xml", BUILD / "imsmanifest.xml")
    shutil.copy2(SCORM / "scorm-api.js", BUILD / "vendor" / "scorm-api.js")

    # 5. Zip — manifest must be at the zip root
    print(f"Writing {OUT.name}...")
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(BUILD.rglob("*")):
            if path.is_file():
                arcname = path.relative_to(BUILD).as_posix()
                zf.write(path, arcname)

    size_mb = OUT.stat().st_size / (1024 * 1024)
    print(f"\nDone. {OUT.relative_to(REPO)}  ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
