from pathlib import Path
import json,subprocess
root=Path(__file__).resolve().parent
base=(root/'root-stages/build-registration/files/Makefile').read_text()

def export(name,title,files,problem,example,design,tradeoffs,reading,tests,dependencies=None):
 d=root/'root-stages'/name;(d/'files').mkdir(parents=True,exist_ok=True)
 for path,text in files.items():
  p=d/'files'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 data=dict(id=name,title=title,dependencies=dependencies or ['build-registration'],change_kind='build-integration',remove=[],tests=tests,problem=problem,example=example,design=design,tradeoffs=tradeoffs,reading_order=reading)
 (d/'stage.json').write_text(json.dumps(data,indent=2)+'\n')

export('local-ignores','Keep local outputs and installations untracked',{
 '.gitignore':subprocess.check_output(['git','show','aeff043:.gitignore'],text=True),
 'docs/contributing/LOCAL_OUTPUTS.md':'# Local outputs\n\nBuild products, portable-runner artifacts, Python caches, profiles and optional local software installations stay untracked. Ignoring these paths preserves existing files; it does not move or delete them. Site provisioning and campaigns belong to the companion evaluation repository.\n'},
 'Portable runner output, profile data and local installations must not be added accidentally when editing the library.',
 'python3 tools/conformance.py ... # artifacts/ stays untracked',
 'Restore the narrow directory and suffix ignores from the retained library snapshot.',
 'Ignored output must be captured deliberately by an evaluation workflow when it serves as evidence.',
 ['.gitignore','docs/contributing/LOCAL_OUTPUTS.md'],[])

make=base.replace('DEPS := $(TEST_HDRS) include/ffmt/base.hpp $(FLAGS_STAMP)','FFMT_HDRS := $(wildcard include/ffmt/*.hpp include/ffmt/detail/*.hpp)\nDEPS := $(TEST_HDRS) $(FFMT_HDRS) $(FLAGS_STAMP)')
test='''import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class HeaderDependencies(unittest.TestCase):
    def test_detail_header_edit_rebuilds_existing_host_object(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copyfile(ROOT / 'Makefile', root / 'Makefile')
            shutil.copytree(ROOT / 'mk', root / 'mk')
            inputs = ['test/test_integers.cpp', 'include/ffmt/base.hpp',
                      'include/ffmt/detail/dependency_probe.hpp',
                      'fmt/include/fmt/format.h', 'build/.dir', 'build/.flags']
            for name in inputs:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('// dependency fixture\\n')
                os.utime(path, (1000000000, 1000000000))
            target = root / 'build/test_main_host_specifiers_integers.o'
            target.touch()
            os.utime(target, (1000000200, 1000000200))
            command = ['make', '-n', '-o', 'build/.flags', str(target.relative_to(root)),
                       'CXX=c++', 'FMT_DIR=fmt']
            before = subprocess.check_output(command, cwd=root, text=True)
            self.assertNotIn('-c test/test_integers.cpp', before)
            os.utime(root / 'include/ffmt/detail/dependency_probe.hpp',
                     (1000000300, 1000000300))
            after = subprocess.check_output(command, cwd=root, text=True)
            self.assertIn('-c test/test_integers.cpp', after)


if __name__ == '__main__':
    unittest.main()
'''
export('build-header-dependencies','Rebuild legacy test objects after any library header edit',{
 'Makefile':make,'test/conformance/test_make_header_dependencies.py':test,
 'docs/contributing/HEADER_DEPENDENCIES.md':'# Header dependencies\n\nThe legacy host/device object rules depend on every installed library header. Editing an internal or optional header therefore invalidates a previously built object; the focused suite registry maintains its own corresponding dependency list. The regression uses real Make timestamps and dry-run compile plans without invoking a compiler.\n'},
 'Legacy test rules watched only base.hpp, so changing an internal header could silently rerun a stale binary.',
 'touch include/ffmt/detail/parse.hpp\nmake test-host # recompiles affected objects',
 'Use the complete installed header list in the existing shared prerequisite variable; exercise an unchanged object and a subsequent internal-header edit with real Make timestamp decisions.',
 'This conservative dependency list rebuilds some tests that do not instantiate the edited header, in exchange for reliable incremental checks.',
 ['Makefile:FFMT_HDRS and DEPS','test/conformance/test_make_header_dependencies.py'],
 [['python3','-m','unittest','discover','-s','test/conformance','-p','test_make_header_dependencies.py']])

make=base.replace('  export PATH := $(HOME)/projet/p26.02/install/bin:$(PATH)\n','')
export('build-compiler-selection','Resolve AdaptiveCpp through the caller environment',{
 'Makefile':make,'docs/contributing/COMPILER_SELECTION.md':'# Compiler selection\n\n`USE_ACPP=1` selects `acpp` from the caller PATH. The Makefile does not prepend a developer-specific installation path. Load a compiler environment or set CXX explicitly before building; site provisioning remains in ffmt-evaluation.\n'},
 'The AdaptiveCpp branch prepended a path from a developer machine and could select an unintended installation.',
 'PATH=/my/compiler/bin:$PATH make USE_ACPP=1 compile-omp',
 'Remove the site-specific PATH assignment and retain the existing backend flags and explicit CXX override behavior.',
 'Callers must load or provide their own compiler environment; this check does not claim an AdaptiveCpp runtime result.',
 ['Makefile:USE_ACPP','docs/contributing/COMPILER_SELECTION.md'],[])

make=base.replace('DEVICE_TESTS    := $(TESTS)\n','DEVICE_TESTS    := $(TESTS) $(BUFFER_TESTS)\n').replace('# Test sources are test/test_<name>.cpp. TESTS build on both paths;\n# BUFFER_TESTS use buffer-path-only specs ({:a}, {:b}, {:^}, ...), which the\n# specifiers path rejects at compile time.','# Historical source-compatibility suites. Both FFMT_BUFFER_PATH values now use\n# the same engine; the focused suites are registered independently.')
export('backend-regression-selection','Exercise the migrated buffer cases in Intel backend builds',{
 'Makefile':make,'docs/contributing/INTEL_REGRESSIONS.md':'# Intel regression selection\n\nAfter public engine migration both legacy path spellings accept the same format grammar. Include buffer_path cases in default SYCL and icpx OpenMP builds as already done for other backends. Portable Make inspection establishes source selection; preserved campaign records retain their original execution identities, and new device execution is not inferred.\n'},
 'Intel SYCL and icpx OpenMP build targets still omitted buffer-specific regression cases after both API paths gained the shared engine.',
 'make USE_OMP_ICPX=1 compile-omp # includes test_buffer_path.cpp',
 'Add BUFFER_TESTS to these two source lists only after migration makes their grammar valid.',
 'This increases accelerator compile work and does not establish accelerator runtime qualification.',
 ['Makefile:USE_OMP_ICPX and default SYCL source lists','docs/contributing/INTEL_REGRESSIONS.md'],[],['migration'])
print('Exported four focused build repairs')
