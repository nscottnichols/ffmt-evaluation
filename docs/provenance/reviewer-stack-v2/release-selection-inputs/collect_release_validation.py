#!/usr/bin/env python3
"""Capture terminal scheduler evidence and account for exact release commits."""
from collections import Counter
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def steps(stage):
    yield 'driver', stage.get('commands', [])
    for compiler in stage.get('compilers', []):
        yield compiler['name'], compiler.get('steps', [])


def main():
    partition = json.loads((ROOT / 'release-validation-partition.json').read_text())
    index = json.loads(Path(partition['index']).read_text())
    queried = subprocess.run(['qstat', '-u', 'nnichols'], capture_output=True, text=True)
    if queried.returncode:
        raise SystemExit(queried.stderr)
    active = {line.split()[0] for line in queried.stdout.splitlines() if line.split() and line.split()[0].isdigit()}
    qualification = {}
    manifest_data = {}
    jobs = []
    for record in partition['reused']:
        manifest_data.setdefault(record['manifest'], json.loads(Path(record['manifest']).read_text()))
        qualification[(record['id'], record['commit'])] = dict(manifest=record['manifest'], reused=True)
    for system, bucket in partition['buckets'].items():
        submitted = bucket['submitted']
        submission_path = Path(submitted['submission'])
        submission = json.loads(submission_path.read_text())
        manifest_path = Path(submitted['output']) / 'manifest.json'
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
        job = dict(system=system, jobid=submission['jobid'], active=submission['jobid'] in active,
                   submission=str(submission_path), manifest=str(manifest_path),
                   status=manifest['status'] if manifest else 'awaiting_manifest')
        jobs.append(job)
        if manifest:
            manifest_data[str(manifest_path)] = manifest
            for stage in manifest['stages']:
                if stage['status'] in ('pass', 'pass_with_skips'):
                    qualification[(stage['id'], stage['commit'])] = dict(
                        manifest=str(manifest_path), reused=False, jobid=submission['jobid'])
        if manifest and manifest['status'] != 'running' and not job['active'] and not submission.get('completion'):
            logs = []
            for source in sorted(Path(submission['cobalt_output_prefix']).parent.glob(Path(submission['cobalt_output_prefix']).name + '.*')):
                target = submission_path.parent / source.name
                shutil.copy2(source, target)
                logs.append(dict(original=str(source), copy=str(target), sha256=digest(target)))
            failures = []
            for stage in manifest['stages']:
                for compiler, items in steps(stage):
                    for item in items:
                        if item['status'] == 'failure':
                            failures.append(dict(stage=stage['id'], compiler=compiler,
                                                 step=item['name'], stderr_file=item.get('stderr_file')))
            submission['completion'] = dict(captured=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                status=manifest['status'], manifest=str(manifest_path), manifest_sha256=digest(manifest_path),
                logs=logs, counts=manifest.get('counts'), failures=failures,
                runner_matches_submitted=digest(Path(submitted['output'])/'validate.py') == digest(submission_path.parent/'validate.py'),
                stages=[dict(id=s['id'], commit=s['commit'], status=s['status']) for s in manifest['stages']])
            submission_path.write_text(json.dumps(submission, indent=2)+'\n')
    rows = []
    exit77, markers = [], []
    for stage in index['stages']:
        record = qualification.get((stage['id'], stage['commit']))
        row = dict(id=stage['id'], commit=stage['commit'], qualified=bool(record))
        if record:
            row.update(record)
            manifest = manifest_data[record['manifest']]
            qualified = next(s for s in manifest['stages'] if s['id']==stage['id'] and s['commit']==stage['commit'])
            row['status'] = qualified['status']
            row['host'] = manifest.get('host', {}).get('name')
            row['manifest_sha256'] = digest(record['manifest'])
            for compiler, items in steps(qualified):
                for item in items:
                    context = dict(stage=stage['id'], commit=stage['commit'], compiler=compiler,
                                   step=item['name'], manifest=record['manifest'])
                    if item['status']=='skip':
                        exit77.append(dict(**context, exit_code=item.get('exit_code'),
                                           stdout_file=item.get('stdout_file'), stderr_file=item.get('stderr_file')))
                    if item.get('reported_skips'):
                        markers.append(dict(**context, lines=item['reported_skips']))
        rows.append(row)
    complete = all(row['qualified'] for row in rows) and not any(job['active'] for job in jobs)
    summary = dict(created=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='qualified' if complete else 'pending', index=partition['index'], index_sha256=digest(partition['index']),
        counts=dict(total=len(rows), qualified=sum(r['qualified'] for r in rows),
                    reused=sum(r.get('reused',False) for r in rows), fresh=sum(r['qualified'] and not r.get('reused',False) for r in rows)),
        jobs=jobs, stages=rows, explicit_optional_exit77=exit77, output_skip_markers=markers,
        marker_limitation='Raw runner matches broad SKIP words, including incidental CMake compiler-probe skipped text. Output markers are not evidence of an exit77 capability gap.',
        cancelled_job=dict(id='1011368', qualified_stages=0, reason='Cancelled before execution for known invalid legacy fixtures; preserved submission/cancellation evidence.'),
        prior_failed_run=dict(jobid='1011366', qualification='Only exact passed stage+commit rows reused; failed migration/obsolete revisions remain failed and preserved.'))
    (ROOT/'release-validation-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(dict(status=summary['status'],counts=summary['counts'],jobs=jobs,explicit_exit77=len(exit77),output_marker_steps=len(markers))))


if __name__=='__main__':
    main()
