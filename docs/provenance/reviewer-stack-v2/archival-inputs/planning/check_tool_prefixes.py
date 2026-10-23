#!/usr/bin/env python3
"""Check each tooling export against only its declared local dependencies."""
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
EXPORT = ROOT / 'tool-stages'
INDEX = json.loads((EXPORT / 'index.json').read_text())
REPORTS = []

def dependencies(identifier, found=None):
    found = [] if found is None else found
    metadata = json.loads((EXPORT / identifier / 'stage.json').read_text())
    for dependency in metadata['dependencies']:
        if dependency in INDEX and dependency not in found:
            dependencies(dependency, found)
    if identifier not in found:
        found.append(identifier)
    return found

for identifier in INDEX:
    with tempfile.TemporaryDirectory(prefix='ffmt-tool-prefix-') as temporary:
        prefix = Path(temporary)
        included = dependencies(identifier)
        for dependency in included:
            source = EXPORT / dependency / 'files'
            for path in source.rglob('*'):
                if path.is_file() and '__pycache__' not in path.parts:
                    destination = prefix / path.relative_to(source)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(path.read_bytes())
        # Syntax checks parse without producing bytecode in export snapshots.
        for path in prefix.rglob('*.py'):
            ast.parse(path.read_text(), filename=str(path))
        tests = sorted((EXPORT / identifier / 'files/test/conformance').glob('test_*.py'))
        results = []
        for test in tests:
            command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s',
                       str(prefix / 'test/conformance'), '-p', test.name]
            process = subprocess.run(command, cwd=prefix, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True)
            results.append(dict(command=command, exit_code=process.returncode,
                                output=process.stdout))
        ok = all(result['exit_code'] == 0 for result in results)
        REPORTS.append(dict(stage=identifier, dependencies=included, pass_=ok, tests=results))
        print(identifier, 'PASS' if ok else 'FAIL', flush=True)
        if not ok:
            print(json.dumps(results, indent=2), flush=True)

(ROOT / 'tool-prefix-python.json').write_text(json.dumps(REPORTS, indent=2) + '\n')
sys.exit(any(not report['pass_'] for report in REPORTS))
