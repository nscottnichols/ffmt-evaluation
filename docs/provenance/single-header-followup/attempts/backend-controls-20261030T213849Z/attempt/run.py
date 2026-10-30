#!/usr/bin/env python3
import concurrent.futures,datetime,hashlib,json,os,pathlib,shlex,subprocess,time
HERE=pathlib.Path(__file__).resolve().parent
WORKSPACE=HERE.parents[3]
LIBRARY=WORKSPACE/'ffmt'
EVALUATION=WORKSPACE/'ffmt-evaluation'
FMT=LIBRARY/'third_party/fmt'
REVISION='f3170f07df7774fb086849b077422e3330166aec'
GCC=pathlib.Path('/soft/compilers/gcc/13.3.0/x86_64-suse-linux')
CUDA=pathlib.Path('/soft/compilers/cuda/cuda-12.9.1')
ROCM=pathlib.Path('/soft/compilers/rocm/rocm-7.0.2')
LLVM=pathlib.Path('/soft/compilers/llvm/release-22.1.8')
INTEL=pathlib.Path('/soft/compilers/oneapi/2025.0.0.825/oneapi/compiler/latest')
LOCAL=EVALUATION/'software/chiatta/install/intel-llvm'
ROUTES={
 'cuda-clang':dict(compiler=LLVM/'bin/clang++',arguments=['USE_CUDA_CLANG=1','CUDA_ARCH=sm_80','CUDA_PATH='+str(CUDA),'build/test_main_cuda'],library_paths=[CUDA/'lib64'],extra='--gcc-toolchain='+str(GCC)+' -Wno-error=unknown-cuda-version -Wno-error=unused-command-line-argument'),
 'nvcc':dict(compiler=CUDA/'bin/nvcc',library_paths=[CUDA/'lib64']),
 'hip':dict(compiler=ROCM/'bin/hipcc',arguments=['USE_HIP=1','OFFLOAD_ARCH=gfx90a','compile-hip'],library_paths=[ROCM/'lib',ROCM/'llvm/lib'],extra='--gcc-toolchain='+str(GCC)),
 'intel-sycl':dict(compiler=INTEL/'bin/icpx',arguments=['BACKEND_FLAGS=-fsycl -fsycl-targets=spir64','OPT_LEVELS=O2','build'],library_paths=[INTEL/'lib',INTEL/'opt/compiler/lib'],extra='--gcc-toolchain='+str(GCC)),
 'intel-openmp':dict(compiler=INTEL/'bin/icpx',arguments=['USE_OMP_ICPX=1','OMP_OPT=-O0','build/test_main_omp'],library_paths=[INTEL/'lib',INTEL/'opt/compiler/lib'],extra='--gcc-toolchain='+str(GCC)),
 'llvm-openmp':dict(compiler=LLVM/'bin/clang++',arguments=['USE_OMP_CLANG=1','OFFLOAD_ARCH=sm_80','OMP_OPT=-O0','compile-omp'],library_paths=[LLVM/'lib',CUDA/'lib64'],extra='--gcc-toolchain='+str(GCC)+' --cuda-path='+str(CUDA)+' -Wno-error=unknown-cuda-version -Wno-error=unused-command-line-argument'),
 'local-sycl':dict(compiler=LOCAL/'bin/clang++',arguments=['BACKEND_FLAGS=-fsycl -fsycl-targets=spir64','OPT_LEVELS=O2','build'],library_paths=[LOCAL/'lib',INTEL/'lib',INTEL/'opt/compiler/lib'],extra='--gcc-toolchain='+str(GCC)),
}
ROUTES={name:config for name,config in ROUTES.items() if name in ('nvcc','hip')}
ROUTES['hip']['arguments']=[argument.replace('gfx90a','gfx942') for argument in ROUTES['hip']['arguments']]
ROUTES['hip']['extra']+=' -O0'

def run_step(route,name,argv,cwd,env,timeout=1500):
 directory=HERE/route;directory.mkdir(exist_ok=True)
 start=time.time();record={'name':name,'argv':list(map(str,argv)),'command':shlex.join(list(map(str,argv))),'cwd':str(cwd),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  with (directory/(name+'.stdout')).open('wb') as out,(directory/(name+'.stderr')).open('wb') as err:
   p=subprocess.run(record['argv'],cwd=cwd,env=env,stdout=out,stderr=err,timeout=timeout)
  record['exit_code']=p.returncode;record['status']='pass' if p.returncode==0 else 'failure'
 except (OSError,subprocess.TimeoutExpired) as error:
  record['status']='infrastructure_failure';record['error']=str(error);record['exit_code']=None
 record['seconds']=round(time.time()-start,3)
 for stream in ['stdout','stderr']:
  file=directory/(name+'.'+stream)
  if file.exists():record[stream]={'path':str(file.relative_to(HERE)),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
 (directory/(name+'.json')).write_text(json.dumps(record,indent=2)+'\n')
 print(route,name,record['status'],record['exit_code'],flush=True)
 return record

def route(name,config):
 cwd=HERE/'worktrees'/name;env=os.environ.copy();paths=[str(p) for p in config['library_paths'] if p.exists()]
 env['LD_LIBRARY_PATH']=':'.join(paths+[env.get('LD_LIBRARY_PATH','')]);env['CUDA_PATH']=str(CUDA);env['ROCM_PATH']=str(ROCM);env['HIP_PATH']=str(ROCM)
 env['PATH']=str(config['compiler'].parent)+':'+str(GCC/'bin')+':'+env['PATH'];env['LC_ALL']='C';env['GOMAXPROCS']='2';env['HIP_PLATFORM']='amd';env['HIP_CLANG_PATH']=str(ROCM/'llvm/bin')
 directory=HERE/name;directory.mkdir(exist_ok=True)
 metadata={'source_revision':REVISION,'fmt_revision':subprocess.check_output(['git','-C',str(FMT),'rev-parse','HEAD'],text=True).strip(),'compiler':str(config['compiler']),'compiler_realpath':str(config['compiler'].resolve()),'selected_environment':{k:env[k] for k in ['PATH','LD_LIBRARY_PATH','CUDA_PATH','ROCM_PATH','HIP_PATH','HIP_CLANG_PATH','HIP_PLATFORM']},'steps':[]}
 files=['Makefile']+[str(p.relative_to(cwd)) for folder in ['include','test'] for p in (cwd/folder).rglob('*') if p.is_file()]
 metadata['source_sha256']={file:hashlib.sha256((cwd/file).read_bytes()).hexdigest() for file in files}
 metadata['fmt_source_sha256']={str(p.relative_to(FMT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in list((FMT/'include/fmt').glob('*.h'))+[FMT/'src/format.cc']}
 metadata['steps'].append(run_step(name,'compiler-version',[config['compiler'],'--version'],cwd,env,120))
 if not config['compiler'].exists():
  metadata['status']='unavailable'
 else:
  if name=='nvcc':
   cases=['integers','floats','strings','layout','misc','formatter','buffer_path']
   for case in cases:
    argv=[config['compiler'],'-std=c++20','-arch=sm_80','--extended-lambda','--expt-relaxed-constexpr','-ccbin',GCC/'bin/g++','-Xcompiler=-Wall,-Werror,-fno-fast-math','-Iinclude','-isystem',FMT/'include','-DTEST_NO_MAIN','-O2','-x','cu','-dc','test/test_'+case+'.cpp','-o',directory/(case+'.o')]
    metadata['steps'].append(run_step(name,'compile-'+case,argv,cwd,env,600))
  else:
   argv=['make','--no-print-directory','-j2','CXX='+str(config['compiler']),'FMT_DIR='+str(FMT),'EXTRA_CXXFLAGS='+config.get('extra',''),*config['arguments']]
   metadata['steps'].append(run_step(name,'make-backend',argv,cwd,env))
  isolated=['-I'+str(HERE/'single-header')]
  common=['-std=c++20','-O0','-fno-fast-math']
  compatibility=['-Wno-error=unknown-cuda-version','-Wno-error=unused-command-line-argument']
  toolchain=['--gcc-toolchain='+str(GCC)]
  if name=='nvcc':
   probe=[config['compiler'],'-std=c++20','-O2','-arch=sm_80','--extended-lambda','--expt-relaxed-constexpr','-ccbin',GCC/'bin/g++','-Xcompiler=-fno-fast-math',*isolated,'-x','cu','-dc',HERE/'header-only-gpu.cpp','-o',directory/'header-only.o']
  elif name=='cuda-clang':
   probe=[config['compiler'],*common,*toolchain,*compatibility,*isolated,'-x','cuda','--cuda-path='+str(CUDA),'--cuda-gpu-arch=sm_80','-c',HERE/'header-only-gpu.cpp','-o',directory/'header-only.o']
  elif name=='hip':
   probe=[config['compiler'],*common,*toolchain,*isolated,'-x','hip','--offload-arch=gfx942','-c',HERE/'header-only-gpu.cpp','-o',directory/'header-only.o']
  elif name in ('intel-sycl','local-sycl'):
   probe=[config['compiler'],*common,*toolchain,*isolated,'-fsycl','-fsycl-targets=spir64','-c',HERE/'header-only-sycl.cpp','-o',directory/'header-only.o']
  elif name=='intel-openmp':
   probe=[config['compiler'],*common,*toolchain,*isolated,'-fiopenmp','-fopenmp-targets=spir64','-c',HERE/'header-only-openmp.cpp','-o',directory/'header-only.o']
  else:
   probe=[config['compiler'],*common,*toolchain,*compatibility,*isolated,'--cuda-path='+str(CUDA),'-fopenmp','--offload-arch=sm_80','-foffload-lto','-c',HERE/'header-only-openmp.cpp','-o',directory/'header-only.o']
  metadata['steps'].append(run_step(name,'header-only-device-consumer',probe,cwd,env,600))
  metadata['status']='pass' if all(x['status']=='pass' for x in metadata['steps']) else 'failure'
 (directory/'manifest.json').write_text(json.dumps(metadata,indent=2)+'\n')
 return {'route':name,'status':metadata['status'],'manifest':str((directory/'manifest.json').relative_to(HERE))}

def main():
 assert os.environ.get('COBALT_JOBID'),'Backend compilation requires allocation'
 assert subprocess.check_output(['git','-C',str(FMT),'rev-parse','HEAD'],text=True).strip()=='0fc31633e7d53ac895ae0a688b83b7d44f0b0c1f'
 report={'source_revision':REVISION,'fmt_revision':'0fc31633e7d53ac895ae0a688b83b7d44f0b0c1f','job_id':os.environ['COBALT_JOBID'],'hostname':os.uname().nodename,'machine':os.uname().machine,'routes':[],'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Compilation/link only. No accelerator execution. This control attempt forces CUDA language for NVCC and tests HIP at -O0 for gfx942. Neither command executes accelerator code.'}
 (HERE/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  tasks={pool.submit(route,name,config):name for name,config in ROUTES.items()}
  for task in concurrent.futures.as_completed(tasks):
   try:report['routes'].append(task.result())
   except Exception as error:report['routes'].append({'route':tasks[task],'status':'orchestrator_failure','error':repr(error)})
   (HERE/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['status']='pass' if all(x['status']=='pass' for x in report['routes']) else 'failure'
 (HERE/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
