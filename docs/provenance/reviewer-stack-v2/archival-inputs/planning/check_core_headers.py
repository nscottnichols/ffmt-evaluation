from pathlib import Path
import json,subprocess,shutil
root=Path('/vast/projects/datascience/nnichols/ffmt_project/ffmt/artifacts/reviewer-v2/core-stages')
target=root.parent/'core-header-check'; stages=json.loads((root/'index.json').read_text()); metadata={s:json.loads((root/s/'stage.json').read_text()) for s in stages}
def ancestors(stage):
 result={stage}
 for parent in metadata[stage]['dependencies']:
  if parent in metadata: result.update(ancestors(parent))
 return result
rows=[]
for stage in stages:
 shutil.rmtree(target,ignore_errors=True); target.mkdir()
 scope=ancestors(stage)
 for dependency in stages:
  if dependency not in scope: continue
  base=root/dependency/'files'
  for source in base.rglob('*'):
   if source.is_file():
    p=target/source.relative_to(base); p.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(source,p)
  for p in metadata[dependency]['remove']: (target/p).unlink(missing_ok=True)
 entry={'core-prepare':'ffmt/base.hpp','checked-config':'ffmt/detail/config.hpp'}.get(stage,'ffmt/detail/checked.hpp')
 command=['/soft/compilers/gcc/13.3.0/x86_64-suse-linux/bin/g++','-std=c++20','-I'+str(target/'include'),'-x','c++','-fsyntax-only','-']
 result=subprocess.run(command,input='#include <'+entry+'>\nint main() {}\n',text=True,capture_output=True)
 rows.append({'stage':stage,'dependencies':metadata[stage]['dependencies'],'entry':entry,'command':command,'exit_code':result.returncode,'stderr':result.stderr}); print(stage,result.returncode,flush=True)
 if result.returncode: print(result.stderr)
(root/'header-check.json').write_text(json.dumps(rows,indent=2)+'\n')
