"""Offline checks for neutral release provisioning and job path selection."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("jlse_provision", ROOT / "tools/jlse/provision.py")
provision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provision)


class DeploymentPathTests(unittest.TestCase):
    def arguments(self, root, *extra):
        return ["--profile", "mi300x", "--deployment-root", str(root),
                "--component", "host-runtime", *extra]

    def parse_error(self, arguments):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            provision.parse_args(arguments)
        self.assertEqual(error.exception.code, 2)

    def test_release_root_validation_and_storage_scope(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            release = base / "releases/r1"
            arguments = provision.parse_args(self.arguments(release))
            self.assertEqual(arguments.deployment_root, release)
            self.assertEqual(arguments.storage_scope, "mi300x")
            arguments = provision.parse_args(self.arguments(release, "--storage-scope", "x86_64"))
            self.assertEqual(arguments.storage_scope, "x86_64")
            self.parse_error(self.arguments("relative/releases/r1"))
            self.parse_error(self.arguments(base / "releases/r1/../r2"))
            self.parse_error(self.arguments(base / "r1"))
            self.parse_error(self.arguments(release, "--storage-scope", "../shared"))
            legacy = provision.parse_args(self.arguments(base / "legacy", "--allow-legacy-root"))
            self.assertEqual(legacy.deployment_root, base / "legacy")

            target = base / "target"
            target.mkdir()
            linked = base / "releases/current"
            linked.parent.mkdir(exist_ok=True)
            linked.symlink_to(target, target_is_directory=True)
            self.parse_error(self.arguments(linked))

    def test_llvm_prefix_validation_and_common_automatic_base(self):
        with tempfile.TemporaryDirectory() as temporary:
            release = Path(temporary) / "releases/r1"
            self.parse_error(self.arguments(release, "--llvm-prefix", "relative/llvm"))
            explicit = Path(temporary) / "explicit-llvm"
            arguments = provision.parse_args(self.arguments(release, "--llvm-prefix", str(explicit)))
            self.assertEqual(arguments.llvm_prefix, explicit)

            arguments = SimpleNamespace(deployment_root=release, llvm_prefix=None)
            log = io.StringIO()
            common_base = release / "software" / provision.platform.machine()
            with mock.patch.object(provision.platform, "machine", return_value="aarch64"):
                self.assertEqual(provision.common_llvm_base(arguments), release / "software/aarch64")
            with mock.patch.object(provision, "provision") as build:
                prefix = provision.llvm_dependency(arguments, log, lambda candidate: False)
                self.assertEqual(prefix, common_base / "install/llvm20-shared")
                build.assert_called_once_with("llvm-shared", arguments, common_base, log)
                self.assertTrue((common_base / "src").is_dir())

            arguments.llvm_prefix = explicit
            with mock.patch.object(provision, "provision") as build:
                prefix = provision.llvm_dependency(arguments, log,
                                                   lambda candidate: self.fail("explicit prefix must not be probed"))
                self.assertEqual(prefix, explicit)
                build.assert_not_called()

    def test_typed_adapter_retains_final_release_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            release = Path(temporary) / "releases/r1"
            base = release / "software/chiatta"
            translator = base / "install/spirv-translator/bin/llvm-spirv"
            translator.parent.mkdir(parents=True)
            translator.write_bytes(b"translator fixture")
            metadata = provision.typed_spirv_adapter(base, translator, 20)
            wrapper = Path(metadata["path"])
            self.assertIn(repr(str(translator)), wrapper.read_text())
            self.assertEqual(metadata["translator"], str(translator))
            self.assertTrue(wrapper.is_relative_to(release))


class HostRuntimeTests(unittest.TestCase):
    def test_symlink_creation_replacement_and_regular_file_rejection(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            link = base / "install/host-runtime/lib/libstdc++.so.6"
            result = provision.provision_host_runtime(base)
            self.assertTrue(link.is_symlink())
            self.assertEqual(Path(result["path"]), link)
            self.assertEqual(os.readlink(link), "/usr/lib64/libstdc++.so.6")

            link.unlink()
            link.symlink_to("/usr/lib64/libm.so.6")
            provision.provision_host_runtime(base)
            self.assertEqual(os.readlink(link), "/usr/lib64/libstdc++.so.6")

            link.unlink()
            link.write_text("preserve this regular file")
            with self.assertRaisesRegex(RuntimeError, "Refusing to replace non-symlink"):
                provision.provision_host_runtime(base)
            self.assertEqual(link.read_text(), "preserve this regular file")

    def test_manifest_and_log_stay_in_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            release = Path(temporary) / "releases/r1"
            arguments = ["--profile", "rome", "--deployment-root", str(release),
                         "--component", "host-runtime", "--access-group", str(os.getgid())]
            with mock.patch.dict(os.environ, {"COBALT_JOBID": "offline-fixture"}), \
                    contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
                provision.main(arguments)
            self.assertEqual(result.exception.code, 0)
            output = release / "manifests/components/rome/provision-offline-fixture"
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(manifest["deployment_root"], str(release))
            self.assertEqual(manifest["storage_scope"], "rome")
            self.assertEqual(manifest["components"]["host-runtime"]["status"], "installed")
            self.assertTrue((output / "host-runtime.log").is_file())
            self.assertTrue((output / "access.log").is_file())
            self.assertEqual(manifest["access"], {"group": str(os.getgid()), "status": "normalized"})
            self.assertTrue((output / "manifest.json").stat().st_mode & 0o040)
            self.assertTrue((release / "software/rome").stat().st_mode & 0o050)
            self.assertTrue((release / "software/rome/install/host-runtime/lib/libstdc++.so.6").is_symlink())
            self.assertFalse((release / "artifacts").exists())

    def test_access_group_normalizes_owner_only_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            release = Path(temporary) / "releases/r1"
            private = release / "software/rome/private"
            private.parent.mkdir(parents=True)
            private.write_text("private before provisioning")
            private.chmod(0o600)
            private.parent.chmod(0o700)
            arguments = ["--profile", "rome", "--deployment-root", str(release),
                         "--component", "host-runtime", "--access-group", str(os.getgid())]
            with mock.patch.dict(os.environ, {"COBALT_JOBID": "offline-fixture"}), \
                    contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
                provision.main(arguments)
            self.assertEqual(result.exception.code, 0)
            self.assertTrue(private.stat().st_mode & 0o040)
            self.assertTrue(private.parent.stat().st_mode & 0o050)

    def test_access_group_is_an_operand_not_an_option(self):
        with mock.patch.object(provision, "run") as run:
            provision.normalize_release_access(Path("/release"), "--help", io.StringIO())
        self.assertEqual(run.call_args_list[0].args[0],
                         ["chgrp", "-R", "-h", "--", "--help", "/release"])


class EnvironmentRuntimeTests(unittest.TestCase):
    def test_common_llvm_and_openmp_directories_are_searchable(self):
        with tempfile.TemporaryDirectory() as temporary:
            release = Path(temporary) / "releases/r1"
            architecture = os.uname().machine
            llvm = release / "software" / architecture / "install/llvm20-shared"
            (llvm / "bin").mkdir(parents=True)
            (llvm / "lib" / (architecture + "-unknown-linux-gnu")).mkdir(parents=True)
            environment = os.environ.copy()
            environment["FFMT_RUNTIME_ROOT"] = str(release)
            result = subprocess.run(
                ["bash", "--noprofile", "--norc", "-c",
                 'source "$1" h100; printf "%s\\n%s\\n" "$LD_LIBRARY_PATH" "$PATH"',
                 "environment-test", str(ROOT / "tools/jlse/environment.sh")],
                env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            library_path, executable_path = result.stdout.splitlines()[-2:]
            self.assertIn(str(llvm / "lib"), library_path.split(":"))
            self.assertIn(str(llvm / "lib" / (architecture + "-unknown-linux-gnu")), library_path.split(":"))
            self.assertNotIn(str(llvm / "bin"), executable_path.split(":"))

    def test_other_architecture_does_not_inherit_common_x86_libraries(self):
        with tempfile.TemporaryDirectory() as temporary:
            release = Path(temporary) / "releases/r1"
            llvm = release / "software/x86_64/install/llvm20-shared"
            (llvm / "lib/x86_64-unknown-linux-gnu").mkdir(parents=True)
            environment = os.environ.copy()
            environment["FFMT_RUNTIME_ROOT"] = str(release)
            result = subprocess.run(
                ["bash", "--noprofile", "--norc", "-c",
                 'uname() { if [ "$1" = -m ]; then echo aarch64; else command uname "$@"; fi; }; '
                 'source "$1" gh200; printf "%s\\n" "$LD_LIBRARY_PATH"',
                 "environment-test", str(ROOT / "tools/jlse/environment.sh")],
                env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn(str(llvm / "lib"), result.stdout.splitlines()[-1].split(":"))


class JobPathTests(unittest.TestCase):
    def fixture(self, base):
        tools = base / "tools/jlse"
        tools.mkdir(parents=True)
        job = tools / "job.sh"
        shutil.copyfile(ROOT / "tools/jlse/job.sh", job)
        (tools / "environment.sh").write_text("# offline environment fixture\n")
        (tools / "discover.py").write_text("# offline discovery fixture\n")
        (tools / "provision.py").write_text(
            "import json,os,sys\n"
            "from pathlib import Path\n"
            "Path(os.environ['FFMT_TEST_ARGUMENTS']).write_text(json.dumps(sys.argv[1:]))\n")
        return job

    def environment(self, base):
        environment = os.environ.copy()
        environment.pop("FFMT_JOB_ENV_FILE", None)
        environment.pop("FFMT_RUNTIME_ROOT", None)
        environment["FFMT_PYTHON"] = sys.executable
        environment["FFMT_TEST_ARGUMENTS"] = str(base / "arguments.json")
        return environment

    def test_discovery_does_not_create_software_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            job = self.fixture(base)
            result = subprocess.run(["bash", str(job), "rome", "discovery", "offline-revision"],
                                    cwd=base, env=self.environment(base), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((base / "software").exists())
            self.assertTrue((base / "artifacts/rome").is_dir())

    def test_provision_requires_and_forwards_runtime_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            job = self.fixture(base)
            result = subprocess.run(["bash", str(job), "rome", "provision", "offline-revision"],
                                    cwd=base, env=self.environment(base), capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("FFMT_RUNTIME_ROOT is required", result.stderr)
            self.assertFalse((base / "artifacts").exists())

            release = base / "releases/r1"
            environment = self.environment(base)
            environment["FFMT_RUNTIME_ROOT"] = str(release)
            result = subprocess.run(["bash", str(job), "rome", "provision", "offline-revision",
                                     "--component", "host-runtime"],
                                    cwd=base, env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((base / "arguments.json").read_text()),
                             ["--profile", "rome", "--deployment-root", str(release),
                              "--component", "host-runtime"])
            self.assertFalse((base / "software").exists())


if __name__ == "__main__":
    unittest.main()
