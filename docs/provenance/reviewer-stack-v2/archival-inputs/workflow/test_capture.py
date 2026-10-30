"""Portable safety/byte-preservation checks for the evidence packager."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('capture.py')


class Capture(unittest.TestCase):
    def run_capture(self, *arguments):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, arguments)],
                              capture_output=True, text=True)

    def test_visible_inputs_raw_nuls_hashes_and_build_exclusions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attempt = root / 'attempt'
            attempt.mkdir()
            (attempt / 'manifest.json').write_text(json.dumps(dict(
                status='failure', finished='captured', cobalt_jobid='42', stages=[])))
            (attempt / 'runner.py').write_text('# handwritten runner\n')
            raw = b'prefix\x00suffix\n'
            (attempt / 'run.stdout').write_bytes(raw)
            (attempt / 'probe.cpp').write_text('// generated probe\n')
            (attempt / 'probe.o').write_bytes(b'compiler object')
            (attempt / 'program').write_bytes(b'\x7fELFbinary')
            for directory, marker in [('source', 'checkout.hpp'), ('cmake-output', 'CMakeCache.txt')]:
                target = attempt / directory
                target.mkdir()
                (target / marker).write_text('excluded')
                (target / 'unused.stdout').write_text('excluded')
            fixture = root / 'fixture.cpp.in'
            fixture.write_text('// handwritten template\n')
            output = root / 'capture'
            result = self.run_capture('--validation', attempt, '--input',
                                      'fixture.cpp.in=' + str(fixture), '--output', output)
            self.assertEqual(result.returncode, 0, result.stderr)
            inventory = json.loads((output / 'capture.json').read_text())
            names = {item['relative_path'] for item in inventory['files']}
            self.assertEqual(names, {'validation/manifest.json', 'validation/runner.py',
                                    'validation/run.stdout', 'validation/probe.cpp', 'fixture.cpp.in'})
            self.assertEqual((output / 'fixture.cpp.in').read_bytes(), fixture.read_bytes())
            with tarfile.open(output / 'raw-logs.tar.gz') as archive:
                self.assertEqual(archive.extractfile('validation/run.stdout').read(), raw)
            self.assertEqual(self.run_capture('--output', output, '--verify').returncode, 0)
            (output / 'validation/runner.py').write_text('changed')
            self.assertNotEqual(self.run_capture('--output', output, '--verify').returncode, 0)

    def test_active_attempt_and_reserved_path_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            attempt = root / 'attempt'
            attempt.mkdir()
            (attempt / 'manifest.json').write_text('{"status":"running"}')
            output = root / 'capture'
            self.assertNotEqual(self.run_capture('--validation', attempt, '--output', output).returncode, 0)
            self.assertFalse(output.exists())
            fixture = root / 'README.md'
            fixture.write_text('must not be overwritten')
            self.assertNotEqual(self.run_capture('--input', 'README.md=' + str(fixture),
                                                '--output', output).returncode, 0)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
