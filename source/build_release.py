from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"
VERSION = "v2.0_Logo02_Approved_Working"
DATE = "2026-08-02"
ZIP_PATH = RELEASE / f"INTAG_Brand_Identity_{VERSION}_{DATE}.zip"
TOP_FOLDER = f"INTAG_Brand_Identity_{VERSION}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def included_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if rel.parts[0] in {"tmp", "release"}:
            continue
        if "__pycache__" in rel.parts or path.suffix.lower() in {".pyc", ".pyo"}:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.as_posix().lower())


def main() -> None:
    RELEASE.mkdir(parents=True, exist_ok=True)
    files = included_files()
    manifest_entries = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in files
        if path.name != "MANIFEST_SHA256.json"
    ]
    manifest = {
        "brand": "INTAG Digital Solutions",
        "version": VERSION,
        "status": "Logo 02 approved - remaining brand system decisions are Working",
        "release_date": DATE,
        "file_count_excluding_manifest": len(manifest_entries),
        "files": manifest_entries,
    }
    manifest_path = ROOT / "MANIFEST_SHA256.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    files = included_files()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            rel = path.relative_to(ROOT).as_posix()
            archive.write(path, arcname=f"{TOP_FOLDER}/{rel}")

    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC check failed at {bad}")
        entries = archive.namelist()

    release_info = {
        "zip": ZIP_PATH.name,
        "bytes": ZIP_PATH.stat().st_size,
        "sha256": sha256(ZIP_PATH),
        "entries": len(entries),
        "top_folder": TOP_FOLDER,
        "status": "Logo 02 approved - remaining brand system decisions are Working",
    }
    (RELEASE / "RELEASE_INFO.json").write_text(json.dumps(release_info, indent=2), encoding="utf-8")
    (RELEASE / "RELEASE_SHA256.txt").write_text(f"{release_info['sha256']}  {ZIP_PATH.name}\n", encoding="ascii")
    print(json.dumps(release_info, indent=2))


if __name__ == "__main__":
    main()
