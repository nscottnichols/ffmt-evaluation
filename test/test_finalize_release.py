"""Offline checks for validated shared release finalization."""
import datetime
import grp
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("jlse_finalize_release", ROOT / "tools/jlse/finalize_release.py")
finalize = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finalize)
COMMIT = "a" * 40


class ReleaseFinalizerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.release = self.base / "releases/r1"
        self.manifests = self.release / "manifests"
        self.manifests.mkdir(parents=True)
        self.group = grp.getgrgid(os.getgid()).gr_name
        self.write_json(self.manifests / "release.json", {
            "schema_version": 1,
            "release": "r1",
            "state": "provisioning",
            "access_group": self.group,
            "components": {},
            "qualification": {"nnichols": "pending", "bertoni": "pending"},
        })
        self.kokkos = self.make_source_component()
        self.archive, self.archive_record = self.make_archive_component()
        self.host_record = self.make_host_component()
        self.component_job("rome", "provision-1", "rome", {
            "kokkos-serial": self.kokkos,
            "host-runtime": self.host_record,
        })
        self.component_job("chiatta", "provision-2", "chiatta", {
            "intel-llvm": self.archive_record,
        })
        self.component_job("mi300x", "provision-fetch", "mi300x", {
            "adaptivecpp": {"source": "/outside/source", "status": "source-ready"},
        })

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def write_json(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n")

    @staticmethod
    def git(source, *arguments):
        return subprocess.check_output(["git", "-C", str(source), *arguments], text=True).strip()

    def make_source_component(self):
        scope = self.release / "software/rome"
        source = scope / "src/kokkos"
        build = scope / "build/kokkos-serial"
        prefix = scope / "install/kokkos-serial"
        source.mkdir(parents=True)
        build.mkdir(parents=True)
        prefix.mkdir(parents=True)
        (source / "fixture.txt").write_text("pinned source\n")
        self.git(source, "init", "--quiet")
        self.git(source, "add", "fixture.txt")
        self.git(source, "-c", "user.name=Release Test", "-c", "user.email=release@example.invalid",
                 "commit", "--quiet", "-m", "Fixture")
        commit = self.git(source, "rev-parse", "HEAD")
        (source / "fixture.txt").write_text("recorded local patch\n")
        patch = subprocess.check_output(["git", "-C", str(source), "diff", "--binary"])
        patch_hash = hashlib.sha256(patch).hexdigest()
        (build / "CMakeCache.txt").write_text(f"CMAKE_HOME_DIRECTORY:INTERNAL={source}\n")
        return {"prefix": str(prefix), "build_directory": str(build), "source_commit": commit,
                "source_patch_sha256": patch_hash, "status": "installed"}

    def make_archive_component(self):
        scope = self.release / "software/chiatta"
        archive = scope / "downloads/sycl_linux.tar.gz"
        prefix = scope / "install/intel-llvm"
        archive.parent.mkdir(parents=True)
        prefix.mkdir(parents=True)
        archive.write_bytes(b"pinned archive fixture")
        record = {"archive": str(archive), "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                  "prefix": str(prefix), "status": "installed"}
        return archive, record

    def make_host_component(self):
        prefix = self.release / "software/rome/install/host-runtime"
        target = self.base / "libstdc++.so.6"
        target.write_bytes(b"host runtime")
        link = prefix / "lib/libstdc++.so.6"
        link.parent.mkdir(parents=True)
        link.symlink_to(target)
        return {"prefix": str(prefix), "path": str(link), "target": str(target), "status": "installed"}

    def component_job(self, profile, jobid, scope, components):
        path = self.manifests / "components" / profile / jobid / "manifest.json"
        self.write_json(path, {
            "schema_version": 1,
            "profile": profile,
            "deployment_root": str(self.release),
            "storage_scope": scope,
            "cobalt_jobid": jobid.removeprefix("provision-"),
            "components": components,
        })
        return path

    def evidence(self, account, pipeline_id):
        return {
            "account": account,
            "release_root": str(self.release),
            "tested_commit": COMMIT,
            "pipeline": {
                "id": pipeline_id,
                "sha": COMMIT,
                "status": "success",
                "web_url": f"https://gitlab.jlse.anl.gov/bertoni/ffmt/-/pipelines/{pipeline_id}",
                "user": {"username": account},
                "created_at": "2026-11-11T00:00:00+00:00",
                "updated_at": "2026-11-11T01:00:00+00:00",
                "qualified_jobs": [{
                    "id": pipeline_id + 1000,
                    "name": "jlse-runtime-h100",
                    "status": "success",
                    "web_url": f"https://gitlab.jlse.anl.gov/bertoni/ffmt/-/jobs/{pipeline_id + 1000}",
                }],
            },
        }

    def qualification_paths(self):
        paths = {}
        for account, pipeline_id in (("nnichols", 101), ("bertoni", 102)):
            path = self.base / f"{account}.json"
            self.write_json(path, self.evidence(account, pipeline_id))
            paths[account] = path
        return paths

    def test_finalize_aggregates_installed_components_and_freezes(self):
        result = finalize.finalize_release(self.release, self.group, COMMIT, self.qualification_paths())
        recorded = json.loads((self.manifests / "release.json").read_text())
        self.assertEqual(result, recorded)
        self.assertEqual(recorded["state"], "ready")
        self.assertIs(recorded["frozen"], True)
        self.assertEqual(recorded["tested_commit"], COMMIT)
        self.assertEqual(set(recorded["components"]), {"rome", "chiatta"})
        self.assertEqual(set(recorded["components"]["rome"]), {"kokkos-serial", "host-runtime"})
        self.assertEqual(recorded["components"]["rome"]["kokkos-serial"]["provisioning_manifest"],
                         "manifests/components/rome/provision-1/manifest.json")
        self.assertEqual(recorded["qualification"]["nnichols"]["pipeline"]["id"], 101)
        self.assertEqual(recorded["qualification"]["bertoni"]["pipeline"]["id"], 102)
        self.assertEqual(recorded["access"], {"group": self.group, "status": "normalized"})
        datetime.datetime.fromisoformat(recorded["frozen_utc"])
        self.assertEqual(list(self.manifests.glob(".release-*.tmp")), [])
        self.assertFalse((self.release.parent / "current").exists())

    def test_qualification_rejects_mismatched_or_unsuccessful_evidence(self):
        def change_status(evidence):
            evidence["pipeline"]["status"] = "canceled"

        def change_root(evidence):
            evidence["release_root"] = str(self.base / "releases/other")

        def change_pipeline_commit(evidence):
            evidence["pipeline"]["sha"] = "b" * 40

        def reverse_timestamps(evidence):
            evidence["pipeline"]["created_at"] = "2026-11-11T02:00:00+00:00"

        for name, change in (("status", change_status), ("root", change_root),
                             ("commit", change_pipeline_commit), ("timestamps", reverse_timestamps)):
            with self.subTest(name=name):
                evidence = self.evidence("nnichols", 101)
                change(evidence)
                with self.assertRaises(finalize.ReleaseError):
                    finalize.validate_qualification(evidence, "nnichols", self.release, COMMIT)

    def test_failed_pipeline_with_successful_qualified_jobs_is_accepted(self):
        evidence = self.evidence("nnichols", 101)
        evidence["pipeline"]["status"] = "failed"
        qualified = finalize.validate_qualification(evidence, "nnichols", self.release, COMMIT)
        self.assertEqual(qualified["status"], "qualified")
        self.assertEqual(qualified["pipeline"]["status"], "failed")

    def test_manual_pipeline_with_completed_automatic_jobs_is_accepted(self):
        evidence = self.evidence("nnichols", 101)
        evidence["pipeline"]["status"] = "manual"
        qualified_job = evidence["pipeline"]["qualified_jobs"][0]
        evidence["pipeline"]["automatic_jobs"] = [
            dict(qualified_job),
            {
                "id": 1102,
                "name": "known-structural-failure",
                "status": "failed",
                "web_url": "https://gitlab.jlse.anl.gov/bertoni/ffmt/-/jobs/1102",
            },
        ]
        qualified = finalize.validate_qualification(evidence, "nnichols", self.release, COMMIT)
        self.assertEqual(qualified["status"], "qualified")
        self.assertEqual(qualified["pipeline"]["status"], "manual")

    def test_manual_pipeline_requires_completed_automatic_jobs(self):
        for name, automatic_jobs in (
                ("missing", None),
                ("empty", []),
                ("running", [{
                    "id": 1101,
                    "name": "jlse-runtime-h100",
                    "status": "running",
                    "web_url": "https://gitlab.jlse.anl.gov/bertoni/ffmt/-/jobs/1101",
                }]),
                ("manual", [{
                    "id": 1101,
                    "name": "intentionally-unqualified",
                    "status": "manual",
                    "web_url": "https://gitlab.jlse.anl.gov/bertoni/ffmt/-/jobs/1101",
                }])):
            with self.subTest(name=name):
                evidence = self.evidence("nnichols", 101)
                evidence["pipeline"]["status"] = "manual"
                if automatic_jobs is not None:
                    evidence["pipeline"]["automatic_jobs"] = automatic_jobs
                with self.assertRaisesRegex(finalize.ReleaseError,
                                            "completed automatic jobs|automatic job was not completed"):
                    finalize.validate_qualification(evidence, "nnichols", self.release, COMMIT)

    def test_manual_pipeline_requires_qualified_jobs_in_automatic_jobs(self):
        evidence = self.evidence("nnichols", 101)
        evidence["pipeline"]["status"] = "manual"
        evidence["pipeline"]["automatic_jobs"] = [{
            "id": 1102,
            "name": "another-runtime-job",
            "status": "success",
            "web_url": "https://gitlab.jlse.anl.gov/bertoni/ffmt/-/jobs/1102",
        }]
        with self.assertRaisesRegex(finalize.ReleaseError, "must be completed automatic jobs"):
            finalize.validate_qualification(evidence, "nnichols", self.release, COMMIT)

    def test_failed_pipeline_without_qualified_jobs_is_rejected(self):
        evidence = self.evidence("nnichols", 101)
        evidence["pipeline"]["status"] = "failed"
        evidence["pipeline"]["qualified_jobs"] = []
        with self.assertRaisesRegex(finalize.ReleaseError, "runtime-consuming jobs"):
            finalize.validate_qualification(evidence, "nnichols", self.release, COMMIT)

    def test_failed_qualified_job_is_rejected(self):
        evidence = self.evidence("nnichols", 101)
        evidence["pipeline"]["status"] = "failed"
        evidence["pipeline"]["qualified_jobs"][0]["status"] = "failed"
        with self.assertRaisesRegex(finalize.ReleaseError, "qualified job was not successful"):
            finalize.validate_qualification(evidence, "nnichols", self.release, COMMIT)

    def test_pipeline_user_mismatch_is_rejected(self):
        evidence = self.evidence("nnichols", 101)
        evidence["pipeline"]["user"]["username"] = "bertoni"
        with self.assertRaisesRegex(finalize.ReleaseError, "pipeline user mismatch"):
            finalize.validate_qualification(evidence, "nnichols", self.release, COMMIT)

    def test_component_verification_rejects_external_paths(self):
        outside = self.base / "outside"
        outside.mkdir()
        record = dict(self.kokkos, prefix=str(outside))
        with self.assertRaisesRegex(finalize.ReleaseError, "inside the release"):
            finalize.verify_component(record, self.release, "rome/kokkos-serial")

    def test_component_verification_rejects_archive_hash_mismatch(self):
        self.archive.write_bytes(b"changed archive")
        with self.assertRaisesRegex(finalize.ReleaseError, "SHA-256 mismatch"):
            finalize.verify_component(self.archive_record, self.release, "chiatta/intel-llvm")

    def test_component_verification_rejects_source_patch_mismatch(self):
        source = self.release / "software/rome/src/kokkos/fixture.txt"
        source.write_text("unrecorded patch\n")
        with self.assertRaisesRegex(finalize.ReleaseError, "source patch SHA-256 mismatch"):
            finalize.verify_component(self.kokkos, self.release, "rome/kokkos-serial")

    def test_git_verification_disables_optional_locks(self):
        with mock.patch.object(finalize.subprocess, "check_output", return_value=b"") as git_output:
            finalize.git_output(Path("/source"), "diff", "--binary")
        self.assertEqual(git_output.call_args.kwargs["env"]["GIT_OPTIONAL_LOCKS"], "0")

    def test_component_verification_checks_adapter_hashes(self):
        prefix = self.release / "software/rome/install/kokkos-serial"
        adapter = prefix / "bin/llvm-spirv-20"
        translator = prefix / "bin/llvm-spirv"
        adapter.parent.mkdir(parents=True)
        adapter.write_bytes(b"adapter")
        translator.write_bytes(b"translator")
        record = {
            "prefix": str(prefix),
            "typed_pointer_adapter": {
                "path": str(adapter),
                "sha256": hashlib.sha256(adapter.read_bytes()).hexdigest(),
                "translator": str(translator),
                "translator_sha256": hashlib.sha256(translator.read_bytes()).hexdigest(),
            },
        }
        finalize.verify_component(record, self.release, "rome/kokkos-serial")
        adapter.write_bytes(b"changed adapter")
        with self.assertRaisesRegex(finalize.ReleaseError, "SHA-256 mismatch"):
            finalize.verify_component(record, self.release, "rome/kokkos-serial")

    def test_duplicate_installed_component_is_rejected(self):
        self.component_job("rome", "provision-3", "rome", {"kokkos-serial": self.kokkos})
        with self.assertRaisesRegex(finalize.ReleaseError, "duplicate installed component"):
            finalize.aggregate_components(self.release)

    def test_access_verification_detects_missing_group_read(self):
        private = self.release / "software/rome/private"
        private.write_text("private")
        private.chmod(0o600)
        with self.assertRaisesRegex(finalize.ReleaseError, "group read/search"):
            finalize.verify_access(self.release, self.group)

    def test_rejected_finalization_preserves_original_manifest(self):
        path = self.manifests / "release.json"
        original = path.read_bytes()
        qualifications = self.qualification_paths()
        del qualifications["bertoni"]
        with mock.patch.object(finalize, "normalize_access") as normalize:
            with self.assertRaisesRegex(finalize.ReleaseError, "nnichols and bertoni"):
                finalize.finalize_release(self.release, self.group, COMMIT, qualifications)
        normalize.assert_not_called()
        self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
