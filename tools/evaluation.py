#!/usr/bin/env python3
"""Select external ffmt sources and launch portable library tools on JLSE."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "platforms/profiles.json"
LIBRARY_PIN = json.loads((ROOT / "platforms/library.json").read_text())
DEFAULT_REPOSITORY = LIBRARY_PIN["repository"]


def git(directory, *arguments):
    return subprocess.check_output(["git", "-C", str(directory), *arguments], text=True).strip()


def add_source_arguments(parser, *, revision=True):
    parser.add_argument("--ffmt-checkout", type=Path, default=os.environ.get("FFMT_CHECKOUT"),
                        help="Existing checkout containing the portable ffmt runners")
    parser.add_argument("--source-root", type=Path, default=os.environ.get("FFMT_SOURCE_ROOT"),
                        help="Library source repository; defaults to --ffmt-checkout")
    parser.add_argument("--runner-revision", default=os.environ.get("FFMT_RUNNER_REVISION"),
                        help="Full immutable ffmt commit to bootstrap when no checkout is supplied")
    parser.add_argument("--ffmt-repository", default=os.environ.get("FFMT_REPOSITORY", DEFAULT_REPOSITORY))
    if revision:
        parser.add_argument("--revision", help="Library revision in --source-root; existing checkouts default to WORKTREE")


def bootstrap(repository, revision):
    """Cache an explicit commit; never infer a mutable upstream branch."""
    if not re.fullmatch(r"[0-9a-fA-F]{40}", revision or ""):
        raise ValueError("Without --ffmt-checkout supply a full 40-character --runner-revision or --revision")
    key = hashlib.sha256(repository.encode()).hexdigest()[:12]
    target = ROOT / "software/local/ffmt-checkouts" / key / revision.lower()
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", "--no-checkout", "--filter=blob:none", repository, str(target)], check=True)
        subprocess.run(["git", "-C", str(target), "fetch", "--quiet", "--depth=1", "origin", revision], check=True)
        subprocess.run(["git", "-C", str(target), "checkout", "--quiet", "--detach", revision], check=True)
    if git(target, "rev-parse", "HEAD") != revision.lower():
        raise ValueError("Cached runner checkout does not match its requested immutable pin")
    if git(target, "status", "--porcelain"):
        raise ValueError("Cached pinned runner checkout is dirty; use an explicit development checkout")
    return target


def select_sources(args):
    requested = getattr(args, "revision", None)
    checkout = args.ffmt_checkout
    if checkout is None:
        if not args.runner_revision and not re.fullmatch(r"[0-9a-fA-F]{40}", requested or ""):
            raise ValueError("Without --ffmt-checkout supply a full 40-character --revision or --runner-revision")
        checkout = bootstrap(args.ffmt_repository, args.runner_revision or LIBRARY_PIN["runner_commit"])
        requested = requested or args.runner_revision
    checkout = Path(checkout).expanduser().resolve()
    source = Path(args.source_root or checkout).expanduser().resolve()
    for directory in (checkout, source):
        if not (directory / "include/ffmt").is_dir():
            raise ValueError("Not an ffmt checkout: " + str(directory))
        git(directory, "rev-parse", "--show-toplevel")
    runner = checkout / "tools/conformance.py"
    if not runner.is_file() or "FFMT_WORKSPACE" not in runner.read_text() or "FFMT_SOURCE_ROOT" not in runner.read_text():
        raise ValueError("The runner checkout predates the portable split; supply a current --ffmt-checkout and use --source-root/--revision for historical library code")
    revision = requested or "WORKTREE"
    if revision != "WORKTREE":
        revision = git(source, "rev-parse", "--verify", revision + "^{commit}")
    environment = os.environ.copy()
    environment.update(FFMT_CHECKOUT=str(checkout), FFMT_SOURCE_ROOT=str(source),
                       FFMT_WORKSPACE=str(ROOT), FFMT_PROFILES_FILE=str(PROFILES),
                       FFMT_FMT_DIR=str(ROOT / "third_party/fmt"))
    return checkout, source, revision, environment


def identity(checkout, source, revision):
    try:
        evaluation_commit = git(ROOT, "rev-parse", "HEAD")
    except subprocess.CalledProcessError:
        evaluation_commit = None
    return dict(evaluation_checkout=str(ROOT), evaluation_commit=evaluation_commit,
                evaluation_dirty=bool(git(ROOT, "status", "--porcelain")),
                runner_checkout=str(checkout), runner_commit=git(checkout, "rev-parse", "HEAD"),
                runner_dirty=bool(git(checkout, "status", "--porcelain")),
                source_checkout=str(source), source_revision=revision,
                source_commit=git(source, "rev-parse", "HEAD" if revision == "WORKTREE" else revision),
                source_worktree=revision == "WORKTREE", source_dirty=bool(git(source, "status", "--porcelain")),
                profiles_sha256=hashlib.sha256(PROFILES.read_bytes()).hexdigest(),
                configured_library_pin=LIBRARY_PIN)


def load_conformance(args):
    checkout, source, revision, environment = select_sources(args)
    os.environ.update({key: environment[key] for key in
                       ("FFMT_CHECKOUT", "FFMT_SOURCE_ROOT", "FFMT_WORKSPACE", "FFMT_PROFILES_FILE", "FFMT_FMT_DIR")})
    sys.path.insert(0, str(checkout / "tools"))
    spec = importlib.util.spec_from_file_location("ffmt_portable_conformance", checkout / "tools/conformance.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    args.revision = revision
    return module, checkout, source


def launch(tool, argv=None):
    parser = argparse.ArgumentParser(description="Run external ffmt " + tool + " with evaluation profiles", allow_abbrev=False)
    add_source_arguments(parser)
    parser.add_argument("--profile", default="local")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fmt-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Resolve inputs (populating a pinned checkout cache if needed) and print the command without executing the runner")
    args, extra = parser.parse_known_args(argv)
    profiles = json.loads(PROFILES.read_text())["profiles"]
    if args.profile not in profiles:
        parser.error("Unknown evaluation profile: " + args.profile)
    if args.profile != "local" and not args.dry_run and not os.environ.get("COBALT_JOBID"):
        parser.error("Representative JLSE runs require an active Cobalt allocation")
    try:
        checkout, source, revision, environment = select_sources(args)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.error(str(error))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = args.output or ROOT / "artifacts" / args.profile / (tool + "-" + stamp)
    if not output.is_absolute():
        output = ROOT / output
    command = [sys.executable, str(checkout / "tools" / (tool + ".py")),
               "--profiles", str(PROFILES), "--profile", args.profile,
               "--source-root", str(source), "--revision", revision,
               "--fmt-dir", str(args.fmt_dir or ROOT / "third_party/fmt"),
               "--output", str(output), *extra]
    record = dict(schema_version=1, tool=tool, started_utc=stamp, command=command,
                  output=str(output), profile=args.profile, cobalt_jobid=os.environ.get("COBALT_JOBID"),
                  sources=identity(checkout, source, revision),
                  launcher_files={str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in (ROOT / "tools/evaluation.py", ROOT / "tools" / (tool + ".py"))})
    discovery = ROOT / "artifacts" / args.profile / ("discovery-" + os.environ.get("COBALT_JOBID", "manual") + ".json")
    if discovery.is_file():
        record["discovery"] = dict(path=str(discovery), sha256=hashlib.sha256(discovery.read_bytes()).hexdigest())
    if args.dry_run:
        print(json.dumps(record, indent=2))
        return 0
    receipt = ROOT / "artifacts/launchers" / (tool + "-" + stamp + ".json")
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(record, indent=2) + "\n")
    process = subprocess.run(command, cwd=str(ROOT), env=environment)
    record.update(returncode=process.returncode, finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    manifest = output / "manifest.json"
    if manifest.is_file():
        record["manifest_sha256"] = hashlib.sha256(manifest.read_bytes()).hexdigest()
    receipt.write_text(json.dumps(record, indent=2) + "\n")
    print("Evaluation receipt: " + str(receipt), flush=True)
    return process.returncode
