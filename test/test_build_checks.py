"""Keep immutable build checks independent of a different live source tree."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
spec = importlib.util.spec_from_file_location("jlse_build_checks", ROOT / "tools/jlse/build_checks.py")
build_checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_checks)


class ImmutableBuildSourceTests(unittest.TestCase):
    def exercise(self, *, failing_step=None):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "evaluation"
            root.mkdir()
            original = Path(temporary) / "live-library"
            header = original / "include/ffmt/core.hpp"
            header.parent.mkdir(parents=True)
            header.write_text("different uncommitted WORKTREE header")
            revision = "a" * 40
            observed = []

            def run(command, directory, name, timeout):
                if name == "checkout":
                    self.assertEqual(command[:3], ["git", "-C", str(original)])
                    self.assertEqual(command[-1], revision)
                    detached = Path(command[-2])
                    destination = detached / "include/ffmt/core.hpp"
                    destination.parent.mkdir(parents=True)
                    destination.write_text("immutable requested revision")
                if name in ("configure", "build", "ctest", "make-tests"):
                    # This real, harmless child inherits the same environment
                    # as the intercepted CMake/CTest/Make invocation. No C++
                    # compiler, scheduler or hardware is used by the fixture.
                    process = subprocess.run([sys.executable, "-c",
                        "import json,os;from pathlib import Path;"
                        "root=Path(os.environ['FFMT_SOURCE_ROOT']);"
                        "print(json.dumps(dict(root=str(root),header=(root/'include/ffmt/core.hpp').read_text())))"],
                        check=True, capture_output=True, text=True)
                    observed.append((name, command, json.loads(process.stdout)))
                return dict(exit_code=1 if name == failing_step else 0,
                            command=command, seconds=0, stdout=b"", stderr=b"",
                            stdout_file=str(directory / (name + ".stdout")),
                            stderr_file=str(directory / (name + ".stderr")))

            conformance = SimpleNamespace(run=run, record=lambda result: {
                key: value for key, value in result.items() if key not in ("stdout", "stderr")})
            requested_identity = dict(source_checkout=str(original), source_revision=revision,
                                      source_commit=revision, source_dirty=True)
            arguments = ["build_checks.py", "--profile", "rome", "--revision", revision,
                         "--ffmt-checkout", str(original), "--cxx", sys.executable]
            with mock.patch.object(build_checks, "ROOT", root), \
                    mock.patch.object(build_checks.evaluation, "load_conformance",
                                      return_value=(conformance, original, original)), \
                    mock.patch.object(build_checks.evaluation, "git", return_value=revision), \
                    mock.patch.object(build_checks.evaluation, "identity", return_value=requested_identity), \
                    mock.patch.dict(os.environ, {"COBALT_JOBID": "offline-fixture",
                                                 "FFMT_SOURCE_ROOT": str(original)}), \
                    mock.patch.object(sys, "argv", arguments), \
                    contextlib.redirect_stdout(io.StringIO()):
                result = build_checks.main()
                self.assertEqual(os.environ["FFMT_SOURCE_ROOT"], str(original),
                                 "Child source selection must not replace the parent's requested source")
            output = root / "artifacts/rome/build-checks-offline-fixture"
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(manifest["sources"], requested_identity)
            self.assertEqual(manifest["revision"], revision)
            self.assertEqual(manifest["build_source_checkout"], str(output / "source"))
            self.assertEqual(manifest["child_environment"], {"FFMT_SOURCE_ROOT": str(output / "source")})
            for name, command, child in observed:
                with self.subTest(step=name, command=command):
                    self.assertEqual(child["root"], str(output / "source"))
                    self.assertEqual(child["header"], "immutable requested revision")
            self.assertEqual(header.read_text(), "different uncommitted WORKTREE header")
            return result, manifest, [name for name, _, _ in observed]

    def test_ctest_and_make_children_use_detached_revision(self):
        result, manifest, steps = self.exercise()
        self.assertEqual(result, 0)
        self.assertEqual(manifest["status"], "pass")
        self.assertEqual(steps, ["configure", "build", "ctest", "make-tests"])

    def test_failed_child_preserves_requested_identity_and_restores_environment(self):
        result, manifest, steps = self.exercise(failing_step="ctest")
        self.assertEqual(result, 1)
        self.assertEqual(manifest["status"], "failure")
        self.assertIn("ctest failed", manifest["reason"])
        self.assertEqual(steps, ["configure", "build", "ctest"])


if __name__ == "__main__":
    unittest.main()
