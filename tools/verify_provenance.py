#!/usr/bin/env python3
"""Verify preserved campaign bytes and the split's library source equivalence.

This check uses only the standard library and local files. It never launches a
compiler, scheduler job, hardware test, or network request.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_digest(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def contained(root, name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Manifest path must be relative and contained: " + str(name))
    return root / path


def verify_file(root, name, expected, failures, label):
    try:
        path = contained(root, name)
        actual = digest(path)
    except (OSError, ValueError) as error:
        failures.append(label + ": " + str(error))
        return
    if actual != expected:
        failures.append(label + ": SHA-256 differs for " + name + " (expected " + expected + ", got " + actual + ")")


def git(directory, *arguments):
    return subprocess.check_output(["git", "-C", str(directory), *arguments], stderr=subprocess.PIPE, text=True).strip()


def source_refs(manifest, checkout, failures):
    """Check locally retained refs; no fetching and no working-tree mutations."""
    archive = manifest["original_library"]
    checks = [(archive["archive_ref"], archive["archive_commit"])]
    checks.extend((item["preservation_ref"], item["original_commit"])
                  for item in manifest["qualified_snapshots"])
    for ref, expected in checks:
        try:
            actual = git(checkout, "rev-parse", "--verify", ref + "^{commit}")
            if actual != expected:
                failures.append("source ref " + ref + " targets " + actual + ", expected " + expected)
        except (OSError, subprocess.CalledProcessError) as error:
            failures.append("Cannot resolve local source ref " + ref + ": " + str(error))
    # All old PR tips and additional recorded ffmt/runner commits must remain
    # reachable from the archived campaign, even after PR branches are closed.
    commits = {item["old_tip"] for item in manifest["replacement_changes"]}
    commits.update(item["commit"] for item in manifest["additional_recorded_commits"])
    for commit in sorted(commits):
        try:
            subprocess.run(["git", "-C", str(checkout), "merge-base", "--is-ancestor",
                            commit, archive["archive_commit"]], check=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError):
            failures.append("Recorded commit is not locally reachable from campaign archive: " + commit)
    for snapshot in manifest["qualified_snapshots"]:
        try:
            actual = {}
            names = git(checkout, "ls-tree", "-r", "--name-only", snapshot["original_commit"], "include").splitlines()
            for name in names:
                data = subprocess.check_output(["git", "-C", str(checkout), "show",
                                                snapshot["original_commit"] + ":" + name], stderr=subprocess.PIPE)
                actual[name] = hashlib.sha256(data).hexdigest()
            if actual != snapshot["header_files"]:
                failures.append("Archived header files differ for snapshot " + snapshot["id"])
        except (OSError, subprocess.CalledProcessError) as error:
            failures.append("Cannot inspect archived snapshot " + snapshot["id"] + ": " + str(error))
    return len(checks), len(commits)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmt-checkout", required=True, type=Path,
                        help="Library checkout or source directory to compare with final qualified headers")
    parser.add_argument("--evaluation-root", type=Path, default=ROOT,
                        help="Relocated evaluation tree; defaults to this script's repository")
    parser.add_argument("--manifest", type=Path,
                        help="Split ledger; defaults to docs/provenance/split.json below --evaluation-root")
    parser.add_argument("--check-source-refs", action="store_true",
                        help="Also validate archived local Git refs, ancestry, and snapshot header contents")
    parser.add_argument("--original-checkout", type=Path,
                        help="Git checkout with archive tags; defaults to --ffmt-checkout")
    parser.add_argument("--check-raw-inputs", action="store_true",
                        help="Also verify selected raw manifest hashes in retained ignored artifacts/")
    args = parser.parse_args(argv)
    root = args.evaluation_root.expanduser().resolve()
    checkout = args.ffmt_checkout.expanduser().resolve()
    path = args.manifest or root / "docs/provenance/split.json"
    try:
        manifest = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        parser.error("Cannot load split ledger: " + str(error))
    if manifest.get("schema_version") != 1:
        parser.error("Unsupported split ledger schema")
    failures = []
    for item in manifest["preserved_evidence"]:
        verify_file(root, item["evaluation_path"], item["sha256"], failures, "preserved evidence")
    for item in manifest.get("preserved_campaign_configuration", []):
        verify_file(root, item["evaluation_path"], item["sha256"], failures, "historical configuration")
    if args.check_raw_inputs:
        for item in manifest.get("selected_raw_inputs", []):
            verify_file(root, item["path"], item["sha256"], failures, "selected raw input")
    equivalent = manifest["source_equivalence"]
    expected = equivalent["header_files"]
    if canonical_digest(expected) != equivalent["canonical_header_sha256"]:
        failures.append("Header hash map does not match its canonical digest in split ledger")
    include = checkout / "include"
    actual_names = {item.relative_to(checkout).as_posix() for item in include.rglob("*") if item.is_file()}
    if actual_names != set(expected):
        failures.append("Library header inventory differs (missing=" + str(sorted(set(expected) - actual_names)) +
                        ", additional=" + str(sorted(actual_names - set(expected))) + ")")
    for name, sha256 in expected.items():
        verify_file(checkout, name, sha256, failures, "library source")
    corpus = equivalent["corpus"]
    verify_file(checkout, corpus["path"], corpus["sha256"], failures, "conformance corpus")
    for snapshot in manifest["qualified_snapshots"]:
        if canonical_digest(snapshot["header_files"]) != snapshot["canonical_header_sha256"]:
            failures.append("Archived snapshot hash map is inconsistent: " + snapshot["id"])
    refs = commits = 0
    if args.check_source_refs:
        refs, commits = source_refs(manifest, (args.original_checkout or checkout).expanduser().resolve(), failures)
    if failures:
        for failure in failures:
            print("FAIL: " + failure, file=sys.stderr)
        return 1
    print("PASS: " + str(len(manifest["preserved_evidence"])) + " preserved evidence files, " +
          str(len(manifest.get("preserved_campaign_configuration", []))) + " historical configuration files, " +
          str(len(expected)) + " library headers, and conformance corpus")
    if args.check_source_refs:
        print("PASS: " + str(refs) + " archive/qualified refs and " + str(commits) + " reachable original commits")
    if args.check_raw_inputs:
        print("PASS: " + str(len(manifest.get("selected_raw_inputs", []))) + " retained selected raw inputs")
    print("Source equivalence concerns recorded bytes; it does not qualify changed runners or repeat hardware tests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
