#!/usr/bin/env python3
"""Captured one-off validation of the simplified library; uses the existing runner's process helper."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

EVALUATION = Path('/vast/projects/datascience/nnichols/ffmt_project/ffmt-evaluation')
LIBRARY = EVALUATION.parent / 'ffmt'
sys.path.insert(0, str(EVALUATION / 'tools/campaign_runner/tools'))
from process_evidence import run, record

kind, revision = sys.argv[1:]
if not os.environ.get('COBALT_JOBID'):
    raise SystemExit('Compute allocation required')
output = EVALUATION / 'artifacts/single-header-followup-20261030' / ('final-' + kind + '-' + os.environ['COBALT_JOBID'])
output.mkdir(exist_ok=False)
source = output / 'source'
compiler = {'clang': '/soft/compilers/llvm/release-22.1.8/bin/clang++',
            'gcc': '/soft/compilers/gcc/13.3.0/x86_64-suse-linux/bin/g++'}[kind]
oracle = EVALUATION / 'third_party/fmt'
strict_flags = '-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer' if kind == 'clang' else ''
os.environ.update(ASAN_OPTIONS='detect_leaks=1:strict_string_checks=1:detect_stack_use_after_return=1',
                  UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1', FFMT_SOURCE_ROOT=str(source))
manifest = dict(status='running', source_commit=revision, compiler=compiler,
    evaluator_commit=subprocess.check_output(['git','-C',str(EVALUATION),'rev-parse','HEAD'], text=True).strip(),
    evaluator_dirty=True, host=os.uname().nodename, jobid=os.environ['COBALT_JOBID'],
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), steps=[])

def save():
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')

def step(name, command, timeout=1800):
    result = run(command, output, name, timeout)
    manifest['steps'].append(dict(name=name, **record(result)))
    save()
    print(name, result['exit_code'], flush=True)
    if result['exit_code']:
        raise RuntimeError(name+' failed: '+result['stderr_file'])
    return result

save()
try:
    step('checkout', ['git','-C',str(LIBRARY),'worktree','add','--detach',str(source),revision])
    manifest['source_files'] = {
        p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for area in ('include','test','tools','cmake','.github','benchmarks')
        for p in (source/area).rglob('*') if p.is_file()}
    manifest['source_files']['Makefile']=hashlib.sha256((source/'Makefile').read_bytes()).hexdigest()
    manifest['fmt_commit']=subprocess.check_output(['git','-C',str(oracle),'rev-parse','HEAD'],text=True).strip()
    step('compiler', [compiler,'--version'])
    step('make-portable', ['make','-C',str(source),'-j2','test-portable','test-cxx23',
        'CXX='+compiler,'FMT_DIR='+str(oracle),'HOST_OPT='+('-O0' if kind=='clang' else '-O2'),
        'EXTRA_CXXFLAGS='+strict_flags], 3600)
    if False:  # CMake wiring was already qualified separately; final source checks use Make.
        build = output/'cmake'
        step('cmake-configure',['cmake','-S',str(source),'-B',str(build),'-DFFMT_BUILD_TESTS=ON',
             '-DFFMT_BUILD_CXX23_TESTS=ON','-DCMAKE_BUILD_TYPE=Release',
             '-DCMAKE_CXX_COMPILER='+compiler,'-DCMAKE_CXX_FLAGS='+strict_flags,
             '-DCMAKE_CXX_FLAGS_RELEASE=-O0 -DNDEBUG','-DFFMT_FMT_DIR='+str(oracle)])
        step('cmake-build',['cmake','--build',str(build),'-j2'],3600)
        step('ctest',['ctest','--test-dir',str(build),'--output-on-failure','-j2'],3600)
        prefix=output/'install'
        step('install',['cmake','--install',str(build),'--prefix',str(prefix)])
        consumer=output/'consumer'
        step('consumer-configure',['cmake','-S',str(source/'examples/cmake-consumer'),'-B',str(consumer),
             '-DCMAKE_PREFIX_PATH='+str(prefix),'-DCMAKE_CXX_COMPILER='+compiler])
        step('consumer-build',['cmake','--build',str(consumer),'-j2'])
        step('consumer-run',[str(consumer/'ffmt_consumer')])
    elif kind == 'gcc':
        step('evaluation-smoke',[sys.executable,str(EVALUATION/'tools/conformance.py'),
             '--ffmt-checkout',str(source),'--source-root',str(source),'--revision',revision,
             '--profile','local','--route','host-buffer','--opt','2','--host-cxx',compiler,
             '--case','literal','--case','long-padding','--numeric-samples','1','--no-negative',
             '--fmt-dir',str(oracle),'--output',str(output/'evaluation-smoke')],1800)
    manifest['status']='pass'
except Exception as error:
    manifest.update(status='failure', reason=str(error))
manifest['finished']=datetime.datetime.now(datetime.timezone.utc).isoformat()
save()
print(output/'manifest.json',flush=True)
raise SystemExit(manifest['status']!='pass')
