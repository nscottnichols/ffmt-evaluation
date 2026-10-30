#!/usr/bin/env python3
import datetime,hashlib,json,os,pathlib,shlex,subprocess,time
HERE=pathlib.Path(__file__).resolve().parent
assert os.environ.get('COBALT_JOBID')=='1012529'
assert os.uname().nodename.split('.')[0]=='cpl00'
source=HERE/'source';workspace=HERE.parents[3];fmt=workspace/'ffmt/third_party/fmt';compiler='/soft/compilers/rocm/rocm-7.0.2/bin/hipcc'
env=os.environ.copy();env['HIP_PLATFORM']='amd';env['ROCM_PATH']='/soft/compilers/rocm/rocm-7.0.2';env['HIP_PATH']=env['ROCM_PATH'];env['HIP_CLANG_PATH']=env['ROCM_PATH']+'/llvm/bin';env['LD_LIBRARY_PATH']=env['ROCM_PATH']+'/lib:'+env['ROCM_PATH']+'/llvm/lib:'+env.get('LD_LIBRARY_PATH','')
args=['make','--no-print-directory','-j2','CXX='+compiler,'FMT_DIR='+str(fmt),'EXTRA_CXXFLAGS=--gcc-toolchain=/soft/compilers/gcc/13.3.0/x86_64-suse-linux -O2','USE_HIP=1','OFFLOAD_ARCH=gfx942','compile-hip']
report={'job_id':'1012529','hostname':os.uname().nodename,'source_revision':'f3170f07df7774fb086849b077422e3330166aec','fmt_revision':subprocess.check_output(['git','-C',str(fmt),'rev-parse','HEAD'],text=True).strip(),'compiler':compiler,'argv':args,'command':shlex.join(args),'cwd':str(source),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Full original shared HIP cases, compile only, explicit -O2/gfx942; executed inside the verified still-active CPU allocation1012529. No device execution.'}
report['source_sha256']={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['include','test'] for p in (source/folder).rglob('*') if p.is_file()};report['source_sha256']['Makefile']=hashlib.sha256((source/'Makefile').read_bytes()).hexdigest();(HERE/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
start=time.time()
try:
 with (HERE/'make.stdout').open('wb') as out,(HERE/'make.stderr').open('wb') as err:
  process=subprocess.run(args,cwd=source,env=env,stdout=out,stderr=err,timeout=600)
 report.update(exit_code=process.returncode,status='pass' if process.returncode==0 else 'failure')
except Exception as error:report.update(status='infrastructure_failure',error=repr(error))
report['seconds']=round(time.time()-start,3);report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(HERE/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['status']=='pass' else 1)
