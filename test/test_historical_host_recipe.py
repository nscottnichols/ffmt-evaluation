"""Historical host fixtures require an explicit runner when the library moves on."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
spec = importlib.util.spec_from_file_location("historical_host_tests", ROOT / "tools/jlse/host_tests.py")
host_tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host_tests)


class HistoricalHostFixtureTests(unittest.TestCase):
    def run_preflight(self, checkout, output, fixture, runner):
        arguments = ["host_tests.py", "--profile", "local", "--ffmt-checkout",
                     str(checkout), "--test", fixture]
        with mock.patch.dict(os.environ, {"COBALT_JOBID": "offline-fixture"}), \
                mock.patch.object(sys, "argv", arguments), \
                mock.patch.object(host_tests, "ROOT", output), \
                mock.patch.object(host_tests.evaluation, "load_conformance",
                                  return_value=(runner, checkout, checkout)):
            host_tests.main()

    def test_missing_fixture_fails_before_snapshot_or_compiler(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "modern-runner"
            output = Path(temporary) / "evaluation"
            runner = SimpleNamespace(snapshot=mock.Mock(), run=mock.Mock())
            with contextlib.redirect_stderr(io.StringIO()) as diagnostic, \
                    self.assertRaises(SystemExit) as error:
                self.run_preflight(checkout, output, "test_engine.cpp", runner)
            self.assertEqual(error.exception.code, 2)
            self.assertIn("test_engine.cpp", diagnostic.getvalue())
            self.assertIn("--runner-revision 4b8cf257fc68c5b20c0c493e34d1d90269e76fd9",
                          diagnostic.getvalue())
            self.assertIn("tools/jlse/build_checks.py", diagnostic.getvalue())
            runner.snapshot.assert_not_called()
            runner.run.assert_not_called()
            self.assertFalse(output.exists())

    def test_selected_historical_fixture_proceeds_to_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "historical-runner"
            fixture = checkout / "test/conformance/test_engine.cpp"
            fixture.parent.mkdir(parents=True)
            fixture.write_text("// original fixture stand-in\n")
            output = Path(temporary) / "evaluation"
            # The portable-shortest variant shares test_engine.cpp; do not
            # require an artificial test_engine_portable.cpp fixture.
            stop = RuntimeError("snapshot boundary reached")
            runner = SimpleNamespace(snapshot=mock.Mock(side_effect=stop), run=mock.Mock())
            with self.assertRaisesRegex(RuntimeError, "snapshot boundary reached"):
                self.run_preflight(checkout, output, "test_engine_portable.cpp", runner)
            runner.snapshot.assert_called_once()
            runner.run.assert_not_called()
