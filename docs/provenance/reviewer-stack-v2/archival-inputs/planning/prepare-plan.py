#!/usr/bin/env python3
import argparse,json,shlex
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--foundation-only',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parent
stages={}
for group in ('tool-stages','core-stages','feature-stages','root-stages'):
 for path in sorted((root/group).glob('*/stage.json')):
  s=json.loads(path.read_text());s['directory']=str(path.parent);stages[s['id']]=s
stages['coverage-metrics']['dependencies']=['build-registration']
stages['core-prepare']['dependencies']=['build-registration']
stages['tool-process']['dependencies']=['build-registration']
# A feature's portable fixture is qualified with its implementation.
for name in ('named-arguments','ranges','chrono','standard-types','styling','typed-printf'):
 s=stages[name]
 s['tests']=[['python3','tools/conformance.py','--route','host-buffer','--opt','2','--no-memory','--no-negative']]
# Existing entry points remain executable while the replacement is internal.
for name in ('core-prepare','checked-config','obsolete-deletion'):
 stages[name]['tests']=[['make','-j2','test-host','CXX={cxx}','FMT_DIR={fmt_dir}','HOST_OPT=-O0','EXTRA_CXXFLAGS=-fsanitize=address,undefined -fno-omit-frame-pointer']]

# Validate build integration on its own intermediate tree, with no shell parsing.
if 'cmake-package' in stages:
 stages['cmake-package']['tests']=[
 ['cmake','-S','.','-B','{output}/package','-DCMAKE_CXX_COMPILER={cxx}','-DCMAKE_INSTALL_PREFIX={output}/install','-DCMAKE_DISABLE_FIND_PACKAGE_Python3=ON','-DFFMT_FMT_DIR=/unavailable'],
 ['cmake','--install','{output}/package'],
 ['cmake','-S','examples/cmake-consumer','-B','{output}/consumer','-DCMAKE_CXX_COMPILER={cxx}','-DCMAKE_PREFIX_PATH={output}/install'],
 ['cmake','--build','{output}/consumer','-j2'],
 ['{output}/consumer/ffmt_consumer']]
if 'cmake-tests' in stages:
 stages['cmake-tests']['tests']=[
 ['cmake','-S','.','-B','{output}/cmake','-DFFMT_BUILD_TESTS=ON','-DFFMT_BUILD_CXX23_TESTS=ON','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_COMPILER={cxx}','-DFFMT_FMT_DIR={fmt_dir}'],
 ['cmake','--build','{output}/cmake','-j2'],
 ['ctest','--test-dir','{output}/cmake','--output-on-failure','--no-tests=error','-j2']]
if 'ci-sanitizers' in stages:
 stages['ci-sanitizers']['tests']=[['make','-j2','CXX={cxx}','FMT_DIR={fmt_dir}','HOST_OPT=-O0','EXTRA_CXXFLAGS=-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer','test-host','test-capabilities','conformance-harness','test-negative']]
if 'ci-conformance' in stages:
 stages['ci-conformance']['tests']=[['python3','-m','unittest','discover','-s','test/conformance','-p','test_*.py'],['python3','tools/conformance.py','--route','host-buffer','--route','host-specifiers','--opt','2','--host-cxx','{cxx}','--fmt-dir','{fmt_dir}']]
if 'api-index' in stages:
 stages['api-index']['tests']=[['python3','{repo}/../ffmt-evaluation/tools/review_stack/check_links.py','{source}']]
first=['ci-review-waves','ci-resource-bounds','oracle-pin','build-registration','coverage-metrics','coverage-policy','tool-process','tool-negative','tool-host-oracle']
if a.foundation_only:
 selected=first
else:
 selected=first+[x for x in stages if x not in first and x!='tool-engine-cases']
for name in selected:
 s=stages[name]
 wave_groups=[
  ['ci-review-waves','ci-resource-bounds','oracle-pin','build-registration'],
  ['coverage-metrics','coverage-policy','core-prepare','checked-config','accounting','local-ignores','build-header-dependencies','build-compiler-selection'],
  ['parsing','primitives','tool-process','tool-negative','tool-host-oracle'],
  ['conversion-preparation','floating-conversion','floating-formatting','extended-integers','extended-floats','unicode'],
  ['formatter-compatibility','format-as','legacy-compatibility','transport','tool-snapshots','tool-isolation','tool-oracle-negatives'],
  ['migration','obsolete-deletion'],
  ['named-arguments','enum-helpers','shared-family','cmake-package','ci-sanitizers','reproducer-relocation','backend-regression-selection'],
  ['ranges','chrono','standard-types','styling','typed-printf'],
  ['std23','feature-integration'],
  ['tool-adapter-support','tool-cuda','tool-hip','tool-sycl','tool-openmp','tool-kokkos'],
  ['tool-numeric-memory','tool-memory-cuda','tool-memory-hip','tool-memory-sycl','tool-memory-openmp','tool-memory-kokkos'],
  ['benchmark-primitives','benchmark-driver','benchmark-resources'],
  ['cmake-tests','ci-conformance','api-index'],['complete']]
 s['wave']=next(i for i,names in enumerate(wave_groups,1) if name in names)
 tests=s.get('tests',[]);tests=tests.get('commands',[]) if isinstance(tests,dict) else tests
 if name=='migration':tests += [['make','-j2','test-fast-math','CXX={cxx}','FMT_DIR={fmt_dir}']]
 if name=='oracle-pin':tests=["python3 -m unittest discover -s test/conformance -p test_oracle_pin.py"]+tests
 if name=='coverage-metrics':tests=["python3 -m unittest discover -s test/conformance -p test_coverage_metrics.py",['make','-j2','CXX={cxx}','FMT_DIR={fmt_dir}','HOST_OPT=-O0','coverage']]
 if name=='tool-negative':tests+= [['make','-j2','test-negative','CXX={cxx}','FMT_DIR={fmt_dir}']]
 commands=[]
 for value in tests:
  if isinstance(value,list):command=value
  elif isinstance(value,str) and value.startswith('python3 '):command=shlex.split(value)
  else:continue
  if len(command)>1 and command[1] in ('tools/conformance.py','tools/benchmark.py'):
   if '--fmt-dir' in command:command[command.index('--fmt-dir')+1]='{fmt_dir}'
   else:command+=['--fmt-dir','{fmt_dir}']
   if '--host-cxx' not in command and command[1]=='tools/conformance.py':command+=['--host-cxx','{cxx}']
  commands.append(command)
 s['tests']=commands
out=dict(schema_version=2,base_commit='3fe258a87675c997667c899c2b0f0cad405aad5a',original_commit='aeff043614725d58d383c8add086f548d77d05eb',stages=[stages[x] for x in selected])
(root/'plan.json').write_text(json.dumps(out,indent=2)+'\n')
print('Prepared',len(selected),'stages')
