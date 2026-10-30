#!/usr/bin/env python3
"""Preserve completed CPU stack-validation records without build/source trees."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("validation", type=Path)
    parser.add_argument("--evaluation-root", type=Path, default=Path(__file__).resolve().parents[3] / "ffmt-evaluation")
    args = parser.parse_args()
    original = args.validation.resolve()
    evaluation = args.evaluation_root.resolve()
    manifest = json.loads((original / "manifest.json").read_text())
    if manifest.get("status") == "running" or not manifest.get("finished"):
        parser.error("validation must be finalized before capture")
    destination = evaluation / "docs/provenance/review-stack-validation"
    destination.mkdir(parents=True, exist_ok=True)
    preserved = []
    selected = [original / "manifest.json"]
    for path in original.rglob("*"):
        if not path.is_file() or path in selected:
            continue
        relative = path.relative_to(original)
        # Preserve raw command logs and child manifests, never source headers,
        # generated translation units, object files, libraries or executables.
        if path.suffix in (".stdout", ".stderr", ".su", ".log") or path.name in ("manifest.json", "submission.json"):
            selected.append(path)
    for old in sorted(selected):
        relative = old.relative_to(original)
        new = destination / (relative if relative in (Path("manifest.json"), Path("submission.json")) else "logs" / relative)
        new.parent.mkdir(parents=True, exist_ok=True)
        before = sha(old)
        shutil.copyfile(old, new)
        if sha(new) != before or sha(old) != before:
            raise RuntimeError("capture input changed: " + str(old))
        preserved.append(dict(original_path=str(old), relative_path=relative.as_posix(),
            evaluation_path=new.relative_to(evaluation).as_posix(), sha256=before, bytes=new.stat().st_size))
    inventory = destination / "captured-files.json"
    inventory.write_text(json.dumps(dict(schema_version=1, original_directory=str(original),
        manifest_sha256=sha(original / "manifest.json"), files=preserved), indent=2) + "\n")
    print(json.dumps(dict(status=manifest["status"], captured_files=len(preserved),
        captured_bytes=sum(item["bytes"] for item in preserved), inventory=str(inventory),
        inventory_sha256=sha(inventory)), indent=2))


if __name__ == "__main__":
    main()
