#!/usr/bin/env python3
import concurrent.futures,datetime,hashlib,json,os,pathlib,shlex,subprocess,time
HERE=pathlib.Path(__file__).resolve().parent
CXX='/soft/compilers/rocm/rocm-7.0.2/bin/hipcc'
GCC='/soft/compilers/gcc/13.3.0/x86_64-suse-linux'
assert os.environ.get('COBALT_JOBID')
env=os.environ.copy();env['HIP_PLATFORM']='amd';env['ROCM_PATH']='/soft/compilers/rocm/rocm-7.0.2';env['HIP_PATH']=env['ROCM_PATH'];env['HIP_CLANG_PATH']=env['ROCM_PATH']+'/llvm/bin';env['LD_LIBRARY_PATH']=env['ROCM_PATH']+'/lib:'+env['ROCM_PATH']+'/llvm/lib:'+env.get('LD_LIBRARY_PATH','')
report={'job_id':os.environ['COBALT_JOBID'],'hostname':os.uname().nodename,'compiler':CXX,'baseline_revision':'471627c31cd1e09a2d4587c0369ec662251f7356','final_revision':'f3170f07df7774fb086849b077422e3330166aec','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Controlled compile-only differential; identical runtime-first probe, compiler, architecture and optimization. No device execution.','steps':[]}
report['source_sha256']={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'probe.cpp',HERE/'printf-only.cpp',*list((HERE/'baseline/include').rglob('*.hpp')),*list((HERE/'final').rglob('*.hpp'))]}
def run(name,argv):
 start=time.time();record={'name':name,'argv':list(map(str,argv)),'command':shlex.join(list(map(str,argv))),'cwd':str(HERE),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  with (HERE/(name+'.stdout')).open('wb') as out,(HERE/(name+'.stderr')).open('wb') as err:
   process=subprocess.run(record['argv'],cwd=HERE,env=env,stdout=out,stderr=err,timeout=600)
  record.update(exit_code=process.returncode,status='pass' if process.returncode==0 else 'failure')
 except Exception as error:record.update(status='infrastructure_failure',error=repr(error))
 record['seconds']=round(time.time()-start,3);(HERE/(name+'.json')).write_text(json.dumps(record,indent=2)+'\n');print(name,record['status'],flush=True);return record
report['steps'].append(run('compiler-version',[CXX,'--version']))
tasks=[]
for architecture in ['gfx90a','gfx942']:
 for optimization in ['O0','O2']:
  for version,include in [('baseline',HERE/'baseline/include'),('final',HERE/'final')]:
   name=version+'-'+architecture+'-'+optimization
   args=[CXX,'-std=c++20','-'+optimization,'-fno-fast-math','--gcc-toolchain='+GCC,'--offload-arch='+architecture,'-x','hip','-I'+str(include),'-c',HERE/'probe.cpp','-o',HERE/(name+'.o')]
   tasks.append((name,args))
  name='printf-only-'+architecture+'-'+optimization;tasks.append((name,[CXX,'-std=c++20','-'+optimization,'--gcc-toolchain='+GCC,'--offload-arch='+architecture,'-x','hip','-c',HERE/'printf-only.cpp','-o',HERE/(name+'.o')]))
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
 futures=[executor.submit(run,name,args) for name,args in tasks]
 for future in concurrent.futures.as_completed(futures):
  report['steps'].append(future.result());(HERE/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['status']='complete';(HERE/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
