#!/usr/bin/env python3
"""Submit selected immutable review stages, reusing exact qualified commits."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('index', type=Path)
    parser.add_argument('--validated-manifest', action='append', type=Path, default=[])
    parser.add_argument('--pending-index', action='append', type=Path, default=[])
    parser.add_argument('--stage', action='append', help='Select this stage explicitly; repeatable')
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--evaluation', type=Path, required=True)
    parser.add_argument('--walltime', type=int, default=240)
    parser.add_argument('--queue', default='rome_7742')
    parser.add_argument('--label', default='remaining')
    args = parser.parse_args()
    repository, evaluation = args.repo.resolve(), args.evaluation.resolve()
    index_path = args.index.resolve()
    index = json.loads(index_path.read_text())
    qualified = {}
    records = []
    for path in args.validated_manifest:
        path = path.resolve()
        manifest = json.loads(path.read_text())
        records.append(dict(path=str(path), sha256=digest(path), status=manifest['status']))
        for stage in manifest['stages']:
            if stage['status'] in ('pass', 'pass_with_skips'):
                qualified[(stage['id'], stage['commit'])] = dict(manifest=str(path), status=stage['status'])
    pending = {}
    pending_records = []
    for path in args.pending_index:
        path = path.resolve()
        previous = json.loads(path.read_text())
        pending_records.append(dict(path=str(path), sha256=digest(path)))
        for stage in previous['stages']:
            pending[(stage['id'], stage['commit'])] = str(path)
    known = {stage['id'] for stage in index['stages']}
    if args.stage and set(args.stage) - known:
        parser.error('unknown selected stage IDs: ' + ', '.join(sorted(set(args.stage) - known)))
    selected, reused, pending_validation, not_selected = [], [], [], []
    for stage in index['stages']:
        key = (stage['id'], stage['commit'])
        if key in qualified:
            reused.append(dict(id=stage['id'], commit=stage['commit'], **qualified[key]))
        elif key in pending and (not args.stage or stage['id'] not in args.stage):
            pending_validation.append(dict(id=stage['id'], commit=stage['commit'],
                index=pending[key], reason='Exact commit is in a prior submitted run; qualification remains pending'))
        elif args.stage and stage['id'] not in args.stage:
            not_selected.append(dict(id=stage['id'], commit=stage['commit'], reason='Outside explicit stage selection'))
        else:
            selected.append(stage['id'])
    if not selected:
        parser.error('every indexed stage already has matching qualified validation')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    workspace = repository / 'artifacts/reviewer-v2'
    capture = workspace / 'submissions' / (args.label + '-' + stamp)
    capture.mkdir(parents=True, exist_ok=False)
    immutable_index = capture / 'assembly-index.json'
    immutable_index.write_bytes(index_path.read_bytes())
    output = workspace / ('validation-' + args.label + '-' + stamp)
    tools = evaluation / 'tools/review_stack'
    wrapper, runner = tools / 'validate-cobalt.sh', tools / 'validate.py'
    shutil.copy2(Path(__file__), capture / Path(__file__).name)
    for source in (wrapper, runner):
        shutil.copy2(source, capture / source.name)
    preflight_command = [sys.executable, str(runner), str(immutable_index),
                         '--repo', str(repository), '--preflight']
    preflight = subprocess.run(preflight_command, capture_output=True)
    (capture / 'preflight.stdout').write_bytes(preflight.stdout)
    (capture / 'preflight.stderr').write_bytes(preflight.stderr)
    metadata = dict(started=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    source_index=str(index_path), index=str(immutable_index),
                    index_sha256=digest(immutable_index), validated_manifests=records,
                    selected_stages=selected, reused_validation=reused,
                    pending_indices=pending_records, pending_validation=pending_validation, not_selected=not_selected,
                    output=str(output), runner_sha256=digest(runner), wrapper_sha256=digest(wrapper),
                    preflight=dict(command=preflight_command, exit_code=preflight.returncode,
                                   stdout_sha256=digest(capture/'preflight.stdout'),
                                   stderr_sha256=digest(capture/'preflight.stderr')),
                    purpose='CPU-only immutable review intermediates; no GPU campaigns')
    record_path = capture / 'submission.json'
    record_path.write_text(json.dumps(metadata, indent=2)+'\n')
    if preflight.returncode:
        print(preflight.stderr.decode(errors='replace'), file=sys.stderr)
        print('Preflight evidence: ' + str(record_path), file=sys.stderr)
        return preflight.returncode
    prefix = Path('/home/nnichols/.cache/ffmt-cobalt') / ('review-' + args.label + '-' + stamp)
    command = ['qsub', '--mode', 'script', '-q', args.queue, '-n', '1', '-t', str(args.walltime),
               '--cwd', '/home/nnichols', '-O', str(prefix), '/bin/bash', str(wrapper),
               str(immutable_index), '--repo', str(repository),
               '--fmt-dir', str((repository/'third_party/fmt').resolve()), '--output', str(output)]
    for stage in selected:
        command += ['--stage', stage]
    metadata.update(command=command, cobalt_output_prefix=str(prefix))
    record_path.write_text(json.dumps(metadata, indent=2)+'\n')
    result = subprocess.run(command, capture_output=True)
    for name, data in (('qsub.stdout', result.stdout), ('qsub.stderr', result.stderr)):
        (capture/name).write_bytes(data)
        metadata[name+'_sha256'] = digest(capture/name)
    metadata.update(returncode=result.returncode, stdout=result.stdout.decode(errors='replace'),
                    stderr=result.stderr.decode(errors='replace'),
                    finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if result.returncode == 0:
        metadata['jobid'] = result.stdout.decode().strip().splitlines()[-1]
    record_path.write_text(json.dumps(metadata, indent=2)+'\n')
    print(json.dumps(dict(jobid=metadata.get('jobid'), returncode=result.returncode,
                         submission=str(record_path), output=str(output),
                         selected_count=len(selected), reused_count=len(reused),
                         pending_count=len(pending_validation), not_selected_count=len(not_selected))))
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
