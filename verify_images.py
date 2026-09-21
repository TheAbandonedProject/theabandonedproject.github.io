#!/usr/bin/env python3
"""
Repository gate for the public publication-image host. Standard library only. Run by CI on every push and by the
publish script before every commit. Exit 1 blocks the deploy.

Rules (all must hold for every file under i/):
  * only .jpg files, named <slug>-<first 10 hex of the file's own SHA-256>.jpg (a hash of the CONTENT, never a camera name);
  * the name's hash must match the file, so a file cannot be swapped or edited in place without renaming;
  * at most 600 KB, 1280 px wide and 1800 px tall each (the derivative limits, so a full-resolution original cannot pass);
  * the JPEG carries NO metadata (no EXIF/GPS/XMP/IPTC/ICC/comment); only the plain JFIF header;
  * nothing else lives under i/, and manifest.json lists exactly the files present (no orphan, no unlisted file).
Everything committed to this repository is public. Never commit originals, coordinates, story names or private notes.
"""
import hashlib, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jpeg_clean import verify_clean_raw, jpeg_dimensions  # noqa: E402

ROOT = Path(__file__).resolve().parent
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-([0-9a-f]{10})\.jpg$")
MAX_BYTES = 600_000
MAX_W, MAX_H = 1280, 1800   # derivative limits from make_derivative.py; a full-resolution original cannot pass


def check(root: Path = ROOT):
    errors = []
    idir = root / "i"
    files = sorted(p for p in idir.iterdir()) if idir.exists() else []
    seen = set()
    for p in files:
        if p.name == ".gitkeep":
            continue
        m = NAME.match(p.name)
        if not m:
            errors.append(f"{p.name}: file name must look like slug-<10 hex>.jpg"); continue
        data = p.read_bytes()
        if hashlib.sha256(data).hexdigest()[:10] != m.group(1):
            errors.append(f"{p.name}: hash in the name does not match the file content")
        if len(data) > MAX_BYTES:
            errors.append(f"{p.name}: larger than {MAX_BYTES // 1000} KB")
        dim = jpeg_dimensions(data)
        if not dim:
            errors.append(f"{p.name}: cannot read image dimensions")
        elif dim[0] > MAX_W or dim[1] > MAX_H:
            errors.append(f"{p.name}: {dim[0]}x{dim[1]} exceeds the derivative limit {MAX_W}x{MAX_H} (looks like an original)")
        for prob in verify_clean_raw(data):
            errors.append(f"{p.name}: METADATA/format problem: {prob}")
        seen.add(p.name)
    mf = root / "manifest.json"
    listed = set()
    if mf.exists():
        try:
            listed = {e["file"] for e in json.loads(mf.read_text(encoding="utf-8")).get("images", [])}
        except Exception as e:
            errors.append(f"manifest.json unreadable: {e}")
    for f in sorted(listed - seen):
        errors.append(f"manifest lists {f} but the file is missing")
    for f in sorted(seen - listed):
        errors.append(f"{f} is present but not listed in manifest.json")
    return errors, len(seen)


if __name__ == "__main__":
    errs, n = check()
    if errs:
        print(f"REFUSED: {len(errs)} problem(s) in {n} image(s)")
        for e in errs:
            print("  - " + e)
        sys.exit(1)
    print(f"OK: {n} image(s), all clean, hash-named and listed")
