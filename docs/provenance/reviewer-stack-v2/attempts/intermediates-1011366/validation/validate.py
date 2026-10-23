#!/usr/bin/env python3
"""Validate immutable ffmt review stages on an allocated CPU node.

The index names immutable library commits and newly affected capabilities. Each
compiler gets its own detached checkout and build products, so no compiler can
reuse another compiler's object files. Nothing is submitted or removed here.
"""
import argparse
from collections import Counter
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
CLANG = "/soft/compilers/llvm/release-22.1.8/bin/clang++"
GCC = "/soft/compilers/gcc/13.3.0/x86_64-suse-linux/bin/g++"
EVALUATION = Path(__file__).resolve().parents[2]
_RECORD_FATAL = None


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(repository, *arguments):
    return subprocess.check_output(
        ["git", "-C", str(repository), *arguments], text=True).strip()


def immutable_commit(repository, value):
    return (isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value)
            and git(repository, "rev-parse", value + "^{commit}") == value)


def registered_suites(source):
    """Read the explicit Make registrations, rather than infer tests from files."""
    suites = []
    seen = set()
    for path in sorted((source / "test/conformance/suites").glob("*.mk")):
        text = path.read_text()
        names = re.findall(r"^FFMT_CAPABILITIES[ \t]*\+=[ \t]*([A-Za-z0-9_]+)[ \t]*$", text, re.M)
        fields = {key: value.strip() for key, value in re.findall(
            r"^(FFMT_[A-Za-z0-9_]+)[ \t]*:?[=][ \t]*([^\r\n]*)$", text, re.M)}
        for name in names:
            if name in seen:
                raise ValueError("duplicate capability registration: " + name)
            seen.add(name)
            optional = fields.get("FFMT_OPTIONAL_" + name, "0")
            if optional not in ("0", "1"):
                raise ValueError("invalid optional capability marker: " + name)
            suites.append(dict(name=name, source=fields["FFMT_SOURCE_" + name],
                standard=fields["FFMT_STANDARD_" + name],
                flags=shlex.split(fields.get("FFMT_FLAGS_" + name, "")),
                reference=fields.get("FFMT_REFERENCE_" + name, "0") == "1",
                optional=optional == "1", registration=str(path.relative_to(source)),
                registration_sha256=digest(path)))
    if not suites:
        raise ValueError("integration stage has no registered capabilities")
    return suites


def command_arguments(command, values):
    """Substitute named paths in argv elements, without invoking a shell."""
    if not isinstance(command, list) or not command or not all(
            isinstance(part, (str, int, float)) for part in command):
        raise ValueError("validation_commands must contain nonempty argv lists")
    result = []
    for part in command:
        text = str(part)
        for key, value in values.items():
            text = text.replace("{" + key + "}", str(value))
        result.append(text)
    return result


def main():
    global _RECORD_FATAL
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path)
    parser.add_argument("--repo", type=Path, default=EVALUATION.parent / "ffmt")
    parser.add_argument("--fmt-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--clang", default=os.environ.get("FFMT_STACK_CLANG", CLANG))
    parser.add_argument("--gcc", default=os.environ.get("FFMT_STACK_GCC", GCC))
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--stage", action="append", help="Validate only this stage; repeatable")
    parser.add_argument("--preflight", action="store_true", help="Verify index and pins; do not compile")
    args = parser.parse_args()
    repository = args.repo.resolve()
    oracle = (args.fmt_dir or EVALUATION / "third_party/fmt").resolve()
    index_path = args.index.resolve()
    index = json.loads(index_path.read_text())
    entries = index.get("stages", [])
    if not entries or args.jobs < 1:
        parser.error("an index with stages and a positive --jobs count are required")
    by_id = {entry["id"]: entry for entry in entries}
    if len(by_id) != len(entries):
        parser.error("stage identifiers must be unique")
    if args.stage and set(args.stage) - by_id.keys():
        parser.error("unknown selected stage: " + ", ".join(sorted(set(args.stage) - by_id.keys())))
    for field in ("original_commit", "base_commit"):
        if not immutable_commit(repository, index.get(field)):
            parser.error(field + " must identify an available immutable commit")
    for entry in entries:
        for field in ("commit", "base_commit"):
            if not immutable_commit(repository, entry.get(field)):
                parser.error(entry["id"] + " " + field + " is not an immutable commit")
        for dependency in entry.get("dependencies", []):
            if dependency not in by_id:
                parser.error(entry["id"] + " has an unknown dependency: " + dependency)
            if subprocess.call(["git", "-C", str(repository), "merge-base", "--is-ancestor",
                                by_id[dependency]["commit"], entry["commit"]]):
                parser.error(entry["id"] + " does not contain dependency " + dependency)
        for command in entry.get("validation_commands", []):
            command_arguments(command, {})
        for suite in entry.get("suites", []):
            if not re.fullmatch(r"[A-Za-z0-9_]+", suite["name"]):
                parser.error("suite names must be valid cap_NAME target suffixes")
    if git(oracle, "rev-parse", "HEAD") != FMT_PIN or git(oracle, "status", "--porcelain"):
        parser.error("fmt checkout must be clean at the fixed oracle pin " + FMT_PIN)
    if args.preflight:
        print(f"Verified {len(entries)} immutable review stages, dependency ancestry and clean fmt pin.")
        return 0
    if not os.environ.get("COBALT_JOBID"):
        parser.error("compilation requires an allocated Cobalt compute node")

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = (args.output or EVALUATION / "artifacts/reviewer-v2" / ("validation-" + stamp)).resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "assembly-index.json").write_bytes(index_path.read_bytes())
    (output / "validate.py").write_bytes(Path(__file__).read_bytes())
    manifest = dict(
        schema_version=2, started=now(), status="running",
        purpose="CPU validation of reviewer-oriented intermediate commits; no hardware campaign",
        index=dict(path=str(index_path), sha256=digest(index_path)),
        runner=dict(path=str(Path(__file__).resolve()), sha256=digest(__file__)),
        evaluation=dict(checkout=str(EVALUATION), commit=git(EVALUATION, "rev-parse", "HEAD"),
                        dirty=bool(git(EVALUATION, "status", "--porcelain"))),
        library=dict(checkout=str(repository), original_commit=index["original_commit"],
                     base_commit=index["base_commit"]),
        fmt=dict(checkout=str(oracle), commit=FMT_PIN,
                 format_header_sha256=digest(oracle / "include/fmt/format.h"),
                 format_source_sha256=digest(oracle / "src/format.cc")),
        host=dict(name=socket.gethostname(), machine=platform.machine(), os=platform.platform()),
        cobalt_jobid=os.environ["COBALT_JOBID"], invocation=[sys.executable, *sys.argv],
        environment={key: os.environ[key] for key in (
            "PATH", "LD_LIBRARY_PATH", "LC_ALL", "COBALT_JOBID", "FFMT_STACK_CLANG", "FFMT_STACK_GCC")
            if key in os.environ}, setup=[], stages=[])
    wrapper = os.environ.get("FFMT_VALIDATION_WRAPPER")
    if wrapper and Path(wrapper).is_file():
        manifest["runner"]["wrapper"] = dict(path=wrapper, sha256=digest(wrapper))
        (output / "validate-cobalt.sh").write_bytes(Path(wrapper).read_bytes())

    def save():
        temporary = output / "manifest.json.tmp"
        temporary.write_text(json.dumps(manifest, indent=2) + "\n")
        temporary.replace(output / "manifest.json")

    def record_fatal(error):
        manifest.update(status="failure", finished=now(),
                        fatal_error=dict(type=type(error).__name__, message=str(error)))
        save()

    _RECORD_FATAL = record_fatal

    def step(target, directory, name, command, cwd=repository, environment=None,
             timeout=1800, optional=False):
        directory.mkdir(parents=True, exist_ok=True)
        stdout_path, stderr_path = directory / (name + ".stdout"), directory / (name + ".stderr")
        item = dict(name=name, command=[str(part) for part in command],
                    command_shell=shlex.join([str(part) for part in command]),
                    cwd=str(cwd), started=now(), timeout_seconds=timeout)
        if environment is not None:
            item["environment"] = {key: environment[key] for key in (
                "CXX", "FMT_DIR", "HOST_OPT", "EXTRA_CXXFLAGS", "FFMT_FMT_DIR",
                "FFMT_WORKSPACE", "FFMT_SOURCE_ROOT", "ASAN_OPTIONS", "UBSAN_OPTIONS",
                "FFMT_FLAGS_HOST_BUFFER", "FFMT_FLAGS_HOST_SPECIFIERS") if key in environment}
        started = time.monotonic()
        try:
            with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
                process = subprocess.Popen(item["command"], cwd=str(cwd), env=environment,
                                           stdout=stdout, stderr=stderr, start_new_session=True)
                try:
                    item["exit_code"] = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait()
                    item.update(exit_code=process.returncode, timeout=True)
        except OSError as error:
            stdout_path.touch()
            stderr_path.write_text(str(error) + "\n")
            item.update(exit_code=-1, infrastructure_error=str(error))
        item.update(finished=now(), seconds=time.monotonic() - started,
                    stdout_file=str(stdout_path), stdout_sha256=digest(stdout_path),
                    stderr_file=str(stderr_path), stderr_sha256=digest(stderr_path))
        item["status"] = ("pass" if item["exit_code"] == 0 else
                          "skip" if optional and item["exit_code"] == 77 else "failure")
        item["reported_skips"] = [line for line in stdout_path.read_text(errors="replace").splitlines()
                                  if re.search(r"\bSKIP(?:PED)?\b|\*\*\*Skipped|UNSUPPORTED:", line, re.I)]
        target.append(item)
        save()
        print(f"{name}: {item['status']}", flush=True)
        return item

    def status(steps):
        if any(item["status"] == "failure" for item in steps):
            return "failure"
        if any(item["status"] == "skip" or item.get("reported_skips") for item in steps):
            return "pass_with_skips"
        return "pass"

    def environment(compiler, directory, source, sanitizers):
        selected = dict(os.environ)
        for key in list(selected):
            if key.startswith("FFMT_CXX_") or key.startswith("FFMT_FLAGS_") or key in (
                    "FFMT_PROFILES_FILE", "FFMT_PROFILE", "CXXFLAGS", "CPPFLAGS", "LDFLAGS"):
                selected.pop(key)
        strict = "-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer" if sanitizers else ""
        selected.update(CXX=compiler, FMT_DIR=str(oracle), HOST_OPT="-O0" if sanitizers else "-O2",
                        EXTRA_CXXFLAGS=strict, FFMT_FMT_DIR=str(oracle),
                        FFMT_WORKSPACE=str(directory), FFMT_SOURCE_ROOT=str(source),
                        FFMT_FLAGS_HOST_BUFFER=strict, FFMT_FLAGS_HOST_SPECIFIERS=strict,
                        UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1",
                        ASAN_OPTIONS="detect_leaks=1:strict_string_checks=1:detect_stack_use_after_return=1",
                        LC_ALL="C", GOMAXPROCS="2")
        return selected

    save()
    for label, compiler in (("clang22", args.clang), ("gcc13", args.gcc)):
        step(manifest["setup"], output / "setup", label + "-version", [compiler, "--version"])
    step(manifest["setup"], output / "setup", "cmake-version", ["cmake", "--version"])
    step(manifest["setup"], output / "setup", "cpu", ["lscpu"])

    for entry in entries:
        if args.stage and entry["id"] not in args.stage:
            manifest["stages"].append(dict(id=entry["id"], commit=entry["commit"], status="not_selected"))
            save()
            continue
        directory = output / entry["id"]
        result = dict(**entry, status="running", started=now(), compilers=[], commands=[])
        result["tree"] = git(repository, "rev-parse", entry["commit"] + "^{tree}")
        manifest["stages"].append(result)
        compiler_rows = []
        for label, compiler, sanitized in (("clang22", args.clang, True), ("gcc13", args.gcc, False)):
            source = directory / label / "source"
            row = dict(name=label, executable=compiler, optimization="O0" if sanitized else "O2",
                       sanitizers=sanitized, source_checkout=str(source), steps=[], status="running")
            result["compilers"].append(row)
            compiler_rows.append((row, source, compiler, sanitized))
            checkout = step(row["steps"], directory / label, "checkout",
                            ["git", "worktree", "add", "--detach", str(source), entry["commit"]])
            row["checkout_succeeded"] = checkout["status"] == "pass"
            if not row["checkout_succeeded"]:
                row["status"] = "failure"
                continue
            tracked = git(source, "ls-files").splitlines()
            row["source_files"] = {name: digest(source / name) for name in tracked if (source / name).is_file()}
            env = environment(compiler, directory / label, source, sanitized)
            make = ["make", "-j" + str(args.jobs), "CXX=" + compiler, "FMT_DIR=" + str(oracle),
                    "HOST_OPT=" + env["HOST_OPT"], "EXTRA_CXXFLAGS=" + env["EXTRA_CXXFLAGS"]]
            def check(name, command, optional=False, timeout=1800):
                return step(row["steps"], directory / label, name, command, cwd=source,
                            environment=env, optional=optional, timeout=timeout)
            for header in ("base.hpp", "detail/checked.hpp"):
                if not (source / "include/ffmt" / header).is_file():
                    row["steps"].append(dict(name="header-" + header, status="not_applicable",
                                             reason="header has not been introduced at this stage"))
                    continue
                suffix = header.replace("/", "-").replace(".", "-")
                probe = directory / label / (suffix + ".cpp")
                probe.write_text("#include <ffmt/" + header + ">\nint main() { return 0; }\n")
                command = [compiler, "-std=c++20", "-O0" if sanitized else "-O2", "-fno-fast-math",
                           "-Wall", "-Werror", "-I" + str(source / "include")]
                if sanitized:
                    command += shlex.split(env["EXTRA_CXXFLAGS"])
                command += ["-c", str(probe), "-o", str(probe.with_suffix(".o"))]
                check("header-" + suffix, command)
            suites = entry.get("suites", [])
            if entry["id"] in ("migration", "complete"):
                suites = registered_suites(source)
                row["suite_selection"] = "all explicit Make registrations"
                row["registered_suites"] = suites
            else:
                row["suite_selection"] = "newly affected suites from immutable assembly index"
            for suite in suites:
                name = suite["name"]
                build = check("build-" + name, make + ["build/cap_" + name])
                if build["status"] == "pass":
                    executable = source / "build" / ("cap_" + name)
                    if executable.is_file():
                        build["binary_sha256"] = digest(executable)
                    check("run-" + name, [str(executable)], optional=bool(suite.get("optional", False)))
                else:
                    row["steps"].append(dict(name="run-" + name, status="not_run", reason="capability build failed"))
            if entry["id"] in ("migration", "complete"):
                check("legacy-test-host", make + ["test-host"])
            row["status"] = status(row["steps"])
            save()

        # Python/driver commands run once per immutable stage, with Clang selected.
        row, source, compiler, sanitized = compiler_rows[0]
        if row.get("checkout_succeeded"):
            env = environment(compiler, directory / "commands", source, sanitized)
            substitutions = dict(source=source, fmt_dir=oracle, output=directory / "commands",
                                 cxx=compiler, repo=repository, revision=entry["commit"], python=sys.executable)
            for number, command in enumerate(entry.get("validation_commands", []), 1):
                step(result["commands"], directory / "commands", f"command-{number:02d}",
                     command_arguments(command, substitutions), cwd=source, environment=env)

        if entry["id"] == "complete" and row.get("checkout_succeeded"):
            env = environment(args.clang, directory / "cmake-evidence", source, False)
            build, prefix = directory / "cmake", directory / "install"
            def final_step(name, command, timeout=1800):
                return step(result["commands"], directory / "cmake-evidence", name, command,
                            cwd=source, environment=env, timeout=timeout)
            configured = final_step("cmake-configure", ["cmake", "-S", str(source), "-B", str(build),
                "-DFFMT_BUILD_TESTS=ON", "-DFFMT_BUILD_CXX23_TESTS=ON", "-DCMAKE_BUILD_TYPE=Release",
                "-DCMAKE_CXX_COMPILER=" + args.clang, "-DFFMT_FMT_DIR=" + str(oracle),
                "-DCMAKE_INSTALL_PREFIX=" + str(prefix)])
            built = configured["status"] == "pass" and final_step("cmake-build",
                ["cmake", "--build", str(build), "-j" + str(args.jobs)])["status"] == "pass"
            if built:
                final_step("ctest", ["ctest", "--test-dir", str(build), "--output-on-failure", "--no-tests=error", "-j2"], timeout=3600)
                installed = final_step("cmake-install", ["cmake", "--install", str(build)])
                if installed["status"] == "pass":
                    consumer = directory / "consumer"
                    consumer.mkdir()
                    (consumer / "CMakeLists.txt").write_text(
                        "cmake_minimum_required(VERSION 3.19)\nproject(consumer LANGUAGES CXX)\n"
                        "find_package(ffmt CONFIG REQUIRED)\nadd_executable(consumer main.cpp)\n"
                        "target_link_libraries(consumer PRIVATE ffmt::ffmt)\n")
                    (consumer / "main.cpp").write_text(
                        "#include <ffmt/base.hpp>\n#include <cstring>\n"
                        "int main() { char out[8] = {}; auto r = ffmt::format_to_n(out, sizeof out, \"{:04x}\", 42); "
                        "return !r || r.written != 4 || r.required != 4 || std::memcmp(out, \"002a\", 4) != 0; }\n")
                    manifest.setdefault("consumer_sources", {})[str(consumer)] = {
                        path.name: digest(path) for path in consumer.iterdir() if path.is_file()}
                    ready = final_step("consumer-configure", ["cmake", "-S", str(consumer),
                        "-B", str(consumer / "build"), "-DCMAKE_CXX_COMPILER=" + args.clang,
                        "-DCMAKE_PREFIX_PATH=" + str(prefix)])["status"] == "pass"
                    if ready and final_step("consumer-build", ["cmake", "--build", str(consumer / "build"),
                                                              "-j2"])["status"] == "pass":
                        final_step("consumer-run", [str(consumer / "build/consumer")])
            else:
                result["blocked_checks"] = ["ctest", "cmake-install", "installed-consumer"]
        all_steps = result["commands"] + [item for row in result["compilers"] for item in row["steps"]]
        result.update(status=status(all_steps), finished=now())
        save()
    all_steps = manifest["setup"] + [step for stage in manifest["stages"]
        for step in stage.get("commands", [])] + [step for stage in manifest["stages"]
        for compiler in stage.get("compilers", []) for step in compiler["steps"]]
    manifest.update(finished=now(), status=status(all_steps),
                    counts=dict(Counter(step["status"] for step in all_steps)))
    save()
    print("Validation evidence: " + str(output / "manifest.json"), flush=True)
    return int(manifest["status"] == "failure")


if __name__ == "__main__":
    try:
        exit_code = main()
    except BaseException as error:
        if _RECORD_FATAL is not None:
            _RECORD_FATAL(error)
        raise
    raise SystemExit(exit_code)
