#!/usr/bin/env python3
"""Validate immutable review-stack prefixes on one CPU-only Cobalt node.

This runner is deliberately outside the library tree. It writes fresh detached
worktrees, exact commands, raw logs, source hashes, and explicit failures/skips.
It never changes source commits or submits a scheduler job.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import signal
import socket
import subprocess
import sys
import time

FMT_PIN = "0fc31633e7d53ac895ae0a688b83b7d44f0b0c1f"
STAGES = ("infra", "core", "ranges", "families", "printf", "bench", "integration")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--fmt-dir", type=Path)
    parser.add_argument("--cxx", default=os.environ.get("FFMT_STACK_CXX", "clang++"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--stage", action="append", choices=STAGES)
    parser.add_argument("--preflight", action="store_true", help="Check index and pins without compiling")
    args = parser.parse_args()
    repo = args.repo.resolve()
    oracle = (args.fmt_dir or repo / "third_party/fmt").resolve()
    index_path = args.index.resolve()
    index = json.loads(index_path.read_text())
    entries = index["stages"]
    if [row["stage"] for row in entries] != list(STAGES):
        parser.error("index must contain infra/core/ranges/families/printf/bench/integration in order")
    for row in entries:
        resolved = git(repo, "rev-parse", row["commit"] + "^{commit}")
        if resolved != row["commit"]:
            parser.error("all index commits must use full immutable SHAs")
    if git(oracle, "rev-parse", "HEAD") != FMT_PIN or git(oracle, "status", "--porcelain"):
        parser.error("fmt checkout must be clean and at the fixed oracle pin")
    original = git(repo, "rev-parse", index["original_commit"] + "^{commit}")
    final = entries[-1]["commit"]
    if git(repo, "rev-parse", original + "^{tree}") != git(repo, "rev-parse", final + "^{tree}"):
        parser.error("integration tree differs from the originally reviewed library tree")
    if args.preflight:
        print("Seven immutable prefixes, oracle pin, and final source-tree identity verified.")
        return 0
    if not os.environ.get("COBALT_JOBID"):
        parser.error("heavy validation requires an allocated Cobalt compute node")
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = (args.output or repo / "artifacts/review-stack" / ("validation-" + stamp)).resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "stack-index.json").write_bytes(index_path.read_bytes())
    manifest = dict(schema_version=1, started=now(), status="running",
        runner=dict(path=str(Path(__file__).resolve()), sha256=digest(__file__)),
        index=dict(path=str(index_path), sha256=digest(index_path)),
        repo=str(repo), original_commit=original, original_tree=git(repo, "rev-parse", original + "^{tree}"),
        final_commit=final, final_tree=git(repo, "rev-parse", final + "^{tree}"),
        fmt_commit=FMT_PIN, fmt_checkout=str(oracle), cobalt_jobid=os.environ["COBALT_JOBID"],
        host=socket.gethostname(), machine=platform.machine(), invocation=[sys.executable, *sys.argv],
        environment={k: os.environ[k] for k in ("CXX", "FFMT_STACK_CXX", "LD_LIBRARY_PATH", "PATH") if k in os.environ},
        policy="CPU-only review-prefix validation; no hardware campaign repeated", stages=[], setup=[])

    def save():
        temporary = output / "manifest.json.tmp"
        temporary.write_text(json.dumps(manifest, indent=2) + "\n")
        temporary.replace(output / "manifest.json")

    def step(target, folder, name, command, cwd=repo, timeout=1800, env=None):
        folder.mkdir(parents=True, exist_ok=True)
        start = time.monotonic()
        item = dict(name=name, command=[str(x) for x in command], command_shell=shlex.join([str(x) for x in command]),
            cwd=str(cwd), started=now(), timeout_seconds=timeout)
        stdout_file, stderr_file = folder / (name + ".stdout"), folder / (name + ".stderr")
        try:
            with stdout_file.open("wb") as stdout, stderr_file.open("wb") as stderr:
                proc = subprocess.Popen(item["command"], cwd=str(cwd), env=env,
                    stdout=stdout, stderr=stderr, start_new_session=True)
                try:
                    item["exit_code"] = proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait()
                    item.update(exit_code=proc.returncode, timeout=True)
        except OSError as error:
            stderr_file.write_text(str(error) + "\n")
            stdout_file.touch()
            item.update(exit_code=-1, infrastructure_error=str(error))
        item.update(finished=now(), seconds=time.monotonic() - start,
            stdout_file=str(stdout_file), stdout_sha256=digest(stdout_file),
            stderr_file=str(stderr_file), stderr_sha256=digest(stderr_file))
        item["status"] = "pass" if item["exit_code"] == 0 else "skip" if item["exit_code"] == 77 else "failure"
        item["reported_skips"] = [line for line in stdout_file.read_text(errors="replace").splitlines()
            if re.search(r"\bSKIP\b|\*\*\*Skipped", line)]
        target.append(item)
        save()
        print(name + ": " + item["status"], flush=True)
        return item["status"] == "pass"

    save()
    step(manifest["setup"], output / "setup", "compiler-version", [args.cxx, "--version"])
    step(manifest["setup"], output / "setup", "cmake-version", ["cmake", "--version"])
    step(manifest["setup"], output / "setup", "cpu", ["lscpu"])
    for entry in entries:
        if args.stage and entry["stage"] not in args.stage:
            manifest["stages"].append(dict(**entry, status="not_selected", reason="--stage selection"))
            save()
            continue
        name = entry["stage"]
        directory, source = output / name, output / name / "source"
        result = dict(**entry, status="running", steps=[], source_checkout=str(source),
            tree=git(repo, "rev-parse", entry["commit"] + "^{tree}"))
        manifest["stages"].append(result)
        if not step(result["steps"], directory, "checkout", ["git", "worktree", "add", "--detach", str(source), entry["commit"]]):
            result.update(status="failure", reason="detached checkout failed")
            save()
            continue
        result["source_files"] = {p: digest(source / p) for p in git(source, "ls-files").splitlines() if (source / p).is_file()}
        # Preserve the exact portable tools' own evidence separately for each prefix.
        environment = dict(os.environ, CXX=args.cxx, FFMT_FMT_DIR=str(oracle),
            FFMT_WORKSPACE=str(directory), FFMT_SOURCE_ROOT=str(source),
            UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1",
            ASAN_OPTIONS="detect_leaks=1:strict_string_checks=1:detect_stack_use_after_return=1")
        for key in list(environment):
            if key.startswith("FFMT_CXX_") or key in ("FFMT_PROFILES_FILE", "FFMT_PROFILE"):
                environment.pop(key)
        make = ["make", "-j" + str(args.jobs), "CXX=" + args.cxx, "FMT_DIR=" + str(oracle), "HOST_OPT=-O0",
            "EXTRA_CXXFLAGS=-fsanitize=address,undefined"]
        def check(label, command, timeout=1800):
            return step(result["steps"], directory, label, command, cwd=source, timeout=timeout, env=environment)
        if name == "infra":
            check("harness", make + ["conformance-harness"])
            check("legacy-host-sanity", make + ["test-host"])
            check("negative-sanity", make + ["test-negative"])
        elif name in ("core", "ranges", "families", "printf"):
            check("focused-sanitized-O0", make + ["test-focused"])
            if name == "core":
                check("legacy-host-sanitized-O0", make + ["test-host"])
                check("negative-sanitized", make + ["test-negative"])
            if name in ("families", "printf"):
                check("optional-cxx23-sanitized-O0", make + ["test-cxx23"])
            if name == "printf":
                check("negative-final-families", make + ["test-negative"])
        elif name == "bench":
            check("host-memory-benchmark-smoke", [sys.executable, "tools/benchmark.py", "--profile", "local",
                "--route", "host-buffer", "--revision", entry["commit"], "--source-root", str(source),
                "--fmt-dir", str(oracle), "--family", "integer", "--mode", "memory", "--capacity", "128",
                "--memory-iterations", "32", "--output", str(directory / "benchmark-smoke")])
        else:
            build, prefix = directory / "cmake", directory / "install"
            configured = check("cmake-configure", ["cmake", "-S", str(source), "-B", str(build),
                "-DFFMT_BUILD_TESTS=ON", "-DFFMT_BUILD_CXX23_TESTS=ON", "-DCMAKE_BUILD_TYPE=Release",
                "-DCMAKE_CXX_COMPILER=" + args.cxx, "-DFFMT_FMT_DIR=" + str(oracle), "-DCMAKE_INSTALL_PREFIX=" + str(prefix)])
            built = configured and check("cmake-build", ["cmake", "--build", str(build), "-j" + str(args.jobs)])
            if built:
                check("ctest-full-host-conformance", ["ctest", "--test-dir", str(build), "--output-on-failure", "-j2"], timeout=1800)
                check("cmake-install", ["cmake", "--install", str(build)])
                consumer = directory / "consumer"
                consumer.mkdir()
                (consumer / "CMakeLists.txt").write_text('cmake_minimum_required(VERSION 3.19)\nproject(consumer LANGUAGES CXX)\nfind_package(ffmt CONFIG REQUIRED)\nadd_executable(consumer main.cpp)\ntarget_link_libraries(consumer PRIVATE ffmt::ffmt)\n')
                (consumer / "main.cpp").write_text('#include <ffmt/core.hpp>\n#include <cstring>\nint main() { char out[8] = {}; auto r = ffmt::format_to_n(out, sizeof out, "{:04x}", 42); return !r || r.written != 4 || r.required != 4 || std::memcmp(out, "002a", 4) != 0; }\n')
                ok = check("package-consumer-configure", ["cmake", "-S", str(consumer), "-B", str(consumer / "build"),
                    "-DCMAKE_CXX_COMPILER=" + args.cxx, "-DCMAKE_PREFIX_PATH=" + str(prefix)])
                if ok and check("package-consumer-build", ["cmake", "--build", str(consumer / "build"), "-j2"]):
                    check("package-consumer-run", [str(consumer / "build/consumer")])
            else:
                result["blocked_checks"] = ["ctest-full-host-conformance", "cmake-install", "package-consumer"]
        result["status"] = "failure" if any(item["status"] == "failure" for item in result["steps"]) else "pass"
        result["finished"] = now()
        save()
    manifest.update(finished=now(), status="failure" if any(s["status"] == "failure" for s in manifest["stages"]) or any(s["status"] == "failure" for s in manifest["setup"]) else "pass")
    save()
    print("Validation evidence: " + str(output / "manifest.json"), flush=True)
    return int(manifest["status"] != "pass")


if __name__ == "__main__":
    raise SystemExit(main())
