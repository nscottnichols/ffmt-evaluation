#!/usr/bin/env python3
"""Validate and freeze a provisioned release after dual-account CI qualification."""
import argparse
import datetime
import grp
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
from urllib.parse import urlparse

REQUIRED_ACCOUNTS = frozenset({"nnichols", "bertoni"})
FULL_COMMIT = re.compile(r"[0-9a-f]{40}\Z")


class ReleaseError(Exception):
    pass


def validate_root(value):
    root = Path(value)
    if not root.is_absolute() or ".." in root.parts:
        raise ReleaseError("deployment root must be an absolute path without '..'")
    if root.is_symlink() or root.parent.name != "releases" or not root.name:
        raise ReleaseError("deployment root must be a real .../releases/<id> directory")
    if not root.is_dir():
        raise ReleaseError(f"deployment root is not a directory: {root}")
    return root


def validate_commit(value):
    if not isinstance(value, str) or not FULL_COMMIT.fullmatch(value):
        raise ReleaseError("tested commit must be a full lowercase Git commit ID")
    return value


def release_path(value, root, label, external=False):
    if not isinstance(value, str):
        raise ReleaseError(f"{label} must be a path string")
    path = Path(value)
    if not path.is_absolute() or ".." in path.parts:
        raise ReleaseError(f"{label} must be absolute and contain no '..'")
    try:
        path.relative_to(root)
        resolved = path.resolve(strict=True)
        if not external:
            resolved.relative_to(root.resolve())
    except (ValueError, OSError) as error:
        raise ReleaseError(f"{label} must name an existing path inside the release: {path}") from error
    return path


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(source, *arguments):
    try:
        return subprocess.check_output(["git", "-C", str(source), *arguments], stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        diagnostic = error.stderr.decode(errors="replace").strip()
        raise ReleaseError(f"Git verification failed for {source}: {diagnostic}") from error


def cmake_source(build_directory):
    cache = build_directory / "CMakeCache.txt"
    try:
        lines = cache.read_text().splitlines()
    except OSError as error:
        raise ReleaseError(f"cannot read CMake source identity: {cache}") from error
    prefix = "CMAKE_HOME_DIRECTORY:INTERNAL="
    for line in lines:
        if line.startswith(prefix):
            return line[len(prefix):]
    raise ReleaseError(f"CMake source identity is missing from {cache}")


def verify_hash(path, expected, label):
    if not isinstance(expected, str) or file_sha256(path) != expected:
        raise ReleaseError(f"SHA-256 mismatch for {label}: {path}")


def verify_component(record, root, label):
    paths = {}
    for field in ("prefix", "source", "build_directory", "archive"):
        if field in record:
            paths[field] = release_path(record[field], root, f"{label}.{field}")
    if "archive" in paths:
        verify_hash(paths["archive"], record.get("sha256"), f"{label}.archive")
    if "path" in record:
        external = "target" in record
        path = release_path(record["path"], root, f"{label}.path", external=external)
        if external:
            target = record["target"]
            if not isinstance(target, str) or not Path(target).is_absolute() or not path.is_symlink():
                raise ReleaseError(f"{label} external runtime path must be an absolute symlink")
            if Path(os.readlink(path)) != Path(target):
                raise ReleaseError(f"{label} symlink does not match its recorded target")
    adapter = record.get("typed_pointer_adapter")
    if adapter is not None:
        if not isinstance(adapter, dict):
            raise ReleaseError(f"{label}.typed_pointer_adapter must be an object")
        adapter_path = release_path(adapter.get("path"), root, f"{label} adapter path")
        translator = release_path(adapter.get("translator"), root, f"{label} translator")
        verify_hash(adapter_path, adapter.get("sha256"), f"{label} adapter")
        verify_hash(translator, adapter.get("translator_sha256"), f"{label} translator")
    if "source_commit" in record or "source_patch_sha256" in record:
        if "source_commit" not in record or "source_patch_sha256" not in record:
            raise ReleaseError(f"{label} must record both source commit and patch hash")
        source_value = record.get("source") or cmake_source(paths.get("build_directory", Path("missing")))
        source = release_path(source_value, root, f"{label} source")
        commit = git_output(source, "rev-parse", "HEAD").decode().strip()
        if commit != record["source_commit"]:
            raise ReleaseError(f"source commit mismatch for {label}")
        patch_hash = hashlib.sha256(git_output(source, "diff", "--binary")).hexdigest()
        if patch_hash != record["source_patch_sha256"]:
            raise ReleaseError(f"source patch SHA-256 mismatch for {label}")


def aggregate_components(root):
    base = root / "manifests/components"
    aggregated = {}
    for manifest_path in sorted(base.glob("*/*/manifest.json")):
        job = json.loads(manifest_path.read_text())
        if job.get("deployment_root") != str(root):
            raise ReleaseError(f"component manifest names another release: {manifest_path}")
        scope = job.get("storage_scope")
        if not isinstance(scope, str) or not scope or Path(scope).name != scope or scope in (".", ".."):
            raise ReleaseError(f"invalid storage scope in {manifest_path}")
        components = job.get("components")
        if not isinstance(components, dict):
            raise ReleaseError(f"invalid component map in {manifest_path}")
        for name, original in components.items():
            if not isinstance(name, str) or not name or not isinstance(original, dict):
                raise ReleaseError(f"invalid component record in {manifest_path}")
            if original.get("status") != "installed":
                continue
            if name in aggregated.setdefault(scope, {}):
                raise ReleaseError(f"duplicate installed component: {scope}/{name}")
            verify_component(original, root, f"{scope}/{name}")
            record = dict(original)
            record.update(profile=job.get("profile"), cobalt_jobid=job.get("cobalt_jobid"),
                          provisioning_manifest=manifest_path.relative_to(root).as_posix())
            aggregated[scope][name] = record
    if not any(aggregated.values()):
        raise ReleaseError("no installed component records were found")
    return aggregated


def pipeline_time(value, label):
    if not isinstance(value, str):
        raise ReleaseError(f"{label} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ReleaseError(f"{label} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ReleaseError(f"{label} must include a timezone")
    return parsed


def validate_qualification(evidence, account, root, tested_commit):
    if evidence.get("account") != account:
        raise ReleaseError(f"qualification account mismatch for {account}")
    if evidence.get("release_root") != str(root):
        raise ReleaseError(f"qualification release root mismatch for {account}")
    if evidence.get("tested_commit") != tested_commit:
        raise ReleaseError(f"qualification tested commit mismatch for {account}")
    pipeline = evidence.get("pipeline")
    if not isinstance(pipeline, dict) or pipeline.get("status") not in {"success", "failed"}:
        raise ReleaseError(f"unsupported qualification pipeline status for {account}")
    user = pipeline.get("user")
    if not isinstance(user, dict) or user.get("username") != account:
        raise ReleaseError(f"qualification pipeline user mismatch for {account}")
    if pipeline.get("sha") != tested_commit:
        raise ReleaseError(f"qualification pipeline commit mismatch for {account}")
    pipeline_id = pipeline.get("id")
    if isinstance(pipeline_id, bool) or not isinstance(pipeline_id, int) or pipeline_id <= 0:
        raise ReleaseError(f"invalid qualification pipeline ID for {account}")
    web_url = pipeline.get("web_url")
    if not isinstance(web_url, str):
        raise ReleaseError(f"invalid qualification pipeline URL for {account}")
    url = urlparse(web_url)
    if url.scheme != "https" or not url.netloc or not url.path.endswith(f"/pipelines/{pipeline_id}"):
        raise ReleaseError(f"invalid qualification pipeline URL for {account}")
    created = pipeline_time(pipeline.get("created_at"), f"{account} pipeline creation")
    updated = pipeline_time(pipeline.get("updated_at"), f"{account} pipeline update")
    if updated < created:
        raise ReleaseError(f"qualification pipeline timestamps are reversed for {account}")
    jobs = pipeline.get("qualified_jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ReleaseError(f"qualification requires successful runtime-consuming jobs for {account}")
    job_ids = set()
    for job in jobs:
        if not isinstance(job, dict) or job.get("status") != "success":
            raise ReleaseError(f"qualified job was not successful for {account}")
        name = job.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ReleaseError(f"qualified job name is missing for {account}")
        job_id = job.get("id")
        if isinstance(job_id, bool) or not isinstance(job_id, int) or job_id <= 0 or job_id in job_ids:
            raise ReleaseError(f"invalid or duplicate qualified job ID for {account}")
        job_url = job.get("web_url")
        if not isinstance(job_url, str):
            raise ReleaseError(f"invalid qualified job URL for {account}")
        parsed_job_url = urlparse(job_url)
        if (parsed_job_url.scheme != "https" or not parsed_job_url.netloc or
                not parsed_job_url.path.endswith(f"/jobs/{job_id}")):
            raise ReleaseError(f"invalid qualified job URL for {account}")
        job_ids.add(job_id)
    return dict(evidence, status="qualified")


def load_qualifications(paths, root, tested_commit):
    if set(paths) != REQUIRED_ACCOUNTS:
        raise ReleaseError("qualification evidence is required for nnichols and bertoni")
    return {account: validate_qualification(json.loads(path.read_text()), account, root, tested_commit)
            for account, path in paths.items()}


def run_access_command(arguments):
    result = subprocess.run(arguments, capture_output=True, text=True)
    if result.returncode:
        raise ReleaseError(result.stderr.strip() or f"access command failed: {arguments}")


def verify_access(root, group):
    group_id = grp.getgrnam(group).gr_gid
    paths = itertools.chain((root,), root.rglob("*"))
    for path in paths:
        metadata = path.lstat()
        if metadata.st_gid != group_id:
            raise ReleaseError(f"release entry has the wrong access group: {path}")
        required = stat.S_IRGRP | (stat.S_IXGRP if stat.S_ISDIR(metadata.st_mode) else 0)
        if not stat.S_ISLNK(metadata.st_mode) and metadata.st_mode & required != required:
            raise ReleaseError(f"release entry lacks group read/search access: {path}")


def normalize_access(root, group):
    run_access_command(["chgrp", "-R", "-h", "--", group, str(root)])
    run_access_command(["chmod", "-R", "g+rX", str(root)])
    verify_access(root, group)


def atomic_write_json(path, value):
    original = path.stat()
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=".release-", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            json.dump(value, output, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.chown(temporary, -1, original.st_gid)
        os.chmod(temporary, stat.S_IMODE(original.st_mode))
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def finalize_release(root, access_group, tested_commit, qualification_paths):
    root = validate_root(root)
    tested_commit = validate_commit(tested_commit)
    manifest_path = root / "manifests/release.json"
    release = json.loads(manifest_path.read_text())
    if release.get("state") != "provisioning":
        raise ReleaseError("only a provisioning release can be finalized")
    if release.get("access_group") != access_group:
        raise ReleaseError("release access group does not match the requested group")
    qualifications = load_qualifications(qualification_paths, root, tested_commit)
    components = aggregate_components(root)
    normalize_access(root, access_group)
    release.update(state="ready", frozen=True,
                   frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   tested_commit=tested_commit, components=components,
                   qualification=qualifications,
                   access={"group": access_group, "status": "normalized"})
    atomic_write_json(manifest_path, release)
    return release


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deployment-root", required=True)
    parser.add_argument("--access-group", required=True)
    parser.add_argument("--tested-commit", required=True)
    parser.add_argument("--qualification", action="append", required=True, metavar="ACCOUNT=JSON")
    arguments = parser.parse_args(argv)
    qualifications = {}
    for value in arguments.qualification:
        account, separator, path = value.partition("=")
        if not separator or account in qualifications:
            parser.error("--qualification requires unique ACCOUNT=JSON entries")
        qualifications[account] = Path(path)
    return arguments, qualifications


def main(argv=None):
    arguments, qualifications = parse_args(argv)
    try:
        release = finalize_release(arguments.deployment_root, arguments.access_group,
                                   arguments.tested_commit, qualifications)
    except (ReleaseError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise SystemExit(str(error))
    print(f"{release['release']}: ready and frozen at {release['tested_commit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
