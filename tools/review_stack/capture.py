#!/usr/bin/env python3
"""Preserve a completed CPU validation attempt without its disposable builds.

Manifests, scheduler receipts, handwritten inputs and scripts stay visible.
Only raw output and generated case/probe sources go into raw-logs.tar.gz.
Original files are read only. Existing captures are verified, never overwritten.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile

PRUNED = {"source", "build", "CMakeFiles", "__pycache__", ".git"}
PRODUCT_SUFFIXES = {".o", ".a", ".so", ".dylib", ".dll", ".exe", ".pyc",
                    ".profraw", ".profdata", ".bc"}
VISIBLE_SUFFIXES = {".json", ".py", ".sh", ".md", ".in", ".yaml", ".yml",
                    ".h", ".hpp", ".hh", ".hxx", ".cuh"}
TERMINAL = {"pass", "pass_with_skips", "failure", "cancelled", "interrupted"}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2) + "\n").encode()


def files_under(root):
    """Prune checkout/build trees before traversal; never follow symlinks."""
    if root.is_file():
        yield root, Path()
        return
    for directory, names, files in os.walk(root, followlinks=False):
        current = Path(directory)
        names[:] = sorted(name for name in names if name not in PRUNED
                          and not name.startswith("cmake-build")
                          and not (current / name).is_symlink())
        # CMake can use arbitrary binary-directory names. Its cache identifies
        # the build root more reliably than a guessed name.
        if "CMakeCache.txt" in files:
            names[:] = []
            continue
        for name in sorted(files):
            path = current / name
            if not path.is_symlink():
                yield path, path.relative_to(root)


def checked_bytes(path):
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("input changed during capture: " + str(path))
    return data


def verify(directory):
    record = json.loads((directory / "capture.json").read_text())
    archive_path = directory / "raw-logs.tar.gz"
    if sha256(archive_path.read_bytes()) != record["archive_sha256"]:
        raise ValueError("archive hash mismatch")
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        archived = {item.name: item for item in members}
        expected = {item["relative_path"] for item in record["files"]
                    if item["storage"] == "archive"}
        if len(archived) != len(members) or set(archived) != expected:
            raise ValueError("archive member inventory mismatch")
        for item in record["files"]:
            name = item["relative_path"]
            if item["storage"] == "archive":
                member = archived[name]
                if not member.isfile() or Path(name).is_absolute() or ".." in Path(name).parts:
                    raise ValueError("unsafe archive member: " + name)
                data = archive.extractfile(member).read()
            else:
                data = (directory / name).read_bytes()
            if len(data) != item["bytes"] or sha256(data) != item["sha256"]:
                raise ValueError("captured file hash mismatch: " + name)
    print(json.dumps(dict(capture=str(directory), status=record["status"],
                          files=len(record["files"]), verification="pass")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation", type=Path, help="Completed validation output directory")
    parser.add_argument("--submission", type=Path, help="Frozen scheduler submission directory")
    parser.add_argument("--input", action="append", default=[], metavar="LABEL=PATH",
                        help="Handwritten/audit input copied visibly; repeatable")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify", action="store_true", help="Verify an existing capture only")
    args = parser.parse_args()
    destination = args.output.resolve()
    if args.verify:
        verify(destination)
        return
    if destination.exists():
        parser.error("capture already exists; use --verify or choose a new output")
    if not args.validation and not args.submission and not args.input:
        parser.error("supply a validation, submission, or visible input")

    roots = []
    frozen = {}
    manifest = None
    submission = None
    for label, path, filename in (("validation", args.validation, "manifest.json"),
                                  ("submission", args.submission, "submission.json")):
        if path:
            path = path.resolve()
            raw = checked_bytes(path / filename)
            frozen[path / filename] = sha256(raw)
            value = json.loads(raw)
            if label == "validation":
                manifest = value
            else:
                submission = value
            roots.append((label, path, False))
    if manifest is not None:
        status = manifest.get("status")
        if status not in TERMINAL or not manifest.get("finished"):
            parser.error("validation attempt is still active or has no completion record")
    elif submission is not None:
        cancellation = submission.get("cancellation", {})
        if not cancellation.get("status", "").startswith("cancelled"):
            parser.error("a submission without validation needs an explicit cancellation receipt")
        status = cancellation["status"]
    else:
        status = "inputs_only"

    labels = {label for label, _, _ in roots}
    for argument in args.input:
        label, separator, value = argument.partition("=")
        if not separator or not label or Path(label).is_absolute() or ".." in Path(label).parts:
            parser.error("input must use a safe relative LABEL=PATH")
        if label in labels:
            parser.error("duplicate input label: " + label)
        labels.add(label)
        path = Path(value).resolve()
        if not path.exists():
            parser.error("missing input: " + value)
        roots.append((label, path, True))
    if any(path == destination or path in destination.parents for _, path, _ in roots):
        parser.error("output cannot be inside a captured input tree")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".capture-", dir=destination.parent))
    records = []
    names = {"capture.json", "README.md", "raw-logs.tar.gz"}
    skipped = Counter()
    try:
        archive_path = temporary / "raw-logs.tar.gz"
        with archive_path.open("wb") as stream:
            with gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                    for label, root, visible in roots:
                        for path, relative in files_under(root):
                            if path.suffix in PRODUCT_SUFFIXES:
                                skipped["compiler_or_runtime_product"] += 1
                                continue
                            data = checked_bytes(path)
                            if (path.stat().st_mode & 0o111
                                    and data.startswith((b"\x7fELF", b"MZ", b"!<arch>\n"))):
                                skipped["executable_or_library"] += 1
                                continue
                            name = str(Path(label) / relative)
                            if name in names:
                                raise ValueError("duplicate or reserved capture path: " + name)
                            names.add(name)
                            storage = "visible" if visible or path.suffix in VISIBLE_SUFFIXES else "archive"
                            if storage == "visible":
                                target = temporary / name
                                target.parent.mkdir(parents=True, exist_ok=True)
                                target.write_bytes(data)
                            else:
                                info = tarfile.TarInfo(name)
                                info.size = len(data)
                                info.mode = 0o644
                                info.mtime = 0
                                archive.addfile(info, io.BytesIO(data))
                            records.append(dict(relative_path=name, original_path=str(path),
                                                storage=storage, bytes=len(data), sha256=sha256(data)))
        for path, expected in frozen.items():
            if sha256(checked_bytes(path)) != expected:
                raise ValueError("attempt metadata changed during capture: " + str(path))
        stage_counts = Counter(stage["status"] for stage in (manifest or {}).get("stages", []))
        record = dict(schema_version=1, status=status,
                      capture_tool=dict(path=str(Path(__file__).resolve()),
                          sha256=sha256(Path(__file__).read_bytes()), invocation=sys.argv,
                          cwd=str(Path.cwd())),
                      cobalt_jobid=(manifest or {}).get("cobalt_jobid") or (manifest or {}).get("jobid")
                          or (submission or {}).get("jobid"),
                      stage_status_counts=dict(stage_counts),
                      roots=[dict(label=label, original_path=str(path), handwritten_visible=visible)
                             for label, path, visible in roots],
                      exclusion_policy=dict(pruned_directories=sorted(PRUNED),
                          cmake_build_detection="CMakeCache.txt or cmake-build prefix",
                          compiler_product_suffixes=sorted(PRODUCT_SUFFIXES),
                          explanation="Source checkouts and disposable products are omitted; their recorded source hashes remain in manifests. Original evidence is unchanged."),
                      skipped_files=dict(skipped), files=records,
                      archive_sha256=sha256(archive_path.read_bytes()))
        (temporary / "capture.json").write_bytes(json_bytes(record))
        (temporary / "README.md").write_text(
            "# Frozen validation capture\n\n"
            + "Status: `" + status + "`; Cobalt job `" + str(record["cobalt_jobid"]) + "`.\n\n"
            + "Visible files retain manifests, indices, scheduler receipts and handwritten inputs. "
            + "`raw-logs.tar.gz` contains byte-preserved raw output and generated probes/cases, using "
            + "paths relative to the listed original roots. `capture.json` inventories every captured "
            + "file with its original absolute path, byte count, SHA-256 and storage location. "
            + "Compiler products, source worktrees and CMake builds are excluded. The original "
            + "ignored files remain untouched. Failure and cancellation are preserved as such.\n\n"
            + "Verify with `python3 tools/review_stack/capture.py --output "
            + str(destination) + " --verify`.\n")
        temporary.rename(destination)
    except BaseException:
        shutil.rmtree(temporary)
        raise
    verify(destination)


if __name__ == "__main__":
    main()
