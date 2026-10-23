#!/usr/bin/env python3
"""Assemble review snapshots from the preserved library checkout.

This orchestration script is untracked. Exported source is ordinary handwritten
Python/C++, and every export remains available for normal review.
"""
import ast
import json
from pathlib import Path
import shutil
import subprocess
import textwrap
import io
import tokenize
import shlex

PROJECT = Path(__file__).resolve().parent
SOURCE = PROJECT / 'tool-source'
EXPORT = PROJECT / 'tool-stages'
ORIGINAL = subprocess.check_output(['git', 'show', 'aeff043:tools/conformance.py'], cwd=SOURCE, text=True)
TESTS = subprocess.check_output(['git', 'show', 'aeff043:test/conformance/test_runner.py'], cwd=SOURCE, text=True)
NUMERIC = subprocess.check_output(['git', 'show', 'aeff043:tools/numeric_memory.py'], cwd=SOURCE, text=True)

def node(text, name):
    for item in ast.parse(text).body:
        if getattr(item, 'name', None) == name:
            return ast.get_source_segment(text, item)
    raise KeyError(name)

def method(text, name):
    for item in ast.parse(text).body:
        if isinstance(item, ast.ClassDef):
            for member in item.body:
                if getattr(member, 'name', None) == name:
                    return textwrap.dedent(' ' * member.col_offset + ast.get_source_segment(text, member))
    raise KeyError(name)

def stage(identifier, title, files, dependencies=(), remove=(), problem='', example='',
          design='', tradeoffs='', reading_order=(), tests=(), change_kind='source-refactor', docs=''):
    files = dict(files)
    documentation = '# ' + title + '\n\n' + problem + '\n\n' + example + '\n\n' + design + '\n\n' + tradeoffs + '\n\n' + docs + '\n'
    if tests:
        commands = [shlex.join([str(part) for part in command]) if isinstance(command, list) else command
                    for command in tests]
        documentation += '\nValidation:\n\n```sh\n' + '\n'.join(commands) + '\n```\n'
    files['docs/conformance/' + identifier + '.md'] = documentation
    directory = EXPORT / identifier
    if directory.exists():
        shutil.rmtree(directory)
    for name, content in files.items():
        path = directory / 'files' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        # Normalize only the file terminator, never whitespace inside a source
        # literal or handwritten C++ template.
        path.write_text(content.rstrip('\n') + '\n')
    metadata = dict(id=identifier, title=title, dependencies=list(dependencies),
                    change_kind=change_kind, remove=list(remove), tests=list(tests),
                    problem=problem, example=example, design=design, tradeoffs=tradeoffs,
                    reading_order=list(reading_order), docs=docs)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'stage.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return files

TEST_IMPORTS = '''"""Focused regressions for portable conformance infrastructure."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
'''

PROCESS = '''"""Capture exact process evidence and terminate timed-out process groups."""
import base64
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]

'''
for name in ('path_label', 'compare_bytes', 'run', 'record'):
    PROCESS += node(ORIGINAL, name) + '\n\n'

process_files = {
    'tools/process_evidence.py': PROCESS,
    'test/conformance/test_process.py': TEST_IMPORTS + '\nimport process_evidence as runner\n\n' + node(TESTS, 'ProcessLifetimeTests') + '\n',
    'test/conformance/test_output.py': TEST_IMPORTS + '\nimport process_evidence as runner\n\n' + node(TESTS, 'OutputEvidenceTests') + '\n',
}
stage('tool-process', 'Capture exact subprocess bytes and terminate timed-out children', process_files,
      problem='Compiler drivers can spawn children that outlive a timeout; text decoding can erase output distinctions.',
      example='compare_bytes(b"value\\n", b"value") reports a mismatch; an embedded NUL remains observable.',
      design='Keep byte capture, process lifetime and evidence-path handling in one small reusable module; save both streams before returning.',
      tradeoffs='Timeout cleanup uses POSIX process groups; its regression is explicitly skipped where killpg is unavailable.',
      reading_order=['tools/process_evidence.py:run', 'tools/process_evidence.py:compare_bytes', 'test/conformance/test_process.py', 'test/conformance/test_output.py'],
      tests=['python3 -m unittest discover -s test/conformance -p test_process.py', 'python3 -m unittest discover -s test/conformance -p test_output.py'],
      docs='Process results preserve raw stdout/stderr, exit status, command arguments and elapsed time. Timeout cleanup kills the complete compiler process group.')

DIAGNOSTICS = '"""Classify negative-compile diagnostics conservatively."""\nimport re\n\n' + node(ORIGINAL, 'negative_status') + '\n'
negative = subprocess.check_output(['git', 'show', 'aeff043:tools/negative.py'], cwd=SOURCE, text=True)
negative = negative.replace('from conformance import ROOT, negative_status, record, run',
                            'from process_evidence import ROOT, record, run\nfrom compile_diagnostics import negative_status')
stage('tool-negative', 'Require intended diagnostics in negative compilation tests', {
    'tools/compile_diagnostics.py': DIAGNOSTICS,
    'tools/negative.py': negative,
    'test/conformance/test_negative_driver.py': TEST_IMPORTS + '\nimport compile_diagnostics as runner\n\n' + node(TESTS, 'NegativeEvidenceTests') + '\n',
}, dependencies=['tool-process'],
      problem='Treating every failed compilation as a rejected format lets missing headers and compiler crashes pass.',
      example='A consteval invalid-format diagnostic passes; "fmt/format.h: No such file or directory" is an infrastructure failure.',
      design='Compile a positive control and syntax-only fixture before testing both ffmt paths and fmt. Classify diagnostics independently of the differential runner.',
      tradeoffs='Compiler diagnostic recognition is a conservative heuristic, not a compiler-independent proof; unfamiliar wording fails visibly.',
      reading_order=['tools/compile_diagnostics.py', 'tools/negative.py', 'test/conformance/test_negative_driver.py'],
      tests=['python3 -m unittest discover -s test/conformance -p test_negative_driver.py', 'make test-negative CXX=g++'],
      docs='Negative compilation requires the intended format diagnostic. Infrastructure failures, unrelated errors and unexpected acceptance fail the check.')

CASE_SUPPORT = '''"""Small constructors for trusted, handwritten conformance fixtures."""
def case(name, family, pattern, *args, **options):
    return dict(id=name, family=family, pattern=pattern, args=list(args), **options)
'''
REGISTRY = '''"""Discover feature fixtures that are present in this source revision."""
import hashlib
import importlib.util
from pathlib import Path
import sys

DIRECTORY = Path(__file__).resolve().parent
if str(DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DIRECTORY))

CASES = []
NEGATIVE_CASES = []
FIXTURE_FILES = [Path(__file__), DIRECTORY / "case_support.py"]
for path in sorted(DIRECTORY.glob("cases_*.py")):
    spec = importlib.util.spec_from_file_location("ffmt_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    CASES.extend(getattr(module, "CASES", []))
    NEGATIVE_CASES.extend(getattr(module, "NEGATIVE_CASES", []))
    FIXTURE_FILES.append(path)

for collection in (CASES, NEGATIVE_CASES):
    identifiers = [item["id"] for item in collection]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("conformance case identifiers must be unique")

def source_hashes():
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in FIXTURE_FILES}
'''

BASE_CASES = '''"""Baseline cases supported by the original public implementation."""
from case_support import case

CASES = [
    case("literal", "literal", "hello {{world}} %\\n"),
    case("int-min", "integer", "{}", "INT64_MIN"),
    case("uint-max", "integer", "{}", "UINT64_MAX"),
    case("ascii", "string", "[{:.3s}] [{:>10s}]", '"abcdef"', '"hello"'),
]
'''

ORACLE_IDENTITY = '''"""Verify reference inputs without changing the caller's fmt checkout."""
import hashlib
from pathlib import Path
import subprocess

FMT_COMMIT = "0fc31633e7d53ac895ae0a688b83b7d44f0b0c1f"

def oracle_identity(checkout, expected_commit=FMT_COMMIT):
    checkout = Path(checkout).resolve()
    def git(*arguments):
        try:
            return subprocess.check_output(["git", "-C", str(checkout), *arguments],
                                           text=True, stderr=subprocess.PIPE).strip()
        except (OSError, subprocess.CalledProcessError) as error:
            raise ValueError("cannot inspect fmt checkout: " + str(checkout)) from error

    commit = git("rev-parse", "HEAD")
    if commit != expected_commit:
        raise ValueError("fmt checkout differs from oracle pin: expected " + expected_commit + ", found " + commit)
    if git("status", "--porcelain"):
        raise ValueError("fmt oracle checkout must be clean; preserve local edits and select a clean checkout")
    return dict(repository="https://github.com/fmtlib/fmt", commit=commit,
                format_header_sha256=hashlib.sha256((checkout / "include/fmt/format.h").read_bytes()).hexdigest(),
                format_source_sha256=hashlib.sha256((checkout / "src/format.cc").read_bytes()).hexdigest())
'''

ORACLE_TESTS = '''"""A dirty oracle cannot be relabeled as the pinned reference."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from oracle import oracle_identity

class OracleIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.checkout = Path(self.temporary.name)
        self.header = self.checkout / "include/fmt/format.h"
        self.source = self.checkout / "src/format.cc"
        for path, content in ((self.header, b"reference header\\n"), (self.source, b"reference implementation\\n")):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        self.git("init", "--quiet", "--template=")
        self.git("add", "include", "src")
        self.git("-c", "user.name=ffmt test", "-c", "user.email=ffmt-test@example.invalid",
                 "-c", "core.hooksPath=/dev/null", "commit", "--no-gpg-sign", "--quiet", "-m", "oracle fixture")
        self.pin = self.git("rev-parse", "HEAD")

    def git(self, *arguments):
        return subprocess.check_output(["git", "-C", str(self.checkout), *arguments], text=True).strip()

    def test_clean_inputs_retain_their_exact_hashes(self):
        result = oracle_identity(self.checkout, self.pin)
        self.assertEqual(result["commit"], self.pin)
        self.assertEqual(result["format_header_sha256"], hashlib.sha256(self.header.read_bytes()).hexdigest())
        self.assertEqual(result["format_source_sha256"], hashlib.sha256(self.source.read_bytes()).hexdigest())

    def test_changed_reference_source_is_rejected_without_reverting_it(self):
        self.source.write_bytes(b"local reference edit\\n")
        status = self.git("status", "--porcelain")
        with self.assertRaisesRegex(ValueError, "must be clean"):
            oracle_identity(self.checkout, self.pin)
        self.assertEqual(self.source.read_bytes(), b"local reference edit\\n")
        self.assertEqual(self.git("status", "--porcelain"), status)
        self.assertEqual(self.git("rev-parse", "HEAD"), self.pin)

    def test_untracked_inputs_are_not_silently_accepted(self):
        local = self.checkout / "local-input.txt"
        local.write_bytes(b"keep this file\\n")
        with self.assertRaisesRegex(ValueError, "must be clean"):
            oracle_identity(self.checkout, self.pin)
        self.assertEqual(local.read_bytes(), b"keep this file\\n")

    def test_wrong_commit_is_rejected_without_checking_out_another_revision(self):
        with self.assertRaisesRegex(ValueError, "differs from oracle pin"):
            oracle_identity(self.checkout, "0" * 40)
        self.assertEqual(self.git("rev-parse", "HEAD"), self.pin)
'''

COMMON_BACKENDS = '''"""Discover independent portable execution adapters.

Adapters are handwritten Python and C++ launcher templates. Only adapters in
this revision are registered; an unknown route is never treated as host code.
"""
import importlib.util
import os
from pathlib import Path
import shlex

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(os.environ.get("FFMT_WORKSPACE", ROOT)).resolve()

def base_flags(route, optimization):
    strict = [] if route == "nvcc" else ["-fno-fast-math"]
    return ["-std=c++20", "-O" + str(optimization)] + strict

ADAPTERS = {}
wrappers = []
for path in sorted(Path(__file__).parent.glob("backend_*.py")):
    spec = importlib.util.spec_from_file_location("ffmt_" + path.stem, path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    if hasattr(adapter, "BASES"):
        wrappers.append(adapter)
    else:
        for route in adapter.ROUTES:
            ADAPTERS[route] = adapter
for adapter in wrappers:
    for route, base in adapter.BASES.items():
        if base in ADAPTERS:
            ADAPTERS[route] = adapter
ROUTES = tuple(ADAPTERS)

def adapter(route):
    try:
        return ADAPTERS[route]
    except KeyError:
        raise ValueError("unknown backend route: " + route) from None

def compiler(route):
    default = adapter(route).compiler(route)
    override = os.environ.get("FFMT_CXX_" + route.upper().replace("-", "_"))
    return shlex.split(override or default)

def flags(route, optimization):
    result = adapter(route).flags(route, optimization)
    return result + shlex.split(os.environ.get("FFMT_FLAGS_" + route.upper().replace("-", "_"), ""))

def link_flags(route):
    module = adapter(route)
    return module.link_flags(route) if hasattr(module, "link_flags") else []

def prelude(route):
    return adapter(route).prelude(route)

def launcher(route):
    return adapter(route).launcher(route)
'''

HOST_BACKEND = '''"""Host execution through the two historical public macro settings."""
import os

ROUTES = ("host-buffer", "host-specifiers")

def compiler(route):
    return os.environ.get("CXX", "g++")

def flags(route, optimization):
    buffer_path = "1" if route == "host-buffer" else "0"
    return ["-std=c++20", "-O" + str(optimization), "-fno-fast-math",
            "-DFFMT_BUFFER_PATH=" + buffer_path]

def prelude(route):
    return "#define HD\\n"

def launcher(route):
    return r"""
int main(int argc, char** argv) {
  if (argc != 2) return 2;
  std::fprintf(stderr, "FFMT_DEVICE host\\n");
  execute_case(std::atoi(argv[1]));
  return 0;
}
"""
'''

REGISTRY_TEST = TEST_IMPORTS + '''
class FixtureRegistryTests(unittest.TestCase):
    def test_every_loaded_fixture_has_a_source_hash(self):
        spec = importlib.util.spec_from_file_location("fixture_registry",
            Path(__file__).parent / "cases.py")
        fixtures = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixtures)
        hashes = fixtures.source_hashes()
        self.assertIn("cases.py", hashes)
        self.assertIn("case_support.py", hashes)
        for path in Path(__file__).parent.glob("cases_*.py"):
            self.assertEqual(hashes[path.name], hashlib.sha256(path.read_bytes()).hexdigest())
        identifiers = [case["id"] for case in fixtures.CASES]
        self.assertEqual(len(identifiers), len(set(identifiers)))
'''

RUNNER_IMPORTS = '''#!/usr/bin/env python3
"""Compare ffmt against an independently compiled, pinned host fmt oracle."""
import argparse
import datetime
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
from process_evidence import ROOT, compare_bytes, path_label, record, run
from oracle import FMT_COMMIT, oracle_identity
from compile_diagnostics import negative_status
import backends
from backends import ROUTES, compiler, flags, link_flags

WORKSPACE = Path(os.environ.get("FFMT_WORKSPACE", ROOT)).resolve()
SOURCE_ROOT = Path(os.environ.get("FFMT_SOURCE_ROOT", ROOT)).resolve()

'''

LOAD_FIXTURES = '''
CONFIG = load_profiles(os.environ.get("FFMT_PROFILES_FILE"))
_spec = importlib.util.spec_from_file_location("ffmt_cases", str(ROOT / "test/conformance/cases.py"))
fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fixtures)

'''

TARGET_SOURCE = '''def target_source(items, indices, route):
    # Reject unknown adapters before generating any host fallback.
    prefix = backends.prelude(route)
    body = "\\n".join("case %d: {%s; break;}" % (i, expression(items[i])) for i in indices)
    source = prefix + "#include <ffmt/base.hpp>\\n" + PRELUDE
    source += extra_headers([items[i] for i in indices])
    source += "\\nHD void execute_case(int index) {\\nswitch (index) {\\n" + body + "\\n}\\n}\\n"
    return source + backends.launcher(route)
'''

# Initial runnable runner: individual case binaries, no batch isolation or
# auxiliary suites. The later isolation stage replaces this method explicitly.
SIMPLE_CONFIGURATION = '''def configuration(self, route, opt, items, expected):
    directory = self.output / (route + "-O" + str(opt))
    directory.mkdir()
    command = compiler(route) + flags(route, opt) + ["-I" + str(self.output / "source/include")]
    config = dict(route=route, optimization=opt, command_prefix=command,
                  cases=[], negative_cases=[])
    self.manifest["configurations"].append(config)
    config["compiler_version"] = record(run(compiler(route) + ["--version"], directory, "compiler-version"))
    for index, item in enumerate(items):
        source = directory / (item["id"] + ".cpp")
        source.write_text(target_source(items, [index], route))
        executable = directory / item["id"]
        build = run(command + [source] + link_flags(route) + ["-o", executable],
                    directory, item["id"] + "-build", self.args.compile_timeout)
        result = dict(id=item["id"], family=item["family"], build=record(build),
                      source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        if build["exit_code"]:
            result["status"] = "compile_timeout" if build.get("timeout") else "compile_failure"
        else:
            execution = run([executable, index], directory, item["id"], self.args.run_timeout)
            result["execution"] = record(execution)
            if execution["exit_code"]:
                result["status"] = "execution_timeout" if execution.get("timeout") else "execution_failure"
            else:
                result.update(compare_bytes(expected[index], execution["stdout"]))
        config["cases"].append(result)
        self.save()
        print("%s -O%s %s: %s" % (route, opt, item["id"], result["status"]), flush=True)
    config["stdout_status"] = "completed"
    config["status"] = "completed"
    self.save()
'''

ISOLATED_CONFIGURATION = '''def configuration(self, route, opt, items, expected):
    directory = self.output / (route + "-O" + str(opt))
    directory.mkdir()
    command = compiler(route) + flags(route, opt) + ["-I" + str(self.output / "source/include")]
    config = dict(route=route, optimization=opt, command_prefix=command,
                  cases=[], negative_cases=[])
    timeout = self.args.run_timeout
    if route in ("sycl", "acpp", "chipstar", "omp-spirv", "kokkos-sycl"):
        timeout = max(timeout, self.args.jit_timeout)
    config["execution_timeout"] = timeout
    self.manifest["configurations"].append(config)
    config["compiler_version"] = record(run(compiler(route) + ["--version"], directory, "compiler-version"))

    if self.stdout_control(command, directory, route, config, timeout):
        applicable = []
        for index, item in enumerate(items):
            missing = [header for header in item.get("requires", [])
                       if not (self.output / "source/include" / header).is_file()]
            if missing:
                config["cases"].append(dict(id=item["id"], family=item["family"],
                    status="unsupported", reason="source snapshot lacks " + ", ".join(missing)))
            else:
                applicable.append(index)
        for first in range(0, len(applicable), self.args.shard_size):
            self.run_shard(command, directory, route, opt, items, expected,
                           applicable[first:first + self.args.shard_size], config, timeout)
        config["stdout_status"] = "completed"
    else:
        reason = "stdout control did not compile" if config["stdout_status"] == "control_compile_failure" else "stdout control did not execute correctly"
        config["cases"] = [dict(id=item["id"], family=item["family"], status="not_run", reason=reason)
                           for item in items]

    # Publish stdout evidence before an auxiliary suite can raise. A completed
    # status is assigned only after every requested auxiliary suite finishes.
    self.save()
    MEMORY_SUITE
    NEGATIVE_SUITE
    config["status"] = config["stdout_status"]
    self.save()

def stdout_control(self, command, directory, route, config, timeout):
    control = [dict(id="control", pattern="control {}", args=["7"])]
    source = directory / "control.cpp"
    source.write_text(target_source(control, [0], route))
    build = run(command + [source] + link_flags(route) + ["-o", directory / "control"],
                directory, "control-build", self.args.compile_timeout)
    config["control_build"] = record(build)
    if build["exit_code"]:
        config["stdout_status"] = "control_compile_failure"
        return False
    execution = run([directory / "control", 0], directory, "control-run", timeout)
    config["control_run"] = record(execution)
    metadata = [line for line in execution["stderr"].decode("utf-8", "replace").splitlines()
                if line.startswith("FFMT_DEVICE ")]
    config["device"] = metadata[0][12:] if metadata else None
    if execution["exit_code"] or execution["stdout"] != b"control 7" or not metadata:
        config["stdout_status"] = "control_execution_failure"
        return False
    return True

def run_shard(self, command, directory, route, opt, items, expected, indices, config, timeout):
    label = "cases-%d-%d" % (indices[0], indices[-1])
    source = directory / (label + ".cpp")
    source.write_text(target_source(items, indices, route))
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    build = run(command + [source] + link_flags(route) + ["-o", directory / label],
                directory, label + "-build", self.args.compile_timeout)
    if build["exit_code"] and len(indices) > 1:
        config.setdefault("shard_failures", []).append(dict(stage="build",
            case_ids=[items[index]["id"] for index in indices], source_sha256=source_hash,
            build=record(build), status="compile_timeout" if build.get("timeout") else "compile_failure"))
        self.save()
        self.split_shard(command, directory, route, opt, items, expected, indices, config, timeout)
        return
    for position, index in enumerate(indices):
        item = items[index]
        result = self.case_result(build, directory / label, index, item,
                                  expected[index], directory, source_hash, timeout)
        if result["status"] != "pass" and "execution" in result and len(indices) > 1:
            # Preserve the failed shared executable before trying smaller ones.
            config.setdefault("shard_failures", []).append(result)
            self.save()
            self.split_shard(command, directory, route, opt, items, expected,
                             indices[position:], config, timeout)
            return
        config["cases"].append(result)
        print("%s -O%s %s: %s" % (route, opt, item["id"], result["status"]), flush=True)
        self.save()

def split_shard(self, command, directory, route, opt, items, expected, indices, config, timeout):
    middle = len(indices) // 2
    groups = [indices] if len(indices) == 1 else [indices[:middle], indices[middle:]]
    for group in groups:
        self.run_shard(command, directory, route, opt, items, expected, group, config, timeout)

def case_result(self, build, executable, index, item, expected, directory, source_hash, timeout):
    result = dict(id=item["id"], family=item["family"], build=record(build), source_sha256=source_hash)
    if build["exit_code"]:
        diagnostic = build["stderr"].decode("utf-8", "replace")
        unsupported = re.search(r"cannot express with printf|format string too long|too_many_placeholders|incompatible|invalid_format_spec|invalid_placeholder", diagnostic)
        result["status"] = "unsupported" if unsupported and negative_status(build) != "infrastructure_failure" else "compile_failure"
        return result
    execution = run([executable, index], directory, item["id"], timeout)
    result["execution"] = record(execution)
    if execution["exit_code"]:
        result["status"] = "execution_timeout" if execution.get("timeout") else "execution_failure"
    else:
        result.update(compare_bytes(expected, execution["stdout"]))
    return result
'''

def runner_source(snapshots=False, isolation=False, memory=False, negatives=False):
    imports = RUNNER_IMPORTS
    if not isolation and not negatives:
        imports = imports.replace('from compile_diagnostics import negative_status\n', '')
    if not snapshots:
        imports = imports.replace('import io\n', '').replace('import tarfile\n', '')
    if not isolation and not negatives:
        imports = imports.replace('import re\n', '')
    result = imports + ('import numeric_memory\n\n' if memory else '')
    result += node(ORIGINAL, 'load_profiles') + '\n' + LOAD_FIXTURES
    result += node(ORIGINAL, 'git') + '\n\n' + node(ORIGINAL, 'source_git') + '\n\n'
    snapshot = node(ORIGINAL, 'snapshot')
    if not snapshots:
        snapshot = '''def snapshot(destination, revision):
    if revision != "WORKTREE":
        raise ValueError("this runner revision supports only --revision WORKTREE")
    shutil.copytree(str(SOURCE_ROOT / "include"), str(destination / "include"))
    return {str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((destination / "include").rglob("*")) if path.is_file()}
'''
    result += snapshot + '\n\n'
    for name in ('expression', 'extra_headers'):
        result += node(ORIGINAL, name) + '\n\n'
    result += 'PRELUDE = ' + repr(ast.literal_eval(next(item.value for item in ast.parse(ORIGINAL).body
              if isinstance(item, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PRELUDE' for t in item.targets)))) + '\n\n'
    result += node(ORIGINAL, 'oracle_source') + '\n\n' + TARGET_SOURCE + '\n\nclass Campaign:\n'
    initialization = method(ORIGINAL, '__init__')
    initialization = initialization.replace('self.args = args',
        'self.args = args\n    self.fmt = Path(args.fmt_dir).resolve()\n    oracle = oracle_identity(self.fmt)')
    initialization = initialization.replace('oracle=dict(repository="https://github.com/fmtlib/fmt", commit=FMT_COMMIT)', 'oracle=oracle')
    initialization = initialization.replace('    if git("-C", str(self.fmt), "rev-parse", "HEAD") != FMT_COMMIT:\n        raise ValueError("fmt checkout differs from oracle pin")\n', '')
    initialization = initialization.replace('self.manifest["corpus_sha256"] = hashlib.sha256((ROOT / "test/conformance/cases.py").read_bytes()).hexdigest()',
        'self.manifest["fixture_files"] = fixtures.source_hashes()\n    self.manifest["corpus_sha256"] = hashlib.sha256(json.dumps(self.manifest["fixture_files"], sort_keys=True).encode()).hexdigest()')
    initialization = initialization.replace('ROOT / "tools/numeric_memory.py", ', '')
    initialization = initialization.replace('for path in (ROOT / "tools/conformance.py", ROOT / "test/conformance/cases.py")',
        'for path in sorted((ROOT / "tools").glob("*.py"))')
    if not memory:
        initialization = initialization.replace('numeric_samples=args.numeric_samples', 'numeric_samples=0')
        initialization = initialization.replace('memory=not args.no_memory', 'memory=False')
    if not negatives:
        initialization = initialization.replace('negative=not args.no_negative', 'negative=False')
    if not snapshots:
        initialization = initialization.replace('SOURCE_ROOT', 'ROOT')
    for code in (initialization, method(ORIGINAL, 'save'), method(ORIGINAL, 'build_oracle')):
        result += textwrap.indent(code, '    ') + '\n\n'
    configuration = ISOLATED_CONFIGURATION if isolation else SIMPLE_CONFIGURATION
    if isolation:
        memory_call = '''if not self.args.no_memory and (self.output / "source/include/ffmt/core.hpp").is_file():
        self.memory_suite(command, directory, route, config)''' if memory else ''
        negative_call = '''if config["stdout_status"] == "completed" and not self.args.no_negative:
        self.negatives(command, directory, route, config)''' if negatives else ''
        configuration = configuration.replace('MEMORY_SUITE', memory_call).replace('NEGATIVE_SUITE', negative_call)
    if not memory:
        configuration = configuration.replace('if not self.args.no_memory and (self.output / "source/include/ffmt/core.hpp").is_file():\n            self.memory_suite(cmd, directory, route, config)', '')
        configuration = configuration.replace('if not self.args.no_memory and (self.output / "source/include/ffmt/core.hpp").is_file():\n        self.memory_suite(cmd, directory, route, config)', '')
    if not negatives:
        configuration = configuration.replace('if not self.args.no_negative:\n        self.negatives(cmd, directory, route, config)', '')
    result += textwrap.indent(configuration, '    ') + '\n\n'
    if memory:
        memory_code = method(ORIGINAL, 'memory_suite').replace('    src = directory / "numeric-memory.cpp"',
            '''    if not hasattr(backends.adapter(route), "numeric_launcher"):
        config["numeric_memory"] = dict(status="unsupported", reason="adapter lacks numeric memory launcher")
        return
    src = directory / "numeric-memory.cpp"''')
        result += textwrap.indent(memory_code, '    ') + '\n\n'
    if negatives:
        result += textwrap.indent(method(ORIGINAL, 'negatives'), '    ') + '\n\n'
    main = node(ORIGINAL, 'main')
    if not memory:
        main = main.replace('parser.add_argument("--no-memory", action="store_true")',
                            'parser.add_argument("--no-memory", action="store_true", help=argparse.SUPPRESS)')
        main = main.replace('parser.add_argument("--numeric-samples", type=int, default=4096)',
                            'parser.add_argument("--numeric-samples", type=int, default=0, help=argparse.SUPPRESS)')
    if not negatives:
        main = main.replace('parser.add_argument("--no-negative", action="store_true")',
                            'parser.add_argument("--no-negative", action="store_true", help=argparse.SUPPRESS)')
    if not snapshots:
        main = main.replace('parser.add_argument("--revision", default="WORKTREE")',
                            'parser.add_argument("--revision", default="WORKTREE", choices=("WORKTREE",))')
        main = main.replace('parser.add_argument("--source-root", default=str(SOURCE_ROOT), help="Library Git checkout to snapshot; runner and fixtures remain in this checkout")', '')
        main = main.replace('SOURCE_ROOT = Path(args.source_root).resolve()', 'SOURCE_ROOT = ROOT')
    result += main + '\n\nif __name__ == "__main__":\n    sys.exit(main())\n'
    literal_lines = set()
    for token in tokenize.generate_tokens(io.StringIO(result).readline):
        if token.type == tokenize.STRING:
            literal_lines.update(range(token.start[0], token.end[0] + 1))
    result = ''.join('\n' if not line.strip() and number not in literal_lines else line
                     for number, line in enumerate(result.splitlines(keepends=True), 1))
    return result

host_files = {'tools/backends.py': COMMON_BACKENDS, 'tools/backend_host.py': HOST_BACKEND,
              'tools/oracle.py': ORACLE_IDENTITY,
              'tools/conformance.py': runner_source(), 'test/conformance/case_support.py': CASE_SUPPORT,
              'test/conformance/cases.py': REGISTRY, 'test/conformance/cases_baseline.py': BASE_CASES,
              'test/conformance/test_fixture_registry.py': REGISTRY_TEST,
              'test/conformance/test_oracle.py': ORACLE_TESTS}
stage('tool-host-oracle', 'Compare host output with an independently compiled fmt oracle', host_files,
      dependencies=['tool-process'],
      problem='The legacy test harness can share assumptions with the implementation; expected bytes need an independent formatting implementation.',
      example='A standalone fmt process formats INT64_MIN; a separate ffmt process must produce the identical bytes.',
      design='Compile fmt only into host reference executables, and compile ffmt targets without fmt headers. Begin with baseline cases supported before engine migration.',
      tradeoffs='Individual executables cost compile time; compiler and fmt source identities are recorded. Accelerator routes and future feature cases are absent.',
      reading_order=['test/conformance/cases_baseline.py', 'tools/conformance.py:build_oracle', 'tools/conformance.py:configuration', 'tools/backend_host.py', 'test/conformance/test_fixture_registry.py'],
      tests=['python3 -m unittest discover -s test/conformance -p test_*.py', 'python3 tools/conformance.py --route host-buffer --opt 2 --no-memory --no-negative --fmt-dir third_party/fmt'],
      docs='The host differential runner compiles the pinned fmt oracle independently. The reference checkout must be clean, and exact format.h/format.cc hashes are retained; verification never changes the caller checkout. Feature fixture modules are introduced with implementations; every loaded fixture file receives a source hash.')

portable_class = node(TESTS, 'PortableConfigurationTests')
stage('tool-snapshots', 'Qualify immutable headers from an independent source checkout', {
    'tools/conformance.py': runner_source(snapshots=True),
    'test/conformance/test_snapshots.py': TEST_IMPORTS + '\nimport conformance as runner\n\n' + portable_class + '\n',
}, dependencies=['tool-host-oracle'],
      problem='Re-running a comparison against a moving worktree can silently change the source under test.',
      example='--source-root ../ffmt --revision COMMIT snapshots that commit even when its working headers have subsequent edits.',
      design='Snapshot include/ through git archive for pinned revisions, or copy current headers for WORKTREE; identify runner checkout separately from library checkout.',
      tradeoffs='Only headers belong to the library snapshot. Exact runner/fixture hashes and compiler commands remain separate evidence, not an assertion of a clean worktree.',
      reading_order=['tools/conformance.py:snapshot', 'tools/conformance.py:Campaign.__init__', 'test/conformance/test_snapshots.py'],
      tests=['python3 -m unittest discover -s test/conformance -p test_snapshots.py', 'python3 tools/conformance.py --revision HEAD --case literal --route host-buffer --opt 2 --no-memory --no-negative'],
      docs='--revision COMMIT snapshots immutable headers. --source-root CHECKOUT separates the tested library checkout from the portable runner; manifests retain both revisions and all captured hashes.')

backend_class = ast.parse(node(TESTS, 'BackendEvidenceTests')).body[0]
def backend_tests(names):
    members = [ast.get_source_segment(TESTS, item) for item in []]
    full = node(TESTS, 'BackendEvidenceTests')
    parsed = ast.parse(full).body[0]
    selected = [textwrap.indent(textwrap.dedent(' ' * member.col_offset + ast.get_source_segment(full, member)), '    ')
                for member in parsed.body if getattr(member, 'name', '') in names]
    return TEST_IMPORTS + '\nimport conformance as runner\n\nclass BackendEvidenceTests(unittest.TestCase):\n' + '\n\n'.join(selected) + '\n'

ISOLATION_NAMES = ['test_unknown_case_cannot_silently_shrink_a_campaign',
                   'test_unknown_route_cannot_become_host_execution',
                   'test_shared_binary_failure_is_isolated_before_case_classification',
                   'test_failed_build_shard_is_saved_before_isolation']
stage('tool-isolation', 'Preserve failed batches before isolating individual cases', {
    'tools/conformance.py': runner_source(snapshots=True, isolation=True),
    'test/conformance/test_runner.py': backend_tests(ISOLATION_NAMES),
}, dependencies=['tool-snapshots', 'tool-negative'],
      problem='A combined switch can fail although individual cases succeed, and retrying without saving it erases the failure.',
      example='When a two-case binary crashes, save its source hash and diagnostic before retrying one-case binaries.',
      design='Require a positive execution control, recursively split failed build batches, and isolate remaining cases after runtime failures. Save each checkpoint atomically.',
      tradeoffs='Retries increase compile time and isolated passes do not erase batch failures. A failed control produces not_run outcomes, not a formatting judgment.',
      reading_order=['tools/conformance.py:configuration', 'test/conformance/test_runner.py'],
      tests=['python3 -m unittest discover -s test/conformance -p test_runner.py', 'python3 tools/conformance.py --route host-buffer --opt 2 --no-memory --no-negative --shard-size 2'],
      docs='Failed batch builds and executions remain in manifest shard_failures before per-case isolation. Positive controls separate missing execution capability from formatting outcomes.')

DEVICE_ARCH = '''"""Compiler target selection shared by CUDA, HIP and OpenMP adapters."""
import os
from pathlib import Path
import subprocess

def cuda_architecture():
    explicit = os.environ.get("FFMT_GPU_ARCH")
    if explicit:
        return explicit
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"], timeout=15)
        return "sm_" + output.decode().splitlines()[0].strip().replace(".", "")
    except (OSError, subprocess.SubprocessError, IndexError):
        return "sm_90"

def hip_architecture():
    explicit = os.environ.get("FFMT_GPU_ARCH")
    if explicit:
        return explicit
    rocm = Path(os.environ.get("ROCM_PATH", "/opt/rocm"))
    try:
        return subprocess.check_output([str(rocm / "llvm/bin/amdgpu-arch")], timeout=15).decode().splitlines()[0]
    except (OSError, subprocess.SubprocessError, IndexError):
        return "gfx942"
'''
stage('tool-adapter-support', 'Share explicit compiler target selection between execution adapters',
      {'tools/device_arch.py': DEVICE_ARCH,
       'test/conformance/test_device_arch.py': '''"""Target overrides never query hardware; discovery failures use explicit defaults."""
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import device_arch

class DeviceArchitectureTests(unittest.TestCase):
    def test_explicit_override_avoids_device_queries(self):
        with mock.patch.dict(os.environ, {"FFMT_GPU_ARCH": "selected-target"}), mock.patch.object(device_arch.subprocess, "check_output") as query:
            self.assertEqual(device_arch.cuda_architecture(), "selected-target")
            self.assertEqual(device_arch.hip_architecture(), "selected-target")
            query.assert_not_called()

    def test_unavailable_queries_use_compile_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(device_arch.subprocess, "check_output", side_effect=OSError("no device tool")):
            self.assertEqual(device_arch.cuda_architecture(), "sm_90")
            self.assertEqual(device_arch.hip_architecture(), "gfx942")

    def test_visible_device_queries_select_the_first_target(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(device_arch.subprocess, "check_output", side_effect=[b"8.0\\n9.0\\n", b"gfx90a\\ngfx942\\n"]):
            self.assertEqual(device_arch.cuda_architecture(), "sm_80")
            self.assertEqual(device_arch.hip_architecture(), "gfx90a")
'''}, dependencies=['tool-isolation'], change_kind='mechanical-move',
      problem='CUDA, HIP and OpenMP launchers need the same target-selection rules without importing each other.',
      example='FFMT_GPU_ARCH=sm_80 selects sm_80 without consulting nvidia-smi.',
      design='Isolate architecture discovery behind two small functions; prefer explicit environment overrides and retain existing fallback targets.',
      tradeoffs='Fallback targets support compilation without a device, but do not prove execution compatibility. Execution controls remain required.',
      reading_order=['tools/device_arch.py', 'test/conformance/test_device_arch.py'], tests=['python3 -m unittest discover -s test/conformance -p test_device_arch.py'],
      docs='Set FFMT_GPU_ARCH explicitly when a compiler target differs from the first visible device. Target discovery is a compiler default, not execution evidence.')

CUDA_BACKEND = '''"""Handwritten CUDA launchers for Clang CUDA and NVIDIA nvcc."""
import os
from device_arch import cuda_architecture

ROUTES = ("cuda", "nvcc")

def compiler(route):
    return "nvcc" if route == "nvcc" else "clang++"

def flags(route, optimization):
    architecture = cuda_architecture()
    common = ["-std=c++20", "-O" + str(optimization)]
    if route == "nvcc":
        return common + ["-x", "cu", "--extended-lambda", "--expt-relaxed-constexpr",
                         "-arch=" + architecture, "-Xcompiler=-fno-fast-math"]
    cuda = os.environ.get("CUDA_PATH", "/usr/local/cuda")
    return common + ["-fno-fast-math", "-x", "cuda", "--cuda-path=" + cuda,
                     "--cuda-gpu-arch=" + architecture, "-L" + cuda + "/lib64", "-lcudart"]

def prelude(route):
    return "#include <cuda_runtime.h>\\n#define HD __host__ __device__\\n"

def launcher(route):
    return r"""
__global__ void kernel(int index) { execute_case(index); }
int main(int argc, char** argv) {
  if (argc != 2) return 2;
  int count = 0;
  if (cudaGetDeviceCount(&count) != cudaSuccess || count == 0) return 77;
  cudaDeviceProp properties{};
  if (cudaGetDeviceProperties(&properties, 0) != cudaSuccess) return 78;
  std::fprintf(stderr, "FFMT_DEVICE cuda name=%s arch=%d.%d\\n",
               properties.name, properties.major, properties.minor);
  kernel<<<1, 1>>>(std::atoi(argv[1]));
  if (cudaGetLastError() != cudaSuccess) return 79;
  if (cudaDeviceSynchronize() != cudaSuccess) return 80;
  return 0;
}
"""
'''

HIP_BACKEND = '''"""Handwritten HIP launchers, including the chipStar compiler route."""
from device_arch import hip_architecture

ROUTES = ("hip", "chipstar")

def compiler(route):
    return "hipcc"

def flags(route, optimization):
    result = ["-std=c++20", "-O" + str(optimization), "-fno-fast-math", "-x", "hip"]
    return result + (["--offload-arch=" + hip_architecture()] if route == "hip" else [])

def prelude(route):
    return "#include <hip/hip_runtime.h>\\n#define HD __host__ __device__\\n"

def launcher(route):
    return r"""
__global__ void kernel(int index) { execute_case(index); }
int main(int argc, char** argv) {
  if (argc != 2) return 2;
  int count = 0;
  if (hipGetDeviceCount(&count) != hipSuccess || count == 0) return 77;
  hipDeviceProp_t properties{};
  if (hipGetDeviceProperties(&properties, 0) != hipSuccess) return 78;
  std::fprintf(stderr, "FFMT_DEVICE hip name=%s arch=%d.%d\\n",
               properties.name, properties.major, properties.minor);
  hipLaunchKernelGGL(kernel, dim3(1), dim3(1), 0, 0, std::atoi(argv[1]));
  if (hipGetLastError() != hipSuccess) return 79;
  if (hipDeviceSynchronize() != hipSuccess) return 80;
  return 0;
}
"""
'''

SYCL_BACKEND = '''"""Handwritten GPU-only SYCL and AdaptiveCpp launchers."""
ROUTES = ("sycl", "acpp")

def compiler(route):
    return "acpp" if route == "acpp" else "icpx"

def flags(route, optimization):
    backend = ["--acpp-targets=generic"] if route == "acpp" else ["-fsycl"]
    return ["-std=c++20", "-O" + str(optimization), "-fno-fast-math"] + backend

def prelude(route):
    return "#include <sycl/sycl.hpp>\\n#define HD\\n"

def launcher(route):
    return r"""
#include <exception>
int main(int argc, char** argv) {
  if (argc != 2) return 2;
  try {
    sycl::queue queue{sycl::gpu_selector_v};
    auto device = queue.get_device();
    auto name = device.get_info<sycl::info::device::name>();
    std::fprintf(stderr, "FFMT_DEVICE sycl name=%s fp64=%d\\n",
                 name.c_str(), device.has(sycl::aspect::fp64));
    int index = std::atoi(argv[1]);
    queue.single_task([=] { execute_case(index); }).wait_and_throw();
    return 0;
  } catch (const std::exception& error) {
    std::fprintf(stderr, "%s\\n", error.what());
    return 80;
  }
}
"""
'''

OPENMP_BACKEND = '''"""Handwritten mandatory-offload OpenMP launchers."""
import os
from device_arch import cuda_architecture, hip_architecture

ROUTES = ("omp-cuda", "omp-hip", "omp-spirv")

def compiler(route):
    return "icpx" if route == "omp-spirv" else "clang++"

def flags(route, optimization):
    common = ["-std=c++20", "-O" + str(optimization), "-fno-fast-math"]
    if route == "omp-spirv":
        return common + ["-fiopenmp", "-fopenmp-targets=spir64"]
    if route == "omp-cuda":
        return common + ["-fopenmp", "--offload-arch=" + cuda_architecture(),
                         "--cuda-path=" + os.environ.get("CUDA_PATH", "/usr/local/cuda")]
    return common + ["-fopenmp", "--offload-arch=" + hip_architecture(),
                     "--rocm-path=" + os.environ.get("ROCM_PATH", "/opt/rocm")]

def prelude(route):
    return "#include <omp.h>\\n#define HD\\n"

def launcher(route):
    return r"""
int main(int argc, char** argv) {
  if (argc != 2) return 2;
  int initial_device = 1;
  #pragma omp target map(from: initial_device)
  { initial_device = omp_is_initial_device(); }
  if (initial_device) return 77;
  std::fprintf(stderr, "FFMT_DEVICE openmp device=%d initial_device=false\\n",
               omp_get_default_device());
  int index = std::atoi(argv[1]);
  #pragma omp target firstprivate(index)
  { execute_case(index); }
  return 0;
}
"""
'''

KOKKOS_BACKEND = '''"""Handwritten Kokkos wrappers for adapters present in this revision."""
import os
from pathlib import Path

BASES = {"kokkos-serial": "host-buffer", "kokkos-cuda": "cuda",
         "kokkos-hip": "hip", "kokkos-sycl": "sycl"}

def compiler(route):
    import backends
    return " ".join(backends.compiler(BASES[route]))

def prefix(route):
    from backends import WORKSPACE
    key = "FFMT_KOKKOS_" + route.split("-", 1)[1].upper() + "_PREFIX"
    fallback = WORKSPACE / "software" / os.environ.get("FFMT_PROFILE", "local") / "install" / route
    return Path(os.environ.get(key, fallback))

def flags(route, optimization):
    import backends
    return backends.flags(BASES[route], optimization) + ["-I" + str(prefix(route) / "include")]

def link_flags(route):
    library = prefix(route) / "lib"
    if not library.is_dir():
        library = prefix(route) / "lib64"
    return ["-L" + str(library), "-lkokkoscontainers", "-lkokkoscore", "-ldl", "-pthread"] + (["-lcuda"] if route == "kokkos-cuda" else [])

def prelude(route):
    import backends
    return backends.prelude(BASES[route]) + "#include <Kokkos_Core.hpp>\\n"

def device_guard(route):
    if route == "kokkos-sycl":
        return r"""
  auto device = Kokkos::DefaultExecutionSpace{}.sycl_queue().get_device();
  if (!device.is_gpu()) { Kokkos::finalize(); return 77; }
  std::fprintf(stderr, "FFMT_DEVICE kokkos space=SYCL name=%s\\n",
               device.get_info<sycl::info::device::name>().c_str());
"""
    if route in ("kokkos-cuda", "kokkos-hip"):
        api = "cuda" if route == "kokkos-cuda" else "hip"
        properties = "cudaDeviceProp" if api == "cuda" else "hipDeviceProp_t"
        space = "Cuda" if api == "cuda" else "HIP"
        return r"""
  int device_id = 0;
  PROPERTIES properties{};
  if (APIGetDevice(&device_id) != APISuccess ||
      APIGetDeviceProperties(&properties, device_id) != APISuccess) {
    Kokkos::finalize(); return 78;
  }
  std::fprintf(stderr, "FFMT_DEVICE kokkos space=SPACE name=%s arch=%d.%d\\n",
               properties.name, properties.major, properties.minor);
""".replace("PROPERTIES", properties).replace("API", api).replace("SPACE", space)
    return '  std::fprintf(stderr, "FFMT_DEVICE kokkos space=Serial\\\\n");\\n'

def launcher(route):
    space = {"kokkos-serial": "Serial", "kokkos-cuda": "Cuda",
             "kokkos-hip": "HIP", "kokkos-sycl": "SYCL"}[route]
    return r"""
#include <cstring>
int main(int argc, char** argv) {
  if (argc != 2) return 2;
  Kokkos::initialize(argc, argv);
  if (std::strcmp(Kokkos::DefaultExecutionSpace::name(), "SPACE") != 0) {
    Kokkos::finalize(); return 77;
  }
GUARD
  int index = std::atoi(argv[1]);
  Kokkos::parallel_for("ffmt-case", Kokkos::RangePolicy<>(0, 1),
                      KOKKOS_LAMBDA(int) { execute_case(index); });
  Kokkos::fence();
  Kokkos::finalize();
  return 0;
}
""".replace("SPACE", space).replace("GUARD", device_guard(route))
'''

for identifier, name, content, deps, example, limitation in [
    ('tool-cuda', 'cuda', CUDA_BACKEND, ['tool-adapter-support'], 'Run a literal case in a one-thread CUDA kernel through nvcc or Clang.', 'Execution requires a CUDA device and runtime; Python checks only source generation here.'),
    ('tool-hip', 'hip', HIP_BACKEND, ['tool-adapter-support'], 'Run the same case through a HIP kernel without a fmt device build.', 'Execution requires the selected HIP or chipStar runtime and a device.'),
    ('tool-sycl', 'sycl', SYCL_BACKEND, ['tool-isolation'], 'Use a GPU selector, launch one SYCL task, and retain its device name.', 'Execution requires SYCL or AdaptiveCpp GPU support; a CPU fallback cannot pass.'),
    ('tool-openmp', 'openmp', OPENMP_BACKEND, ['tool-adapter-support'], 'Reject an OpenMP target region that executes on the initial host device.', 'Execution requires a working offload toolchain and accelerator; host fallback is failure.'),
    ('tool-kokkos', 'kokkos', KOKKOS_BACKEND, ['tool-isolation'], 'Only advertise kokkos-cuda when the CUDA base adapter is present.', 'Kokkos must be installed externally with the selected execution space; no site profiles are included.'),
]:
    test = '''"""Source-generation checks; these do not establish accelerator execution."""
import os
from pathlib import Path
import sys
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import backends
import conformance

class AdapterTests(unittest.TestCase):
    def test_handwritten_launcher_uses_its_backend(self):
        routes = [route for route in backends.ROUTES if backends.adapter(route).__name__.endswith("backend_NAME")]
        self.assertTrue(routes)
        for route in routes:
            with self.subTest(route=route):
                source = conformance.target_source([dict(pattern="{}", args=["7"])], [0], route)
                self.assertIn("execute_case", source)
                self.assertIn("FFMT_DEVICE", source)
                self.assertNotIn("#include <fmt/", source)
'''.replace('NAME', name)
    assertions = {
        'cuda': ['cudaGetDeviceCount', 'cudaGetLastError', 'cudaDeviceSynchronize', 'kernel<<<1, 1>>>'],
        'hip': ['hipGetDeviceCount', 'hipGetLastError', 'hipDeviceSynchronize', 'hipLaunchKernelGGL'],
        'sycl': ['sycl::gpu_selector_v', 'single_task', 'wait_and_throw'],
        'openmp': ['omp_is_initial_device', 'if (initial_device) return 77', '#pragma omp target'],
        'kokkos': ['DefaultExecutionSpace::name()', 'Kokkos::parallel_for', 'Kokkos::fence()', 'Kokkos::finalize()'],
    }[name]
    for assertion in assertions:
        test += '                self.assertIn(' + repr(assertion) + ', source)\n'
    flag_assertions = {
        'cuda': [('cuda', 'clang++', '--cuda-gpu-arch=review_target'), ('nvcc', 'nvcc', '-arch=review_target')],
        'hip': [('hip', 'hipcc', '--offload-arch=review_target'), ('chipstar', 'hipcc', 'hip')],
        'sycl': [('sycl', 'icpx', '-fsycl'), ('acpp', 'acpp', '--acpp-targets=generic')],
        'openmp': [('omp-cuda', 'clang++', '--offload-arch=review_target'), ('omp-hip', 'clang++', '--offload-arch=review_target'), ('omp-spirv', 'icpx', '-fopenmp-targets=spir64')],
        'kokkos': [('kokkos-serial', 'g++', '-I/review/kokkos/include')],
    }[name]
    test += '\n    def test_compiler_and_flags_match_the_selected_route(self):\n'
    test += '        with mock.patch.dict(os.environ, {"FFMT_GPU_ARCH": "review_target", "FFMT_KOKKOS_SERIAL_PREFIX": "/review/kokkos"}, clear=True):\n'
    for route, compiler_name, expected_flag in flag_assertions:
        test += '            self.assertEqual(backends.compiler(' + repr(route) + '), [' + repr(compiler_name) + '])\n'
        test += '            self.assertIn(' + repr(expected_flag) + ', backends.flags(' + repr(route) + ', 2))\n'
    stage(identifier, 'Add independent ' + name.upper() + ' differential execution adapter',
          {'tools/backend_' + name + '.py': content,
           'test/conformance/test_adapter_' + name + '.py': test}, dependencies=deps,
          problem='Portable output cases need a backend-specific execution launcher without coupling unrelated accelerator runtimes.',
          example=example, design='Register this adapter independently; keep handwritten compiler flags and C++ launch code next to each other.',
          tradeoffs=limitation, reading_order=['tools/backend_' + name + '.py', 'test/conformance/test_adapter_' + name + '.py'],
          tests=['python3 -m unittest discover -s test/conformance -p test_adapter_' + name + '.py'],
          docs=example + ' ' + limitation)

stage('tool-oracle-negatives', 'Compare invalid literal rejection against the independent oracle', {
    'tools/conformance.py': runner_source(snapshots=True, isolation=True, negatives=True),
}, dependencies=['tool-isolation'],
      problem='A source snapshot can reject valid formatting output correctly while silently accepting an invalid literal.',
      example='The unclosed "{" fixture must produce an intended format diagnostic in both the target compiler and the host fmt oracle.',
      design='Reuse the diagnostic classifier for revisioned negative fixture modules and preserve both compiler diagnostics separately.',
      tradeoffs='This adds compile-time rejection parity, not runtime parser exception parity. The baseline fixture registry has no new negative cases until engine migration.',
      reading_order=['tools/conformance.py:negatives', 'tools/compile_diagnostics.py'],
      tests=['python3 -m unittest discover -s test/conformance -p test_negative_driver.py'],
      docs='Revisioned negative fixtures accompany parser behavior and run through both the independent host fmt oracle and the selected target compiler.')

# Core differential fixtures are introduced only when base.hpp migrates to the
# new engine. Earlier stages have focused C++ oracle tests through checked.hpp.
case_original = subprocess.check_output(['git', 'show', 'aeff043:test/conformance/cases.py'], cwd=SOURCE, text=True)
case_tree = ast.parse(case_original)
base_calls = next(item.value.elts for item in case_tree.body
                  if isinstance(item, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'CASES' for t in item.targets))
engine_calls = [item for item in base_calls if ast.literal_eval(item.args[0]) not in ('literal', 'int-min', 'uint-max', 'ascii')]
for item in ast.walk(case_tree):
    if isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id == 'case' and item.args:
        if ast.literal_eval(item.args[0]) in ('runtime-format', 'wide-stdout'):
            engine_calls.append(item)
engine_cases = '"""Public engine cases activated with migration from the legacy engine."""\nfrom case_support import case\n\nCASES = [\n'
for item in engine_calls:
    engine_cases += '    ' + ast.get_source_segment(case_original, item) + ',\n'
engine_cases += ']\n\n'
negative_assignment = next(item for item in case_tree.body if isinstance(item, ast.Assign)
                           and any(isinstance(t, ast.Name) and t.id == 'NEGATIVE_CASES' for t in item.targets))
engine_cases += ast.get_source_segment(case_original, negative_assignment) + '\n'
stage('tool-engine-cases', 'Activate public engine differential cases at migration', {
    'test/conformance/cases_engine.py': engine_cases,
}, dependencies=['migration', 'tool-oracle-negatives'],
      problem='The new public engine needs transport, capacity, Unicode and floating-point cases beyond the old implementation baseline.',
      example='A 300-character padded field must compare against all 300 oracle bytes; a missing newline or embedded NUL is significant.',
      design='Introduce these public-entry-point fixtures with engine migration. Earlier internal engine steps already carry focused C++ comparisons against fmt.',
      tradeoffs='This corpus is representative, not exhaustive; extension-specific integer and floating-point coverage remains in focused C++ tests.',
      reading_order=['test/conformance/cases_engine.py', 'test/conformance/cases_baseline.py'],
      tests=['python3 tools/conformance.py --route host-buffer --route host-specifiers --opt 2 --no-memory'],
      docs='Public engine cases are introduced at migration, after focused C++ oracle tests qualify individual internal engine steps.')

numeric_ast = ast.parse(NUMERIC)
numeric_cpp = next(item.value for item in ast.walk(numeric_ast)
                   if isinstance(item, ast.Constant) and isinstance(item.value, str) and 'struct Input' in item.value)
numeric_cpp = subprocess.run(['/soft/compilers/llvm/release-22.1.8/bin/clang-format'], input=numeric_cpp,
                             stdout=subprocess.PIPE, text=True, check=True).stdout
NUMERIC_MODULE = '''"""Binary numeric records and handwritten C++ conformance source templates."""
from pathlib import Path
import struct
import backends

MAGIC = 0x46464D54
SEED = 0x4D595DF4D0F33173
CAPACITY = 768
CORPUS_TEMPLATE = Path(__file__).resolve().parents[1] / "test/conformance/numeric_memory.cpp.in"

'''
for name in ('parse_records', 'compare_records'):
    NUMERIC_MODULE += node(NUMERIC, name) + '\n\n'
NUMERIC_MODULE += '''def source(route, oracle=False, samples=4096):
    if samples < 0:
        raise ValueError("numeric sample count must be nonnegative")
    module = backends.adapter("host-buffer" if oracle else route)
    if not hasattr(module, "numeric_launcher"):
        raise ValueError("numeric memory execution is unavailable for route: " + route)
    prefix = "#define HD\\n#include <fmt/format.h>\\n#define ORACLE 1\\n" if oracle else backends.prelude(route) + "#include <ffmt/base.hpp>\\n"
    body = CORPUS_TEMPLATE.read_text().replace("SAMPLE_COUNT", str(samples))
    return prefix + body + module.numeric_launcher(route)
'''

HOST_NUMERIC = '''

def numeric_launcher(route):
    return r"""
int main() {
  auto input = inputs();
  std::vector<Output> output(input.size());
  for (unsigned i = 0; i < input.size(); ++i)
    format_record(input[i], output[i]);
  serialize(input, output);
  return 0;
}
"""
'''

memory_runner = runner_source(snapshots=True, isolation=True, memory=True, negatives=True)
memory_runner = memory_runner.replace('for path in sorted((ROOT / "tools").glob("*.py"))',
    'for path in sorted((ROOT / "tools").glob("*.py")) + sorted((ROOT / "test/conformance").glob("*.cpp.in"))')
# Template hashes supplement runner and fixture identity independently of the
# source snapshot. Captured per-configuration C++ source hashes remain intact.
stage('tool-numeric-memory', 'Compare bounded numeric memory records with host fmt output', {
    'tools/numeric_memory.py': NUMERIC_MODULE,
    'tools/backend_host.py': HOST_BACKEND + HOST_NUMERIC,
    'tools/conformance.py': memory_runner,
    'test/conformance/numeric_memory.cpp.in': numeric_cpp,
    'test/conformance/test_numeric_memory.py': TEST_IMPORTS + '\nimport numeric_memory\n\n' + node(TESTS, 'MemoryEvidenceTests') + '\n',
    'test/conformance/test_auxiliary_evidence.py': backend_tests(['test_stdout_control_failure_does_not_hide_memory_results',
                                  'test_auxiliary_exception_leaves_configuration_unfinished']),
}, dependencies=['tool-oracle-negatives', 'migration'],
      problem='Printf transport can hide whether floating-point conversion and bounded output accounting produced the correct memory bytes.',
      example='A record for a subnormal double checks the input encoding, output bytes, written/required counts and error status against independent fmt.',
      design='Use explicit binary framing and a fixed seed. Keep numeric operations in a conventionally formatted handwritten C++ template that is hashed with runner inputs.',
      tradeoffs='The 4,096 float and double encodings plus boundaries are representative samples; matching this corpus is not exhaustive floating-point proof. This stage executes host memory only.',
      reading_order=['test/conformance/numeric_memory.cpp.in', 'tools/numeric_memory.py:parse_records', 'tools/conformance.py:memory_suite', 'test/conformance/test_numeric_memory.py'],
      tests=['python3 -m unittest discover -s test/conformance -p test_numeric_memory.py', 'python3 tools/conformance.py --route host-buffer --opt 2 --numeric-samples 32'],
      docs='The numeric memory suite checks byte payloads, framing, input bits, written and required sizes, and error status. The template is handwritten source, not excluded generated material. Raw record framing is unchanged from the preserved suite.')

CUDA_NUMERIC = '''

def numeric_launcher(route):
    return r"""
__global__ void memory_kernel(const Input* input, Output* output, unsigned count) {
  unsigned i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i < count) format_record(input[i], output[i]);
}
int main() {
  auto input = inputs();
  std::vector<Output> output(input.size());
  Input* device_input = nullptr;
  Output* device_output = nullptr;
  if (cudaMalloc((void**)&device_input, input.size() * sizeof(Input)) != cudaSuccess) return 81;
  if (cudaMalloc((void**)&device_output, output.size() * sizeof(Output)) != cudaSuccess) return 82;
  if (cudaMemcpy(device_input, input.data(), input.size() * sizeof(Input), cudaMemcpyHostToDevice) != cudaSuccess) return 83;
  if (cudaMemset(device_output, 0, output.size() * sizeof(Output)) != cudaSuccess) return 84;
  memory_kernel<<<(input.size() + 63) / 64, 64>>>(device_input, device_output, unsigned(input.size()));
  if (cudaGetLastError() != cudaSuccess || cudaDeviceSynchronize() != cudaSuccess) return 85;
  if (cudaMemcpy(output.data(), device_output, output.size() * sizeof(Output), cudaMemcpyDeviceToHost) != cudaSuccess) return 86;
  cudaFree(device_input);
  cudaFree(device_output);
  serialize(input, output);
  return 0;
}
"""
'''
HIP_NUMERIC = CUDA_NUMERIC.replace('cuda', 'hip').replace('memory_kernel<<<(input.size() + 63) / 64, 64>>>(device_input, device_output, unsigned(input.size()));',
    'hipLaunchKernelGGL(memory_kernel, dim3((input.size() + 63) / 64), dim3(64), 0, 0, device_input, device_output, unsigned(input.size()));')
SYCL_NUMERIC = '''

def numeric_launcher(route):
    return r"""
int main() {
  try {
    auto input = inputs();
    std::vector<Output> output(input.size());
    sycl::queue queue{sycl::gpu_selector_v};
    Input* device_input = sycl::malloc_device<Input>(input.size(), queue);
    Output* device_output = sycl::malloc_device<Output>(output.size(), queue);
    if (!device_input || !device_output) return 81;
    queue.memcpy(device_input, input.data(), input.size() * sizeof(Input)).wait_and_throw();
    queue.memset(device_output, 0, output.size() * sizeof(Output)).wait_and_throw();
    unsigned count = unsigned(input.size());
    queue.parallel_for(sycl::range<1>(count), [=](sycl::id<1> id) {
      format_record(device_input[id[0]], device_output[id[0]]);
    }).wait_and_throw();
    queue.memcpy(output.data(), device_output, output.size() * sizeof(Output)).wait_and_throw();
    sycl::free(device_input, queue);
    sycl::free(device_output, queue);
    serialize(input, output);
    return 0;
  } catch (const std::exception& error) {
    std::fprintf(stderr, "%s\\n", error.what());
    return 80;
  }
}
"""
'''
OPENMP_NUMERIC = '''

def numeric_launcher(route):
    return r"""
int main() {
  auto input = inputs();
  std::vector<Output> output(input.size());
  unsigned count = unsigned(input.size());
  Input* device_input = input.data();
  Output* device_output = output.data();
  int initial_device = 1;
  #pragma omp target map(from: initial_device)
  { initial_device = omp_is_initial_device(); }
  if (initial_device) return 77;
  #pragma omp target teams distribute parallel for map(to: device_input[0:count]) map(from: device_output[0:count])
  for (unsigned i = 0; i < count; ++i)
    format_record(device_input[i], device_output[i]);
  serialize(input, output);
  return 0;
}
"""
'''
KOKKOS_NUMERIC = '''

def numeric_launcher(route):
    space = {"kokkos-serial": "Serial", "kokkos-cuda": "Cuda",
             "kokkos-hip": "HIP", "kokkos-sycl": "SYCL"}[route]
    return r"""
#include <cstring>
int main(int argc, char** argv) {
  Kokkos::initialize(argc, argv);
  if (std::strcmp(Kokkos::DefaultExecutionSpace::name(), "SPACE") != 0) {
    Kokkos::finalize(); return 77;
  }
GUARD
  {
    auto input = inputs();
    std::vector<Output> output(input.size());
    unsigned count = unsigned(input.size());
    Kokkos::View<Input*> device_input("input", count);
    Kokkos::View<Output*> device_output("output", count);
    auto host_input = Kokkos::create_mirror_view(device_input);
    for (unsigned i = 0; i < count; ++i) host_input(i) = input[i];
    Kokkos::deep_copy(device_input, host_input);
    Kokkos::parallel_for("ffmt-memory", Kokkos::RangePolicy<>(0, count),
      KOKKOS_LAMBDA(int i) { format_record(device_input(i), device_output(i)); });
    auto host_output = Kokkos::create_mirror_view_and_copy(Kokkos::HostSpace{}, device_output);
    for (unsigned i = 0; i < count; ++i) output[i] = host_output(i);
    serialize(input, output);
  }
  Kokkos::finalize();
  return 0;
}
""".replace("SPACE", space).replace("GUARD", device_guard(route))
'''

for name, original, addition in [('cuda', CUDA_BACKEND, CUDA_NUMERIC), ('hip', HIP_BACKEND, HIP_NUMERIC),
                                  ('sycl', SYCL_BACKEND, SYCL_NUMERIC), ('openmp', OPENMP_BACKEND, OPENMP_NUMERIC),
                                  ('kokkos', KOKKOS_BACKEND, KOKKOS_NUMERIC)]:
    memory_assertions = {
        'cuda': ['cudaMalloc', 'cudaMemcpyHostToDevice', 'cudaMemcpyDeviceToHost', 'cudaDeviceSynchronize', 'memory_kernel<<<'],
        'hip': ['hipMalloc', 'hipMemcpyHostToDevice', 'hipMemcpyDeviceToHost', 'hipDeviceSynchronize', 'hipLaunchKernelGGL(memory_kernel'],
        'sycl': ['sycl::gpu_selector_v', 'sycl::malloc_device', 'queue.parallel_for', 'queue.memcpy(output.data()', 'wait_and_throw'],
        'openmp': ['omp_is_initial_device', 'if (initial_device) return 77', 'map(to: device_input[0:count])', 'map(from: device_output[0:count])'],
        'kokkos': ['DefaultExecutionSpace::name()', 'Kokkos::deep_copy', 'Kokkos::parallel_for', 'create_mirror_view_and_copy', 'Kokkos::finalize()'],
    }[name]
    memory_test = '''"""Device-memory source generation is checked without claiming hardware execution."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import backends
import numeric_memory

class MemoryAdapterTests(unittest.TestCase):
    def test_numeric_records_use_the_selected_memory_backend(self):
        routes = [route for route in backends.ROUTES if backends.adapter(route).__name__.endswith("backend_NAME")]
        self.assertTrue(routes)
        for route in routes:
            with self.subTest(route=route):
                source = numeric_memory.source(route, samples=0)
                self.assertNotIn("#include <fmt/", source)
                self.assertIn("format_record", source)
                self.assertIn("serialize(input, output)", source)
'''.replace('NAME', name)
    for assertion in memory_assertions:
        memory_test += '                self.assertIn(' + repr(assertion) + ', source)\n'
    stage('tool-memory-' + name, 'Execute numeric memory records through the ' + name.upper() + ' adapter', {
        'tools/backend_' + name + '.py': original + addition,
        'test/conformance/test_memory_' + name + '.py': memory_test,
    }, dependencies=['tool-numeric-memory', 'tool-' + name],
          problem='Stdout transport and floating-point memory conversion can fail independently on an accelerator.',
          example='Copy numeric input encodings to device memory, format there, then compare copied binary output records with host fmt.',
          design='Add a memory launcher to the existing independent adapter without changing other backend modules.',
          tradeoffs='Runtime execution remains hardware-dependent; source-generation and host record tests validate structure but do not establish accelerator execution.',
          reading_order=['tools/backend_' + name + '.py:numeric_launcher', 'test/conformance/numeric_memory.cpp.in'],
          tests=['python3 -m unittest discover -s test/conformance -p test_memory_' + name + '.py'],
          docs='The memory launcher formats on the selected backend and copies records to the host for byte-exact oracle comparison. Stdout control failure does not hide memory outcomes.')

coverage = subprocess.check_output(['git', 'show', 'aeff043:.github/scripts/coverage_union.py'], cwd=SOURCE, text=True)
coverage_test = '''"""Coverage collection keeps source identity and runtime metric categories separate."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location("coverage_union",
    Path(__file__).resolve().parents[2] / ".github/scripts/coverage_union.py")
coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage)

class CoverageMetricsTests(unittest.TestCase):
    def test_file_identity_and_real_executable_lines_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            first = directory / "first.hpp"
            second = directory / "second.hpp"
            first.touch()
            second.touch()
            foreign = str(directory.parent / "foreign.hpp")
            payload = {"data": [{"functions": [
                {"filenames": [str(first), foreign], "regions": [
                    [1, 1, 3, 4, 0, 0, 0, 0], [1, 1, 3, 4, 9, 0, 0, 0],
                    [1, 1, 3, 4, 9, 1, 0, 0]]},
                {"filenames": [str(second)], "regions": [[1, 1, 3, 4, 0, 0, 0, 0]]}],
                "files": [{"filename": str(first), "branches": [[2, 1, 2, 8, 1, 0, 0, 0, 4]]},
                          {"filename": foreign, "branches": [[2, 1, 2, 8, 1, 1, 0, 0, 4]]}]}]}
            lcov = f"SF:{first}\\nDA:1,1\\nDA:3,0\\nSF:{second}\\nDA:1,0\\nSF:{foreign}\\nDA:1,1\\n"
            with mock.patch.object(coverage.subprocess, "run"), mock.patch.object(coverage.subprocess, "check_output", side_effect=[json.dumps(payload).encode(), lcov.encode()]):
                result = coverage.regions("llvm-cov", "llvm-profdata", str(directory), "binary", temporary)
            self.assertEqual(coverage.metrics(result["regions"]), dict(covered=1, count=2, percent=50.0))
            self.assertEqual(coverage.metrics(result["lines"]), dict(covered=1, count=3, percent=100 / 3))
            self.assertEqual(coverage.metrics(result["branches"]), dict(covered=1, count=2, percent=50.0))

    def test_empty_coverage_is_explicit_instead_of_perfect(self):
        self.assertEqual(coverage.metrics({}), dict(covered=0, count=0, percent=None))
'''
stage('coverage-metrics', 'Report source-file region, executable-line and branch coverage', {
    '.github/scripts/coverage_union.py': coverage,
    'test/conformance/test_coverage_metrics.py': coverage_test,
}, problem='One-header region percentages omit new headers and cannot describe executable-line or branch-edge coverage.',
      example='Two headers with a region at the same coordinates remain two regions; an unexecuted branch side stays uncovered.',
      design='Include source filenames in union keys, preserve any-instantiation coverage, and read executable lines from LLVM LCOV export rather than estimating spans.',
      tradeoffs='Only instantiated runtime code is measured. Device-only code, compile-time evaluation and uninstantiated templates remain outside the denominator. This PR preserves the blocking policy.',
      reading_order=['.github/scripts/coverage_union.py:regions', '.github/scripts/coverage_union.py:metrics', 'test/conformance/test_coverage_metrics.py'],
      tests=['python3 -m unittest discover -s test/conformance -p test_coverage_metrics.py', 'make coverage CXX=clang++'],
      docs='Coverage metrics can accept a file or header directory. This measurement extension does not relax the existing regression gate; policy is reviewed separately.')

benchmark = subprocess.check_output(['git', 'show', 'aeff043:tools/benchmark.py'], cwd=SOURCE, text=True)
benchmark = benchmark.replace('import conformance as qualification', 'import conformance as qualification\nfrom oracle import oracle_identity')
benchmark = benchmark.replace('    oracle_commit = subprocess.check_output(["git", "-C", str(a.fmt_dir), "rev-parse", "HEAD"]).decode().strip()\n    if oracle_commit != qualification.FMT_COMMIT:\n        p.error("fmt oracle commit differs from the portable suite pin")',
    '''    try:
        oracle = oracle_identity(a.fmt_dir)
    except ValueError as error:
        p.error(str(error))
    oracle_commit = oracle["commit"]''')
benchmark = benchmark.replace('"fmt_commit": oracle_commit, "timer_policy":', '"fmt_commit": oracle_commit, "oracle": oracle, "timer_policy":')
benchmark = benchmark.replace('for path in (ROOT / "tools/benchmark.py", ROOT / "tools/conformance.py", ROOT / "tools/numeric_memory.py")',
                              'for path in sorted((ROOT / "tools").glob("*.py"))')
benchmark = benchmark.replace('choices=["host-buffer", "host-specifiers", "cuda", "nvcc", "hip",\n                   "omp-cuda", "omp-hip", "omp-spirv", "sycl", "acpp", "chipstar"]',
                              'choices=[route for route in qualification.ROUTES if not route.startswith("kokkos-")]')

def without_resources(source):
    result = source
    for name in ('image_tables', 'resources'):
        result = result.replace(node(result, name) + '\n\n', '')
    build = node(result, 'build')
    resource_start = build.index('    resource = []')
    resource_end = build.index('    destination.mkdir', resource_start)
    build = build[:resource_start] + build[resource_end:]
    build = build.replace('*defines, *resource,', '*defines,')
    sizes = build.index('    sizes = []')
    build = build[:sizes] + '''    return {"status": "built", "executable": str(executable), "events": events,
            "clean_compile_seconds": sum(event["seconds"] for event in events),
            "executable_bytes": executable.stat().st_size,
            "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
            "object_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in objects}}
'''
    result = result.replace(node(result, 'build'), build)
    result = result.replace('    p.add_argument("--resources-only", action="store_true", help="Compile dedicated integer/float one/two-call resource probes without timing")\n', '')
    result = result.replace('    p.add_argument("--resource-presentation", choices=["existing", "shortest", "both"], default="existing", help="Resource-only float presentation; existing rows use explicit8e precision")\n', '')
    result = result.replace('a.resources_only or set(a.mode or ["memory", "print"]) != {"memory"}', 'set(a.mode or ["memory", "print"]) != {"memory"}')
    start = result.index('    if a.resources_only and a.resource_presentation')
    stop = result.index('    # Keep JIT preparation', start)
    result = result[:start] + result[stop:]
    start = result.index('        if a.resources_only:')
    stop = result.index('        oracle = build(', start)
    result = result[:start] + result[stop:]
    result = result.replace(', "resource_probes": []', '')
    result = result.replace('resource_presentation=a.resource_presentation, ', '')
    result = result.replace('; use --resource-presentation for resource probes', '')
    result = result.replace('Restrict timing/resource probes to selected', 'Restrict timing workloads to selected')
    result = result.replace('import re\n', '').replace('import shutil\n', '').replace('import importlib.util\n', '')
    return result

benchmark_primitive_files = {}
for name in ('benchmark.cpp', 'benchmark_calls.hpp', 'benchmark_extra.cpp'):
    data = subprocess.check_output(['git', 'show', 'aeff043:test/conformance/' + name], cwd=SOURCE, text=True)
    data = subprocess.run(['/soft/compilers/llvm/release-22.1.8/bin/clang-format'], input=data,
                          stdout=subprocess.PIPE, text=True, check=True).stdout
    benchmark_primitive_files['test/conformance/' + name] = data
stage('benchmark-primitives', 'Add explicit memory and printing benchmark primitives', benchmark_primitive_files,
      dependencies=['migration'],
      problem='Formatting into memory and printing have different costs; a reusable benchmark must preserve that distinction.',
      example='Integer memory mode formats value={:+012d} into a bounded buffer; print mode emits the same presentation through the selected transport.',
      design='Keep the callable primitive, single-process sampling harness and optional second translation unit directly reviewable as handwritten C++.',
      tradeoffs='These primitives define workloads, not hardware conclusions. Five warmups and thirty samples do not make first invocation a cold-JIT measurement.',
      reading_order=['test/conformance/benchmark_calls.hpp', 'test/conformance/benchmark.cpp', 'test/conformance/benchmark_extra.cpp'],
      tests=[['{cxx}', '-std=c++20', '-O2', '-fno-fast-math', '-Iinclude', 'test/conformance/benchmark.cpp', '-o', '{output}/benchmark-smoke'],
             ['{output}/benchmark-smoke', '0', '0', '0', '1', '8', '1']],
      docs='Memory and print modes are separate workload primitives. Input values are exact binary fractions; shortest conversion is compared with fmt in memory only.')

benchmark_tests = '''"""Measurement protocol rejects malformed or ambiguous sample records."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import benchmark

class BenchmarkProtocolTests(unittest.TestCase):
    def record(self, count=30):
        return dict(schema_version=1, samples_ns=[10] * count,
                    warmups=5, iterations=2, calls=1)

    def process(self, records):
        return dict(stderr=b"".join(json.dumps(record, separators=(",", ":")).encode() + b"\\n" for record in records))

    def test_a_missing_or_duplicate_protocol_record_fails(self):
        for records in ([], [self.record(), self.record()]):
            with self.subTest(records=len(records)), self.assertRaises(ValueError):
                benchmark.metrics(self.process(records))

    def test_incomplete_sample_batches_fail(self):
        with self.assertRaises(ValueError):
            benchmark.metrics(self.process([self.record(29)]))

    def test_sample_normalization_uses_iterations_and_calls(self):
        metrics = benchmark.metrics(self.process([self.record()]))
        self.assertEqual(metrics["median_ns"], 10)
        self.assertEqual(metrics["median_ns_per_call"], 5)
'''
stage('benchmark-driver', 'Verify benchmark output before collecting timing samples', {
    'tools/benchmark.py': without_resources(benchmark),
    'test/conformance/test_benchmark.py': benchmark_tests,
}, dependencies=['benchmark-primitives', 'tool-snapshots'],
      problem='Fast timing numbers are meaningless if the candidate truncates output or executes a different workload.',
      example='Before measuring integer memory formatting, compare its emitted verification bytes with a separate pinned fmt executable.',
      design='Snapshot sources and benchmark primitives, compare output before timing, validate sample counts and checksums, and retain exact commands and source identities.',
      tradeoffs='Host wall timing includes launch and synchronization for accelerators. Verification process time and first batch are recorded separately; neither is a cold-JIT claim.',
      reading_order=['tools/benchmark.py:main', 'tools/benchmark.py:build', 'tools/benchmark.py:metrics', 'test/conformance/test_benchmark.py'],
      tests=['python3 -m unittest discover -s test/conformance -p test_benchmark.py', 'python3 tools/benchmark.py --route host-buffer --family integer --mode memory --capacity 128 --memory-iterations 128'],
      docs='Output verification precedes timing. Manifests retain source snapshots, runner files, exact compiler commands and timer policy; campaign conclusions belong in ffmt-evaluation.')

benchmark_resource = subprocess.check_output(['git', 'show', 'aeff043:test/conformance/benchmark_resource.cpp'], cwd=SOURCE, text=True)
benchmark_resource = subprocess.run(['/soft/compilers/llvm/release-22.1.8/bin/clang-format'], input=benchmark_resource,
                                    stdout=subprocess.PIPE, text=True, check=True).stdout
stage('benchmark-resources', 'Retain compiler resource reports independently of timing measurements', {
    'tools/benchmark.py': benchmark,
    'test/conformance/benchmark_resource.cpp': benchmark_resource,
}, dependencies=['benchmark-driver'],
      problem='Object size, static compiler frame size, accelerator scratch and registers describe different resources and must not be conflated with measured runtime.',
      example='--resources-only compiles one- and two-call probes and preserves the compiler report without claiming device execution.',
      design='Keep raw tool output, object hashes and backend image metadata beside parsed resource fields; distinguish compile-only probe outcomes from timing rows.',
      tradeoffs='Tool availability and diagnostic wording vary. Static frame reports exclude cumulative call depth; linked-image and conversion-table sizes are separate measurements.',
      reading_order=['test/conformance/benchmark_resource.cpp', 'tools/benchmark.py:resources', 'tools/benchmark.py:image_tables'],
      tests=['python3 -m unittest discover -s test/conformance -p test_benchmark.py', 'python3 tools/benchmark.py --route host-buffer --resources-only --family integer --mode memory --capacity 128'],
      docs='Resource probes are compile-only evidence. Compiler frames, scratch, registers, retained tables and image sizes are named separately and retain raw commands and diagnostics.')

# Materialize the final owned files for independent review and lightweight
# Python regression checks. Root owns Git commits and build-system integration.
order = ['tool-process', 'tool-negative', 'tool-host-oracle', 'tool-snapshots', 'tool-isolation',
         'tool-adapter-support', 'tool-cuda', 'tool-hip', 'tool-sycl', 'tool-openmp', 'tool-kokkos',
         'tool-oracle-negatives', 'tool-engine-cases', 'tool-numeric-memory',
         'tool-memory-cuda', 'tool-memory-hip', 'tool-memory-sycl', 'tool-memory-openmp', 'tool-memory-kokkos',
         'coverage-metrics', 'benchmark-primitives', 'benchmark-driver', 'benchmark-resources']
for directory in EXPORT.iterdir():
    if directory.is_dir() and directory.name not in order:
        shutil.rmtree(directory)
for directory in EXPORT.rglob('__pycache__'):
    shutil.rmtree(directory)
for identifier in order:
    for path in (EXPORT / identifier / 'files').rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            destination = SOURCE / path.relative_to(EXPORT / identifier / 'files')
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(path.read_bytes())
for path in (PROJECT / 'feature-source/test/conformance').glob('cases_*.py'):
    shutil.copyfile(path, SOURCE / 'test/conformance' / path.name)
(EXPORT / 'index.json').write_text(json.dumps(order, indent=2) + '\n')


