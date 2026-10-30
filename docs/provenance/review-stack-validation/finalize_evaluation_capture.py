#!/usr/bin/env python3
"""Preserve finalized stack attempts and bundle original logs losslessly."""
from pathlib import Path
import gzip
import hashlib
import io
import json
import shutil
import tarfile

LIBRARY = Path(__file__).resolve().parents[2]
EVALUATION = LIBRARY.parent / 'ffmt-evaluation'
INPUT = LIBRARY / 'artifacts/review-stack'
DEST = EVALUATION / 'docs/provenance/review-stack-validation'
FOLLOWUP = INPUT / 'consumer-validation-1011212'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy(original, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    before = digest(original)
    shutil.copyfile(original, destination)
    assert digest(original) == digest(destination) == before
    return dict(original_path=str(original), evaluation_path=destination.relative_to(EVALUATION).as_posix(),
                sha256=before, bytes=destination.stat().st_size)


def main():
    original_manifest = json.loads((DEST / 'manifest.json').read_text())
    followup_manifest = json.loads((FOLLOWUP / 'manifest.json').read_text())
    assert original_manifest['status'] == 'failure'
    assert followup_manifest['status'] == 'pass'
    assert followup_manifest['original_attempt']['sha256'] == digest(DEST / 'manifest.json')
    assert followup_manifest['source_commit'] == original_manifest['final_commit']
    assert followup_manifest['source_tree'] == original_manifest['final_tree'] == original_manifest['original_tree']
    assert len(followup_manifest['installed_headers']) == 17
    assert all(item['matches'] for item in followup_manifest['installed_headers'].values())

    inventory_file = DEST / 'captured-files.json'
    inventory = json.loads(inventory_file.read_text())
    archive_path = DEST / 'raw-logs.tar.gz'
    bundled = []
    with archive_path.open('wb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w') as archive:
                for item in inventory['files']:
                    relative = Path(item['evaluation_path']).relative_to(DEST.relative_to(EVALUATION))
                    if relative.parts[0] != 'logs':
                        continue
                    path = EVALUATION / item['evaluation_path']
                    data = path.read_bytes()
                    assert hashlib.sha256(data).hexdigest() == item['sha256']
                    entry = tarfile.TarInfo(relative.as_posix())
                    entry.size, entry.mode, entry.mtime = len(data), 0o644, 0
                    archive.addfile(entry, io.BytesIO(data))
                    bundled.append((item, relative.as_posix()))
    with tarfile.open(archive_path, 'r:gz') as archive:
        assert set(archive.getnames()) == {name for _, name in bundled}
        for item, name in bundled:
            data = archive.extractfile(name).read()
            assert len(data) == item['bytes']
            assert hashlib.sha256(data).hexdigest() == item['sha256']
    archive_relative = archive_path.relative_to(EVALUATION).as_posix()
    for item, name in bundled:
        del item['evaluation_path']
        item.update(archive_path=archive_relative, archive_member=name)
    inventory['archive'] = dict(evaluation_path=archive_relative, sha256=digest(archive_path),
        bytes=archive_path.stat().st_size, members=len(bundled),
        scope='Lossless original command logs and child manifests; file hashes refer to decompressed member bytes.')
    for suffix in ('cobaltlog', 'output', 'error'):
        inventory['files'].append(copy(Path('/home/nnichols/1011211.' + suffix), DEST / 'scheduler' / ('1011211.' + suffix)))
    inventory_file.write_text(json.dumps(inventory, indent=2) + '\n')
    shutil.rmtree(DEST / 'logs')

    followup_dest = DEST / 'consumer-followup'
    preserved = [copy(FOLLOWUP / 'manifest.json', followup_dest / 'manifest.json'),
                 copy(INPUT / 'consumer-submission-1011212.json', followup_dest / 'submission.json')]
    for name in ('consumer.py', 'consumer.sh'):
        preserved.append(copy(INPUT / name, followup_dest / name))
    for name, item in followup_manifest['consumer_sources'].items():
        preserved.append(copy(Path(item['path']), followup_dest / 'consumer' / name))
    for step in followup_manifest['steps']:
        for stream in ('stdout', 'stderr'):
            path = Path(step[stream + '_file'])
            assert digest(path) == step[stream + '_sha256']
            preserved.append(copy(path, followup_dest / path.name))
    for suffix in ('cobaltlog', 'output', 'error'):
        preserved.append(copy(Path('/home/nnichols/1011212.' + suffix), followup_dest / 'scheduler' / ('1011212.' + suffix)))
    followup_inventory = followup_dest / 'captured-files.json'
    followup_inventory.write_text(json.dumps(dict(schema_version=1, original_directory=str(FOLLOWUP),
        manifest_sha256=digest(FOLLOWUP / 'manifest.json'), files=preserved), indent=2) + '\n')
    print(json.dumps(dict(original_status=original_manifest['status'], consumer_followup=followup_manifest['status'],
        archive_sha256=digest(archive_path), archive_bytes=archive_path.stat().st_size,
        archive_members=len(bundled), original_preserved_files=len(inventory['files']),
        consumer_preserved_files=len(preserved)), indent=2))


if __name__ == '__main__':
    main()
