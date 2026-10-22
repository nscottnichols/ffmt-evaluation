"""Offline checks for repository separation and honest evidence publication."""
import contextlib
import hashlib
import io
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import evaluation
import report

submission_spec = importlib.util.spec_from_file_location("jlse_submit", evaluation.ROOT / "tools/jlse/submit.py")
submission = importlib.util.module_from_spec(submission_spec)
submission_spec.loader.exec_module(submission)


class ExternalCheckoutTests(unittest.TestCase):
    def repository(self, path, content="header"):
        (path / "include/ffmt").mkdir(parents=True)
        (path / "include/ffmt/core.hpp").write_text(content)
        (path / "tools").mkdir()
        # A harmless stand-in exercises the real process and path boundary.
        source = '''# FFMT_WORKSPACE FFMT_SOURCE_ROOT
import argparse,json,os
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--output',required=True)
a,extra=p.parse_known_args()
out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
(out/'manifest.json').write_text(json.dumps(dict(arguments=extra,
    workspace=os.environ['FFMT_WORKSPACE'], source=os.environ['FFMT_SOURCE_ROOT'])))
'''
        for tool in ("conformance", "benchmark"):
            (path / "tools" / (tool + ".py")).write_text(source)
        subprocess.run(["git", "init", "--quiet", "--template=", str(path)], check=True)
        subprocess.run(["git", "-C", str(path), "add", "."], check=True)
        subprocess.run(["git", "-C", str(path), "-c", "user.name=ffmt test", "-c",
                        "user.email=test@example.invalid", "-c", "core.hooksPath=/dev/null",
                        "commit", "--quiet", "--no-gpg-sign", "-m", "fixture"], check=True)
        return evaluation.git(path, "rev-parse", "HEAD")

    def workspace(self, path):
        path.mkdir()
        (path / "tools").mkdir()
        for filename in ("evaluation.py", "conformance.py", "benchmark.py"):
            (path / "tools" / filename).write_bytes((evaluation.ROOT / "tools" / filename).read_bytes())
        profiles = path / "platforms/profiles.json"
        profiles.parent.mkdir()
        profiles.write_text(json.dumps(dict(profiles={"local": {}, "rome": {"queue": "rome_7742"}},
                                            baseline_commit="3" * 40)))
        subprocess.run(["git", "init", "--quiet", "--template=", str(path)], check=True)
        subprocess.run(["git", "-C", str(path), "-c", "user.name=ffmt test", "-c",
                        "user.email=test@example.invalid", "-c", "core.hooksPath=/dev/null",
                        "commit", "--allow-empty", "--quiet", "--no-gpg-sign", "-m", "evaluation fixture"], check=True)
        return profiles

    def arguments(self, checkout=None, **changes):
        values = dict(ffmt_checkout=checkout, source_root=None, runner_revision=None,
                      ffmt_repository=evaluation.DEFAULT_REPOSITORY, revision=None)
        values.update(changes)
        return SimpleNamespace(**values)

    def test_missing_checkout_requires_an_immutable_pin(self):
        with self.assertRaisesRegex(ValueError, "40-character"):
            evaluation.select_sources(self.arguments())
        with self.assertRaisesRegex(ValueError, "40-character"):
            evaluation.select_sources(self.arguments(runner_revision="main"))

    def test_runner_source_and_workspace_are_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runner = base / "runner"
            target = base / "target"
            runner_commit = self.repository(runner, "runner-header")
            source_commit = self.repository(target, "target-header")
            workspace = base / "evaluation"
            profiles = self.workspace(workspace)
            with mock.patch.object(evaluation, "ROOT", workspace), mock.patch.object(evaluation, "PROFILES", profiles):
                checkout, source, revision, environment = evaluation.select_sources(
                    self.arguments(runner, source_root=target, revision=source_commit))
                self.assertEqual((checkout, source, revision), (runner, target, source_commit))
                self.assertEqual(environment["FFMT_WORKSPACE"], str(workspace))
                self.assertEqual(environment["FFMT_SOURCE_ROOT"], str(target))
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(evaluation.launch("conformance", ["--ffmt-checkout", str(runner),
                        "--source-root", str(target), "--revision", source_commit,
                        "--output", "artifacts/smoke", "--case", "literal"]), 0)
                result = json.loads((workspace / "artifacts/smoke/manifest.json").read_text())
                self.assertEqual(result["source"], str(target))
                receipts = list((workspace / "artifacts/launchers").glob("*.json"))
                self.assertEqual(len(receipts), 1)
                receipt = json.loads(receipts[0].read_text())
                self.assertEqual(receipt["sources"]["runner_commit"], runner_commit)
                self.assertEqual(receipt["sources"]["source_commit"], source_commit)
                self.assertEqual(receipt["manifest_sha256"], hashlib.sha256(
                    (workspace / "artifacts/smoke/manifest.json").read_bytes()).hexdigest())
                self.assertFalse((workspace / "include").exists())

    def test_explicit_pin_bootstraps_once_and_preserves_source_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repository = base / "upstream"
            commit = self.repository(repository)
            workspace = base / "evaluation"
            profiles = self.workspace(workspace)
            with mock.patch.object(evaluation, "ROOT", workspace), mock.patch.object(evaluation, "PROFILES", profiles):
                selected = evaluation.select_sources(self.arguments(ffmt_repository=str(repository), runner_revision=commit))
                checkout, source, revision, _ = selected
                self.assertTrue(checkout.is_relative_to(workspace / "software/local"))
                self.assertEqual(source, checkout)
                self.assertEqual(revision, commit)
                with mock.patch.object(evaluation.subprocess, "run", wraps=subprocess.run) as operation:
                    self.assertEqual(evaluation.bootstrap(str(repository), commit), checkout)
                    self.assertFalse(any("clone" in call.args[0] or "fetch" in call.args[0]
                                         for call in operation.call_args_list))

    def test_dry_run_does_not_create_evidence_or_submit(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runner = base / "runner"
            self.repository(runner)
            workspace = base / "evaluation"
            profiles = self.workspace(workspace)
            with mock.patch.object(evaluation, "ROOT", workspace), mock.patch.object(evaluation, "PROFILES", profiles), \
                    mock.patch.object(evaluation.subprocess, "run", wraps=subprocess.run) as operation, \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(evaluation.launch("benchmark", ["--ffmt-checkout", str(runner),
                    "--profile", "rome", "--dry-run", "--family", "integer"]), 0)
                command = json.loads(output.getvalue())["command"]
                self.assertEqual(command[1], str(runner / "tools/benchmark.py"))
                self.assertTrue(all(call.args[0][0] == "git" for call in operation.call_args_list))
                self.assertFalse((workspace / "artifacts").exists())

    def test_accelerator_campaign_requires_allocation_before_resolving_sources(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(evaluation, "select_sources") as selection, \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            evaluation.launch("conformance", ["--profile", "rome"])
        self.assertEqual(error.exception.code, 2)
        selection.assert_not_called()

    def test_scheduler_defaults_pin_source_head_and_keep_explicit_revisions(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            runner = base / "runner"
            source = base / "source"
            self.repository(runner, "runner")
            baseline = self.repository(source, "baseline")
            (source / "include/ffmt/core.hpp").write_text("source HEAD")
            subprocess.run(["git", "-C", str(source), "add", "."], check=True)
            subprocess.run(["git", "-C", str(source), "-c", "user.name=ffmt test", "-c",
                            "user.email=test@example.invalid", "-c", "core.hooksPath=/dev/null",
                            "commit", "--quiet", "--no-gpg-sign", "-m", "head"], check=True)
            head = evaluation.git(source, "rev-parse", "HEAD")
            workspace = base / "evaluation"
            profiles = self.workspace(workspace)
            configuration = json.loads(profiles.read_text())
            configuration["baseline_commit"] = baseline
            profiles.write_text(json.dumps(configuration))
            for stage in ("baseline", "head", "benchmark", "host-tests", "provision", "discovery", "diagnostics"):
                for explicit in (None, baseline, "WORKTREE"):
                    with self.subTest(stage=stage, revision=explicit):
                        argv = ["submit.py", stage, "rome", "--ffmt-checkout", str(runner),
                                "--source-root", str(source), "--dry-run"]
                        if explicit:
                            argv += ["--revision", explicit]
                        with mock.patch.object(evaluation, "ROOT", workspace), mock.patch.object(evaluation, "PROFILES", profiles), \
                                mock.patch.object(submission, "ROOT", workspace), mock.patch.object(sys, "argv", argv), \
                                contextlib.redirect_stdout(io.StringIO()) as output:
                            submission.main()
                        expected = explicit or (baseline if stage == "baseline" else head)
                        command = shlex.split(output.getvalue())
                        self.assertEqual(command[0], "qsub")
                        self.assertEqual(command[-4:], [str(workspace / "tools/jlse/job.sh"), "rome", stage, expected])
                        self.assertFalse((workspace / "artifacts").exists())

    def test_direct_shell_bridge_uses_external_source_head(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            head = self.repository(source)
            workspace = base / "evaluation"
            self.workspace(workspace)
            tools = workspace / "tools/jlse"
            tools.mkdir()
            (tools / "job.sh").write_bytes((evaluation.ROOT / "tools/jlse/job.sh").read_bytes())
            (tools / "environment.sh").write_text("export FFMT_PYTHON=" + shlex.quote(sys.executable) + "\n")
            (tools / "discover.py").write_text("# no hardware inspection in this fixture\n")
            (workspace / "tools/conformance.py").write_text("# no compiler execution in this fixture\n")
            environment = dict(os.environ, FFMT_CHECKOUT=str(source), FFMT_SOURCE_ROOT=str(source))
            environment.pop("FFMT_JOB_ENV_FILE", None)
            result = subprocess.run(["/bin/bash", str(tools / "job.sh"), "rome", "head"],
                                    env=environment, capture_output=True, text=True, check=True)
            self.assertIn("profile=rome stage=head revision=" + head + "\n", result.stdout)


class ReportEvidenceTests(unittest.TestCase):
    def manifest(self, directory, status, case_status, fatal=None):
        path = directory / "manifest.json"
        data = dict(profile="local", label="test", started="test", source={}, oracle={}, host={},
            configurations=[dict(route="host-buffer", optimization=2, status=status,
                cases=[dict(id="case", status=case_status)])])
        if fatal:
            data["fatal_error"] = fatal
        path.write_text(json.dumps(data))
        return path

    def test_auxiliary_fatal_error_cannot_publish_a_completed_config(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(report, "ROOT", Path(temporary)):
            path = self.manifest(Path(temporary), "completed", "pass", "numeric oracle failed")
            result = report.summarize(path, terminal_only=True)
            self.assertEqual(result["configurations"], [])
            self.assertEqual(result["fatal_error"], "numeric oracle failed")
            self.assertEqual(result["unfinished_configurations"][0]["positive_counts"], {"pass": 1})

    def test_terminal_selection_retains_failed_controls(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(report, "ROOT", Path(temporary)):
            path = self.manifest(Path(temporary), "control_compile_failure", "not_run")
            result = report.summarize(path, terminal_only=True)
            self.assertEqual(result["unfinished_configurations"], [])
            config = result["configurations"][0]
            self.assertEqual(config["status"], "control_compile_failure")
            self.assertEqual(config["positive_executions"], 0)

    def test_symlinked_evidence_storage_preserves_logical_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "evaluation"
            storage = Path(temporary) / "preserved-artifacts"
            root.mkdir()
            storage.mkdir()
            (root / "artifacts").symlink_to(storage, target_is_directory=True)
            path = self.manifest(storage, "completed", "pass")
            with mock.patch.object(report, "ROOT", root):
                result = report.summarize(path.resolve(), terminal_only=True)
            self.assertEqual(result["input_manifest"], "artifacts/manifest.json")


if __name__ == "__main__":
    unittest.main()
