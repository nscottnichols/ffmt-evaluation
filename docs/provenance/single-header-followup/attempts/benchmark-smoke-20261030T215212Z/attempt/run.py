#!/usr/bin/env python3
import datetime,hashlib,json,os,pathlib,shlex,subprocess,time
HERE=pathlib.Path(__file__).resolve().parent
assert os.environ.get('COBALT_JOBID')=='1012529'
assert os.uname().nodename.split('.')[0]=='cpl00'
workspace=HERE.parents[3];source=HERE/'source';fmt=workspace/'ffmt/third_party/fmt';cxx='/soft/compilers/gcc/13.3.0/x86_64-suse-linux/bin/g++'
report={'job_id':'1012529','hostname':os.uname().nodename,'source_revision':subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),'fmt_revision':subprocess.check_output(['git','-C',str(fmt),'rev-parse','HEAD'],text=True).strip(),'scope':'Relocation and linkage smoke, verification mode only, one batch per process. No performance campaign or timing comparison.','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'steps':[],'comparisons':[]}
report['source_sha256']={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in list((source/'benchmarks').glob('*'))+[source/'include/ffmt/base.hpp'] if p.is_file()}
def step(name,args):
 record={'name':name,'argv':list(map(str,args)),'command':shlex.join(list(map(str,args))),'cwd':str(source)};start=time.time()
 with (HERE/(name+'.stdout')).open('wb') as out,(HERE/(name+'.stderr')).open('wb') as err:
  try:process=subprocess.run(record['argv'],cwd=source,env=os.environ,stdout=out,stderr=err,timeout=300);record.update(exit_code=process.returncode,status='pass' if process.returncode==0 else 'failure')
  except Exception as error:record.update(status='infrastructure_failure',error=repr(error))
 record['seconds']=round(time.time()-start,3);report['steps'].append(record);(HERE/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(name,record['status'],flush=True);return record
flags=['-std=c++20','-O2','-fno-fast-math','-Wall','-Iinclude','-isystem',fmt/'include']
step('compiler-version',[cxx,'--version'])
assert step('compile-fmt',[cxx,*flags,'-c',fmt/'src/format.cc','-o',HERE/'fmt.o'])['status']=='pass'
for reference in [False,True]:
 for multi in [False,True]:
  name=('reference' if reference else 'library')+('-multi' if multi else '-single');args=[cxx,*flags]
  if reference:args+=['-DBENCH_REFERENCE=1']
  if multi:args+=['-DBENCH_MULTI_TU=1']
  args+=['benchmarks/benchmark.cpp']
  if multi:args+=['benchmarks/benchmark_extra.cpp']
  if reference:args+=[HERE/'fmt.o']
  args+=['-o',HERE/name];assert step('compile-'+name,args)['status']=='pass'
step('compile-resource',[cxx,*flags,'-c','benchmarks/benchmark_resource.cpp','-o',HERE/'resource.o'])
for multi in [False,True]:
 for floating in [0,1]:
  for printing in [0,1]:
   for native in ([0,1] if printing else [0]):
    suffix=('multi' if multi else 'single')+'-f'+str(floating)+'-p'+str(printing)+'-n'+str(native);args=[str(floating),str(printing),str(native),'2' if multi else '1','2','1']
    for implementation in ['library','reference']:
     binary=implementation+('-multi' if multi else '-single');step(implementation+'-'+suffix,[HERE/binary,*args])
    actual=(HERE/('library-'+suffix+'.stdout')).read_bytes();expected=(HERE/('reference-'+suffix+'.stdout')).read_bytes();report['comparisons'].append({'case':suffix,'equal':actual==expected,'bytes':len(actual),'sha256':hashlib.sha256(actual).hexdigest()})
report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['status']='pass' if all(x['status']=='pass' for x in report['steps']) and all(x['equal'] for x in report['comparisons']) else 'failure';(HERE/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['status']=='pass' else 1)
