#!/usr/bin/env python3
"""Correct only the generated installed-package consumer fixture from 1011211."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import socket
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("--cxx", default=os.environ.get("FFMT_STACK_CXX", "clang++"))
    args = parser.parse_args()
    if not os.environ.get("COBALT_JOBID"):
        parser.error("requires a CPU-only Cobalt allocation")
    original = args.original.resolve()
    prior = json.loads(original.read_text())
    integration = next(s for s in prior["stages"] if s["stage"] == "integration")
    prefix = original.parent / "integration/install"
    output = original.parent.parent / ("consumer-validation-" + os.environ["COBALT_JOBID"])
    output.mkdir(parents=True, exist_ok=False)
    source = output / "consumer"
    source.mkdir()
    (source / "CMakeLists.txt").write_text('cmake_minimum_required(VERSION 3.19)\nproject(consumer LANGUAGES CXX)\nfind_package(ffmt CONFIG REQUIRED)\nadd_executable(consumer main.cpp)\ntarget_link_libraries(consumer PRIVATE ffmt::ffmt)\n')
    (source / "main.cpp").write_text('#include <ffmt/base.hpp>\n#include <cstring>\nint main() { char out[8] = {}; auto r = ffmt::format_to_n(out, sizeof out, "{:04x}", 42); return !r || r.written != 4 || r.required != 4 || std::memcmp(out, "002a", 4) != 0; }\n')
    manifest = dict(schema_version=1, status="running", cobalt_jobid=os.environ["COBALT_JOBID"],
        hostname=socket.gethostname(), invocation=[sys.executable, *sys.argv],
        source_commit=integration["commit"], source_tree=integration["tree"], fmt_commit=prior["fmt_commit"],
        installed_prefix=str(prefix), original_attempt=dict(path=str(original), sha256=sha(original),
            cobalt_jobid=prior["cobalt_jobid"], status=prior["status"],
            failed_step="package-consumer-build", failure_classification="test_fixture_error",
            explanation="Generated fixture included internal core.hpp directly; its documented inclusion contract requires base.hpp, which is the public entry used by README and the library regressions."),
        policy="Only correct the generated consumer include; no library source/history change, no repeated full suite or GPU campaign.",
        runner=dict(path=str(Path(__file__).resolve()), sha256=sha(__file__)),
        consumer_sources={p.name: dict(path=str(p), sha256=sha(p)) for p in source.iterdir() if p.is_file()},
        installed_headers={}, steps=[])
    for path in sorted((prefix / "include").rglob("*.hpp")):
        relative = "include/" + str(path.relative_to(prefix / "include"))
        actual, expected = sha(path), integration["source_files"][relative]
        manifest["installed_headers"][relative] = dict(sha256=actual, expected_sha256=expected, matches=actual == expected)
    def save():
        temp = output / "manifest.json.tmp"
        temp.write_text(json.dumps(manifest, indent=2) + "\n")
        temp.replace(output / "manifest.json")
    save()
    if not all(row["matches"] for row in manifest["installed_headers"].values()):
        manifest.update(status="failure", reason="installed header differs from immutable integration source")
        save()
        return 1
    commands = [("compiler-version", [args.cxx, "--version"]),
        ("configure", ["cmake", "-S", str(source), "-B", str(source / "build"),
            "-DCMAKE_CXX_COMPILER=" + args.cxx, "-DCMAKE_PREFIX_PATH=" + str(prefix)]),
        ("build", ["cmake", "--build", str(source / "build"), "-j2"]),
        ("run", [str(source / "build/consumer")])]
    for name, command in commands:
        start = time.monotonic()
        stdout, stderr = output / (name + ".stdout"), output / (name + ".stderr")
        item = dict(name=name, command=command, command_shell=shlex.join(command), cwd=str(source), timeout_seconds=180)
        with stdout.open("wb") as out, stderr.open("wb") as err:
            process = subprocess.Popen(command, cwd=str(source), stdout=out, stderr=err, start_new_session=True)
            try:
                item["exit_code"] = process.wait(timeout=180)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                item.update(exit_code=process.returncode, timeout=True)
        item.update(seconds=time.monotonic() - start, status="pass" if item["exit_code"] == 0 else "failure",
            stdout_file=str(stdout), stdout_sha256=sha(stdout), stderr_file=str(stderr), stderr_sha256=sha(stderr))
        manifest["steps"].append(item)
        save()
        print(name + ": " + item["status"], flush=True)
        if item["exit_code"]:
            break
    manifest.update(status="pass" if len(manifest["steps"]) == 4 and all(s["status"] == "pass" for s in manifest["steps"]) else "failure",
        finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save()
    print("Consumer evidence: " + str(output / "manifest.json"), flush=True)
    return int(manifest["status"] != "pass")


if __name__ == "__main__":
    raise SystemExit(main())
