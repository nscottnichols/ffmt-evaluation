from pathlib import Path
import json,hashlib,subprocess
ROOT=Path('/vast/projects/datascience/nnichols/ffmt_project/ffmt')
OUT=ROOT/'artifacts/reviewer-v2/root-stages'
EVAL='https://github.com/nscottnichols/ffmt-evaluation'
EVAL_SHA='179e6e59e1a0094ec2e4f56aab11eb568f058055'
FMT='0fc31633e7d53ac895ae0a688b83b7d44f0b0c1f'
INVENTORY=[]
def stage(id,title,dependencies,files,problem,example,design,tradeoffs,reading,commands,remove=(),kind='build-integration',limitations='Portable validation is pending on the assembled commit; root records commands and outcomes before publication.'):
 folder=OUT/id; (folder/'files').mkdir(parents=True,exist_ok=True)
 for p,s in files.items():
  destination=folder/'files'/p; destination.parent.mkdir(parents=True,exist_ok=True); destination.write_text(s)
 docs=[p for p in files if p.startswith('docs/')]
 metadata=dict(id=id,title=title,dependencies=dependencies,change_kind=kind,remove=list(remove),tests=[],docs=docs,problem=problem,example=example,design=design,tradeoffs=tradeoffs,reading_order=reading,validation=dict(commands=commands,results='Pending independent review and assembled portable validation.',limitations=limitations),source_changes='Build integration and documentation only; no formatter implementation changes.')
 (folder/'stage.json').write_text(json.dumps(metadata,indent=2)+'\n'); INVENTORY.append(dict(id=id,files=sorted(files),remove=list(remove)))
PACKAGE=r'''cmake_minimum_required(VERSION 3.20)
project(ffmt LANGUAGES CXX)

include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

add_library(ffmt INTERFACE)
add_library(ffmt::ffmt ALIAS ffmt)
target_compile_features(ffmt INTERFACE cxx_std_20)
target_include_directories(ffmt INTERFACE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)

# Consumers install headers and an interface target; no oracle or test runtime.
install(TARGETS ffmt EXPORT ffmtTargets)
install(DIRECTORY include/ffmt DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
install(FILES NOTICE LICENSES/fmt.txt LICENSES/dragonbox-Boost.txt
  DESTINATION ${CMAKE_INSTALL_DATADIR}/ffmt/licenses)
set(ffmt_config_dir ${CMAKE_INSTALL_LIBDIR}/cmake/ffmt)
configure_package_config_file(cmake/ffmtConfig.cmake.in
  ${CMAKE_CURRENT_BINARY_DIR}/ffmtConfig.cmake
  INSTALL_DESTINATION ${ffmt_config_dir})
install(EXPORT ffmtTargets NAMESPACE ffmt:: DESTINATION ${ffmt_config_dir})
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/ffmtConfig.cmake
  DESTINATION ${ffmt_config_dir})
'''
CONFIG=r'''@PACKAGE_INIT@
include("${CMAKE_CURRENT_LIST_DIR}/ffmtTargets.cmake")
check_required_components(ffmt)
'''
CONSUMER_CMAKE=r'''cmake_minimum_required(VERSION 3.20)
project(ffmt_consumer LANGUAGES CXX)
find_package(ffmt CONFIG REQUIRED)
add_executable(ffmt_consumer main.cpp)
target_link_libraries(ffmt_consumer PRIVATE ffmt::ffmt)
'''
CONSUMER=r'''#include <ffmt/base.hpp>
#include <string_view>

int main() {
  char output[8];
  const auto result = ffmt::format_to_n(output, sizeof output, "{:04x}", 42);
  return result && std::string_view(output, result.written) == "002a" ? 0 : 1;
}
'''
BUILD=r'''# Build and install

ffmt is a C++20 header-only library. Use a C++20-capable compiler; CMake
integration requires CMake 3.20 or newer. Library consumers need neither fmt,
Python nor a GPU runtime for host formatting.

For a source checkout:

```cmake
add_subdirectory(ffmt)
target_link_libraries(my_program PRIVATE ffmt::ffmt)
```

For an installed package:

```sh
cmake -S . -B build/package -DCMAKE_INSTALL_PREFIX="$PWD/build/install"
cmake --install build/package
cmake -S examples/cmake-consumer -B build/consumer -DCMAKE_PREFIX_PATH="$PWD/build/install"
cmake --build build/consumer -j2
./build/consumer/ffmt_consumer
```

The consumer uses `find_package(ffmt CONFIG REQUIRED)` and links `ffmt::ffmt`.
The target supplies include directories and the C++20 language requirement.
Compiler backend flags, runtime linking and kernel launch/synchronization remain
the application's responsibility; see [backend contracts](BACKENDS.md).

The package installs headers, CMake target metadata and third-party notices. It
does not fetch software or discover test dependencies while configuring an
ordinary consumer. Select `CMAKE_INSTALL_INCLUDEDIR` and `CMAKE_INSTALL_LIBDIR`
through standard GNUInstallDirs options when packaging for another layout.
'''
stage('cmake-package','Install a header-only CMake interface target',['obsolete-deletion'],{'CMakeLists.txt':PACKAGE,'cmake/ffmtConfig.cmake.in':CONFIG,'examples/cmake-consumer/CMakeLists.txt':CONSUMER_CMAKE,'examples/cmake-consumer/main.cpp':CONSUMER,'docs/BUILD.md':BUILD},'Applications need a reusable CMake target and an installed package without inheriting oracle or test dependencies.','find_package(ffmt CONFIG REQUIRED)\ntarget_link_libraries(my_program PRIVATE ffmt::ffmt)','An INTERFACE target carries headers and C++20 requirements. Standard package helpers export relocatable target metadata; a small independent consumer checks the installed contract.','The target does not configure accelerator runtimes or backend flags. CMake 3.20 is required; direct header consumers do not need CMake.',['CMakeLists.txt','cmake/ffmtConfig.cmake.in','examples/cmake-consumer/main.cpp','docs/BUILD.md'],['cmake -S . -B build/package -DCMAKE_INSTALL_PREFIX="$PWD/build/install" -DCMAKE_DISABLE_FIND_PACKAGE_Python3=ON -DFFMT_FMT_DIR=/unavailable','cmake --install build/package','cmake -S examples/cmake-consumer -B build/consumer -DCMAKE_PREFIX_PATH="$PWD/build/install"','cmake --build build/consumer -j2 && ./build/consumer/ffmt_consumer'])
# Register exactly the actual decomposed sources, never an existence-filtered list.
SUITES=[
 ('core_accounting','test_core_accounting.cpp'),('core_parsing','test_core_parsing.cpp'),
 ('core_primitives','test_core_primitives.cpp'),('core_conversion','test_core_conversion.cpp'),
 ('core_floating','test_core_floating.cpp'),('core_int128','test_core_int128.cpp'),
 ('engine_bitint','test_engine_bitint.cpp'),('engine_extended','test_engine_extended.cpp'),
 ('engine_quad','test_engine_quad.cpp'),('core_unicode','test_core_unicode.cpp'),
 ('core_formatters','test_core_formatters.cpp'),('core_forwarding','test_core_forwarding.cpp'),
 ('formatter_composition','test_formatter_composition.cpp'),('core_format_as','test_core_format_as.cpp'),
 ('core_legacy','test_core_legacy.cpp'),('legacy_forwarding','test_legacy_forwarding.cpp'),
 ('engine_transport','test_engine_transport.cpp'),('engine_legacy_hook','test_engine_legacy_hook.cpp'),
 ('transport_forwarding','test_transport_forwarding.cpp'),('core_migration','test_core_migration.cpp'),
 ('engine_fast_math','test_engine_fast_math.cpp'),('named_arguments','test_named_arguments.cpp'),
 ('family_support','test_family_support.cpp'),('ranges','test_ranges.cpp'),
 ('ranges_iterators','test_ranges_iterators.cpp'),('ranges_forwarding','test_ranges_forwarding.cpp'),
 ('chrono','test_chrono.cpp'),('std','test_std.cpp'),('style','test_style.cpp'),
 ('enum','test_enum.cpp'),('printf','test_printf.cpp'),('feature_integration','test_feature_integration.cpp')]
TESTS=r'''# Test dependencies are discovered only inside FFMT_BUILD_TESTS.
find_package(Python3 REQUIRED COMPONENTS Interpreter)
find_package(Git REQUIRED)
set(FFMT_FMT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/third_party/fmt" CACHE PATH
  "Clean fmt checkout at the immutable conformance revision")
set(ffmt_fmt_revision "0fc31633e7d53ac895ae0a688b83b7d44f0b0c1f")
execute_process(COMMAND "${GIT_EXECUTABLE}" -C "${FFMT_FMT_DIR}" rev-parse HEAD
  RESULT_VARIABLE ffmt_fmt_git_result OUTPUT_VARIABLE ffmt_fmt_actual
  ERROR_VARIABLE ffmt_fmt_git_error OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT ffmt_fmt_git_result EQUAL 0 OR NOT ffmt_fmt_actual STREQUAL ffmt_fmt_revision)
  message(FATAL_ERROR "FFMT_FMT_DIR must be a clean checkout of ${ffmt_fmt_revision}. Preserve local checkouts and select an existing pinned one. ${ffmt_fmt_git_error}")
endif()
execute_process(COMMAND "${GIT_EXECUTABLE}" -C "${FFMT_FMT_DIR}" status --porcelain
  RESULT_VARIABLE ffmt_fmt_status_result OUTPUT_VARIABLE ffmt_fmt_status
  ERROR_VARIABLE ffmt_fmt_status_error OUTPUT_STRIP_TRAILING_WHITESPACE)
if(NOT ffmt_fmt_status_result EQUAL 0 OR NOT ffmt_fmt_status STREQUAL "")
  message(FATAL_ERROR "The fmt oracle checkout is modified or cannot be inspected. Preserve edits and supply a clean pinned FFMT_FMT_DIR. ${ffmt_fmt_status_error}")
endif()

add_library(ffmt_test_reference STATIC "${FFMT_FMT_DIR}/src/format.cc")
target_include_directories(ffmt_test_reference PUBLIC "${FFMT_FMT_DIR}/include")
target_compile_features(ffmt_test_reference PUBLIC cxx_std_20)
set_target_properties(ffmt_test_reference PROPERTIES CXX_EXTENSIONS OFF)

function(ffmt_add_regression suite source)
  # An absent declared source is a configuration error, not a skipped test.
  add_executable(ffmt_test_${suite} "test/conformance/${source}")
  target_link_libraries(ffmt_test_${suite} PRIVATE ffmt::ffmt ffmt_test_reference)
  set_target_properties(ffmt_test_${suite} PROPERTIES CXX_EXTENSIONS OFF)
  target_compile_options(ffmt_test_${suite} PRIVATE
    $<$<CXX_COMPILER_ID:MSVC>:/UNDEBUG>
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-UNDEBUG>)
  add_test(NAME ffmt.${suite} COMMAND ffmt_test_${suite})
endfunction()

# Core behavior and optional families each retain a visible test entry.
'''
for suite,source in SUITES: TESTS+='ffmt_add_regression('+suite+' '+source+')\n'
TESTS+=r'''
# Exercise the full seeded floating suite through the integer interval path.
ffmt_add_regression(core_floating_portable test_core_floating.cpp)
target_compile_definitions(ffmt_test_core_floating_portable PRIVATE FFMT_PORTABLE_SHORTEST=1)

target_compile_options(ffmt_test_engine_fast_math PRIVATE
  $<$<CXX_COMPILER_ID:MSVC>:/fp:fast>
  $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-ffast-math>)
include(CheckCXXSourceCompiles)
check_cxx_source_compiles("#ifndef __SIZEOF_FLOAT128__\n#error unavailable\n#endif\nint main() { __float128 value = 0; return value != 0; }"
  FFMT_TEST_HAS_FLOAT128)
if(FFMT_TEST_HAS_FLOAT128)
  target_compile_definitions(ffmt_test_engine_quad PRIVATE FMT_USE_FLOAT128=1)
endif()
foreach(suite core_int128 engine_bitint engine_quad)
  set_tests_properties(ffmt.${suite} PROPERTIES SKIP_RETURN_CODE 77)
endforeach()
if(FFMT_BUILD_CXX23_TESTS)
  ffmt_add_regression(std23 test_std23.cpp)
  target_compile_features(ffmt_test_std23 PRIVATE cxx_std_23)
  set_tests_properties(ffmt.std23 PROPERTIES SKIP_RETURN_CODE 77)
endif()

# New capability tests participate automatically; helper modules do not match.
add_test(NAME ffmt.harness COMMAND "${Python3_EXECUTABLE}" -m unittest discover
  -s "${CMAKE_CURRENT_SOURCE_DIR}/test/conformance" -p "test_*.py")
set_tests_properties(ffmt.harness PROPERTIES WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}")
add_test(NAME ffmt.host-conformance COMMAND "${Python3_EXECUTABLE}"
  "${CMAKE_CURRENT_SOURCE_DIR}/tools/conformance.py"
  --route host-buffer --route host-specifiers --opt 2
  --host-cxx "${CMAKE_CXX_COMPILER}" --fmt-dir "${FFMT_FMT_DIR}")
set_tests_properties(ffmt.host-conformance PROPERTIES
  TIMEOUT 1800 WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
  ENVIRONMENT "CXX=${CMAKE_CXX_COMPILER}")
'''
TEST_APPEND=r'''
option(FFMT_BUILD_TESTS "Build the portable conformance and regression tests" OFF)
option(FFMT_BUILD_CXX23_TESTS "Include optional C++23 standard-type tests" OFF)
if(FFMT_BUILD_CXX23_TESTS AND NOT FFMT_BUILD_TESTS)
  message(FATAL_ERROR "FFMT_BUILD_CXX23_TESTS requires FFMT_BUILD_TESTS")
endif()
if(FFMT_BUILD_TESTS)
  enable_testing()
  include(cmake/ffmtTests.cmake)
endif()
'''
BUILD_TESTING=r'''
## Portable CMake tests

Tests are opt-in. They require Python 3, Git and a clean independent fmt checkout
at revision `0fc31633e7d53ac895ae0a688b83b7d44f0b0c1f`. Configuration verifies
that checkout and never clones, switches or modifies it.

```sh
git clone https://github.com/fmtlib/fmt.git third_party/fmt
git -C third_party/fmt checkout 0fc31633e7d53ac895ae0a688b83b7d44f0b0c1f
cmake -S . -B build/cmake -DFFMT_BUILD_TESTS=ON -DFFMT_FMT_DIR="$PWD/third_party/fmt"
cmake --build build/cmake -j2
ctest --test-dir build/cmake --output-on-failure
```

Each declared C++ suite has an explicit source and CTest entry. Missing sources
fail configuration; they are never silently omitted. Assertions stay enabled in
Release builds. The floating suite also runs with `FFMT_PORTABLE_SHORTEST=1`;
the fast-math target has a separately compiled strict oracle. Python discovery
runs every `test_*.py` capability test, rather than only the original runner test.

Native int128, BitInt and binary128 tests report CTest skips via exit 77 when the
compiler lacks the tested extension. Optional C++23 expected/unexpected tests use
`-DFFMT_BUILD_CXX23_TESTS=ON`; that option requires `FFMT_BUILD_TESTS=ON` and a
compiler accepting C++23 mode. A standard library lacking expected reports 77.
A skip is not evidence that the corresponding feature conforms.

The full host differential test compares both compatibility paths, including
the independent numeric memory corpus. Compiler/runtime investigations and
accelerator campaign results remain separate; see [the conformance guide](CONFORMANCE.md).
'''
cmake_deps=['cmake-package','migration','named-arguments','ranges','chrono','standard-types','std23','styling','enum-helpers','typed-printf','feature-integration','tool-numeric-memory']
stage('cmake-tests','Register every split portable suite explicitly in CTest',cmake_deps,{'CMakeLists.txt':PACKAGE+TEST_APPEND,'cmake/ffmtTests.cmake':TESTS,'docs/BUILD.md':BUILD+BUILD_TESTING},'The previous test list used combined source files and existence guards, which can turn a missing regression into an apparently successful configure.','cmake -S . -B build/cmake -DFFMT_BUILD_TESTS=ON\ncmake --build build/cmake -j2\nctest --test-dir build/cmake --output-on-failure','Explicit source registrations preserve the decomposed suites, while Python discovers all capability unit tests. Configure verifies a clean pinned oracle; only tests discover Python and Git.','Full tests require the complete feature checkout and independent oracle. Optional extension skips remain visible, and C++23 stays opt-in. This is host validation, not accelerator runtime qualification.',['cmake/ffmtTests.cmake:ffmt_add_regression and source list','cmake/ffmtTests.cmake:extension flags and Python discovery','CMakeLists.txt:test options','docs/BUILD.md'],['cmake -S . -B build/cmake -DFFMT_BUILD_TESTS=ON -DFFMT_BUILD_CXX23_TESTS=ON -DCMAKE_CXX_COMPILER="$CXX" -DFFMT_FMT_DIR="$FFMT_FMT_DIR"','cmake --build build/cmake -j2','ctest --test-dir build/cmake --output-on-failure','ctest --test-dir build/cmake -N'],limitations='Run on the assembled complete-feature commit. Inspect skip counts; an extension skip is not a pass. Missing declared C++ sources must fail configuration. No hosted/device result is implied.')
# CI stages retain the already-reviewed readiness and resource policies verbatim.
host=(OUT/'coverage-policy/files/.github/workflows/host.yml').read_text()
a=host.index('      # `-fno-sanitize=bool`'); b=host.index('      UBSAN_OPTIONS:',a)
san_host=host[:a]+'      EXTRA_CXXFLAGS: -fsanitize=address,undefined\n'+host[b:]
SAN_DOC=r'''# Host sanitizer policy

Ready host CI runs AddressSanitizer and the complete UndefinedBehaviorSanitizer
set with `EXTRA_CXXFLAGS=-fsanitize=address,undefined`. Errors stop the test run.

The former workflow disabled bool validation globally using
`-fno-sanitize=bool` for the old std::format-based test path. The checked engine
and pinned independent fmt reference replace that path, so the exception is
removed. A bool problem in library or reference code now fails the job. A future
toolchain-specific issue needs its own reproducer and review instead of silently
restoring a broad exception.

The compiler matrix, test commands, draft/ready behavior and coverage reporting
policy are unchanged by this sanitizer setting.
'''
stage('ci-sanitizers','Restore bool validation in the host sanitizer jobs',['migration','coverage-policy'],{'.github/workflows/host.yml':san_host,'docs/contributing/SANITIZERS.md':SAN_DOC},'The historical blanket bool suppression can hide undefined behavior after the old formatting path has been replaced.','EXTRA_CXXFLAGS=-fsanitize=address,undefined\n# bool checks are active again','Remove only the obsolete -fno-sanitize=bool exception and its explanation; preserve the matrix and all commands.','Dependency/toolchain bool defects now fail CI as well. A new suppression would need a demonstrated scoped reason.',['.github/workflows/host.yml:matrix.env.EXTRA_CXXFLAGS','docs/contributing/SANITIZERS.md'],['make -j2 CXX="$CXX" EXTRA_CXXFLAGS="-fsanitize=address,undefined" test-host test-capabilities conformance-harness','make -j2 CXX="$CXX" EXTRA_CXXFLAGS="-fsanitize=address,undefined" test-negative'],kind='ci-policy',limitations='Validate sanitizers with GCC and Clang after migration. This stage does not change hosted readiness, coverage policy or corpus selection.')
full_host=san_host.replace('# Does it format correctly? Runs the test suite on the CPU and diffs both\n# paths (FFMT_BUFFER_PATH=0 and =1, through libc printf) against {fmt}:\n# compilers x opt levels under sanitizers, plain Ubuntu / macOS builds,\n# -ffast-math, negative-compile tests, and the coverage gate.','# Portable formatting regressions, independent exact-byte/memory conformance,\n# sanitizers, diagnostic-aware negative tests, and source coverage reporting.')
needle='        run: make -j2 test-host test-capabilities conformance-harness\n'
full_host=full_host.replace(needle,needle+r'''      - name: Compare the independent host stdout and memory corpora
        run: >-
          python3 tools/conformance.py
          --route host-buffer --route host-specifiers
          --opt "${HOST_OPT#-O}" --host-cxx "$CXX"
          --fmt-dir third_party/fmt --output artifacts/ci-conformance
''',1)
a=full_host.index('\n  plain:')
full_host=full_host[:a]+r'''      - name: Preserve conformance commands, sources, diagnostics and results
        if: ${{ always() && !cancelled() }}
        uses: actions/upload-artifact@v4
        with:
          name: conformance-${{ matrix.cxx }}-${{ matrix.opt }}
          path: artifacts/ci-conformance/
          if-no-files-found: warn
'''+full_host[a:]
CI_DOC=r'''# Independent host conformance in ready CI

The sanitizer matrix retains its focused C++ and Python checks. It also runs the
portable differential driver for both host compatibility routes at the matrix's
optimization level. The independent oracle uses the immutable fmt checkout;
programs using ffmt compare complete stdout bytes and framed numeric memory
records, including required/written counts and errors.

```sh
python3 tools/conformance.py --route host-buffer --route host-specifiers \
  --opt 2 --host-cxx g++ --fmt-dir third_party/fmt
```

The corpus includes the feature modules present in this complete checkout.
Cases are selected with their implementations; earlier feature PRs keep their
own focused portable regressions. Missing/failed/unsupported records make the
host conformance step fail rather than count as passes. The corpus is a useful
sample of fmt behavior, not exhaustive compatibility.

The driver keeps commands, source snapshots, reference identity, diagnostics and
results under `artifacts/ci-conformance/`. CI uploads that directory after success
or failure when the job has not been cancelled. A cancelled run is incomplete
evidence. Focused Make tests use ASan/UBSan; this separate driver uses its own
explicit compiler flags and is not implicitly sanitized by EXTRA_CXXFLAGS.

Draft PR compiler jobs remain skipped. `ready_for_review` starts the normal
host/device jobs for a ready wave; this change does not mark later waves ready.
No scheduler or evaluation-repository profile is required.
'''
ci_deps=['ci-sanitizers','tool-numeric-memory','named-arguments','ranges','chrono','standard-types','std23','styling','enum-helpers','typed-printf','feature-integration']
stage('ci-conformance','Run and retain independent host corpus checks in ready CI',ci_deps,{'.github/workflows/host.yml':full_host,'docs/contributing/CONFORMANCE_CI.md':CI_DOC},'Focused regressions alone do not exercise the independently compiled output corpus and framed memory comparison in hosted CI.','python3 tools/conformance.py --route host-buffer --route host-specifiers --opt 2 --host-cxx g++','Add one explicit differential step to each Linux compiler/optimization job and upload its complete evidence directory even after a failure.','This increases hosted compile work; cases sample behavior rather than prove full fmt compatibility. The separate runner does not inherit Make sanitizer flags. Draft compiler jobs remain skipped.',['.github/workflows/host.yml:matrix conformance step and evidence upload','docs/contributing/CONFORMANCE_CI.md'],['python3 -m unittest discover -s test/conformance -p "test_*.py"','python3 tools/conformance.py --route host-buffer --route host-specifiers --opt 2 --host-cxx "$CXX" --fmt-dir "$FFMT_FMT_DIR"'],kind='ci-integration',limitations='Portable validation runs on the complete feature commit. Hosted checks start only for ready review waves; draft skips and cancellations are not passing evidence. This does not repeat hardware campaigns.')
# Preserve independent compiler controls outside the library source tree.
REPRO_DOC=f'''# Compiler/runtime reproducers

Independent compiler/runtime controls belong in the companion
[ffmt-evaluation]({EVAL}) repository. They do not include ffmt and do not serve
as library regressions.

The two controls inherited from the upstream library baseline are preserved at:

- [DPC++ local-pointer printf control]({EVAL}/blob/{EVAL_SHA}/implementation_limitation/dpcpp_O0.cpp).
- [Intel OpenMP pragma-in-macro control]({EVAL}/blob/{EVAL_SHA}/implementation_limitation/icpx_omp_pragma_in_dowhile.cpp).

Their original source bytes, context and provenance remain in evaluation. The
[repository split ledger]({EVAL}/blob/{EVAL_SHA}/docs/provenance/split.json)
records those paths and hashes. Removing their copies from this source tree does
not rewrite the upstream baseline or alter captured failures. Portable tests
that directly exercise ffmt remain under `test/` in this repository.
'''
removes=['implementation_limitation/dpcpp_O0.cpp','implementation_limitation/icpx_omp_pragma_in_dowhile.cpp']
stage('reproducer-relocation','Remove preserved independent compiler controls from the library',['build-registration'],{'docs/contributing/REPRODUCERS.md':REPRO_DOC},'Two inherited compiler/runtime controls live in the library tree despite having no ffmt dependency.','// The controls include SYCL/stdio, not ffmt; their preserved sources are linked in docs/contributing/REPRODUCERS.md.','Delete only the redundant library copies and link fixed evaluation commits that retain the exact source bytes and provenance.','Readers follow the companion repository for independent compiler investigations; library regressions stay in this checkout.',['docs/contributing/REPRODUCERS.md'],['Verify both removed paths match the preserved evaluation source hashes; no compiler campaign rerun is required.'],remove=removes,kind='reproducer-relocation',limitations='Read-only byte/hash verification is sufficient for relocation; original sources and captured failures stay unchanged in evaluation.')
proof=[]
for p in removes:
 original=subprocess.check_output(['git','show','3fe258a:'+p],cwd=ROOT)
 retained=subprocess.check_output(['git','show',EVAL_SHA+':'+p],cwd=ROOT.parent/'ffmt-evaluation')
 proof.append(dict(original_path=p,original_commit='3fe258a87675c997667c899c2b0f0cad405aad5a',evaluation_commit=EVAL_SHA,sha256=hashlib.sha256(original).hexdigest(),byte_identical=original==retained))
(OUT/'reproducer-relocation-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
README=r'''# ffmt

C++20 formatting for host code and accelerator kernels, with
[{fmt}](https://github.com/fmtlib/fmt) as the semantic reference.

```cpp
#include <ffmt/base.hpp>

ffmt::println("value = {0:+08.2f}, again = {0}", 1.25);

char output[8];
auto result = ffmt::format_to_n(output, sizeof output, "{:012x}", 42);
// Eight stored bytes, twelve required bytes; no NUL is appended.
```

ffmt is header-only. Ordinary consumers need neither fmt nor Python; those are
independent test dependencies. Include the optional header for each additional
format family. Device use also requires the formatted objects and their
operations to be callable by the selected compiler.

| Start here | Contents |
|---|---|
| [API and output contracts](docs/API.md) | Checked results, buffers, custom formatters, optional headers and configuration |
| [Build and install](docs/BUILD.md) | Source and installed CMake targets; opt-in portable tests |
| [Backend contracts](docs/BACKENDS.md) | CUDA, HIP, SYCL, SPIR-V, OpenMP and other supported compiler routes |
| [Conformance guide](docs/CONFORMANCE.md) | Independent oracle, focused regressions, exact-byte and memory comparisons |
| [Contributor CI policy](docs/contributing/CI.md) | Ready review waves and the meaning of skipped hosted jobs |
| [Coverage policy](docs/contributing/COVERAGE.md) | Reporting and the limits of the instrumentation denominator |

System profiles, provisioning, scheduling, captured campaigns, independent
compiler reproducers and the manuscript belong in
[ffmt-evaluation](https://github.com/nscottnichols/ffmt-evaluation). They are not
needed to build or test the library. Preserved source snapshots and their
revision mapping remain documented there; library PRs stay unmerged until
reviewed.

Numerical conversion and Unicode material incorporates work from fmt and
Dragonbox. See [NOTICE](NOTICE) and [component licenses](LICENSES).
'''
API=r'''# API and output contracts

Include `<ffmt/base.hpp>` for brace formatting. Literal syntax and positional
fields are checked at compilation; `ffmt::runtime(text)` accepts counted runtime
format text and reports errors through the result. Named fields use runtime
names; see [named arguments](features/named-arguments.md) for their validation
and lifetime rules.

## Buffers and checked results

```cpp
char output[8];
auto result = ffmt::format_to_n(output, sizeof output,
                                ffmt::runtime("{:012x}"), 42);
if (result) {
  // written == 8, required == 12; output is a counted prefix, without a NUL.
}
```

`format_to_n` stores at most the supplied number of code units. A short
 destination is successful bounded formatting: `written` counts stored units,
`required` is the complete size, and `out` is the advanced iterator. It never
adds a terminator. `format_to` accepts an output iterator without a bound;
`formatted_size` returns a result whose `required` field gives the size.

`try_print` and `try_println` return checked stdout results. `print`, `println`,
`FFMT_PRINT` and `FFMT_PRINTLN` discard that status. Template calls such as
`ffmt::print<"{}">(value)` remain supported. `FFMT_PRINTF` and `FFMT_PRINTLNF` are
compatibility aliases for brace formatting; typed percent formatting is in the
separate [printf header](features/printf.md).

Errors distinguish invalid syntax, invalid arguments/specifications, unsupported
types, invalid code points, output overflow and transport failure. A prefix may
already have been written; `required` is meaningful only on success. Narrow
memory output preserves embedded NULs. Wide memory output preserves wide code
units; wide stdout encodes UTF-8 and rejects invalid scalar values.

## Custom formatters

A formatter can reuse a builtin parser and output implementation:

```cpp
struct index { int value; };

template <> struct ffmt::formatter<index> : ffmt::formatter<int> {
  template <typename Context>
  FMT_HD auto format(const index& value, Context& ctx) const {
    return ffmt::formatter<int>::format(value.value, ctx);
  }
};
```

The parse/context protocol preserves cv-qualified references and does not copy
formatter values. Mark custom operations device callable where the selected
compiler requires it. `formatted_size` invokes formatter logic; measuring and
formatting separately invokes it twice. The historical static
`formatter<T>::format(value)` protocol returning `ffmt::formatted<...>` remains
supported for empty outer specs, including existing SYCL id/range/item
formatters. ADL `format_as(value)` maps a user type to a primitive representation.

## Optional headers

| Header | Guide |
|---|---|
| `ffmt/args.hpp` | [Referenced named arguments](features/named-arguments.md) |
| `ffmt/ranges.hpp` | [Ranges, tuples, joins and container adapters](features/ranges.md) |
| `ffmt/chrono.hpp` | [Locale-independent durations and calendar values](features/chrono.md) |
| `ffmt/std.hpp` | [Standard wrappers, bitsets, complex and pointer views](features/standard-types.md) |
| `ffmt/std23.hpp` | [Optional C++23 expected/unexpected](features/std23.md) |
| `ffmt/color.hpp` | [Explicit ANSI color and emphasis](features/styling.md) |
| `ffmt/enum.hpp` | [Opt-in underlying enum values](features/enums.md) |
| `ffmt/printf.hpp` | [Typed checked percent formatting](features/printf.md) |

Contained standard-library types and their operations must themselves be device
callable. Host filesystem, stream, locale/timezone-database, RTTI, thread-ID and
exception-traversal services are outside this device API.

Optional families share [nested alignment support](features/family-support.md).
Left-aligned bodies render once on every destination. Bounded writable pointer
buffers also support right/center alignment in one pass, retaining the exact
truncated prefix. Irreversible iterators and stdout require replayable builtin
values and forward ranges for right/center alignment; unknown custom formatters
and consuming ranges return `unsupported_type` before invoking that body.

## Configuration and stdout

Use consistent macros across translation units. `FFMT_BUFFER_SIZE` defaults to
128 and controls staging capacity, not total output length. Long output streams
through multiple chunks. Independent calls may interleave; runtime printf FIFO
capacity and kernel synchronization remain application/runtime concerns.
`FFMT_BUFFER_PATH=0` and `=1` remain accepted and use the same engine.
`FFMT_UNICODE` controls narrow-string Unicode measurement and defaults to 1.

Some SPIR-V printf runtimes drop embedded NULs; AdaptiveCpp SSCP device printing
accepts null-terminated strings. Checked printing reports transport errors for
unsupported NUL chunks, while memory formatting stays binary safe.
`FFMT_SPIRV_NUL_SUPPORTED=1` opts into a separately validated SPIR-V runtime and
does not change the SSCP string contract. See [backend contracts](BACKENDS.md)
for compiler flags and route-specific requirements.
'''
# Keep portable backend/testing guidance while fixing stale combined-suite commands.
backends=(ROOT/'docs/BACKENDS.md').read_text().replace('Bounded writable pointer destinations and left-aligned streaming format family\nbodies once.', 'Bounded writable pointer destinations render family bodies once. Left-aligned\nstreaming destinations also render each body once.')
conformance=(ROOT/'docs/CONFORMANCE.md').read_text()
conformance=conformance.replace('python3 -m unittest discover -s test/conformance -p test_runner.py','python3 -m unittest discover -s test/conformance -p \'test_*.py\'')
conformance=conformance.replace('make test-host test-focused test-negative CXX=g++','make test-host test-capabilities test-negative CXX=g++')
conformance=conformance.replace('CTest and Make exercise the same focused numeric, bounded-output, custom-type\nand format-family regressions.', 'CTest and Make explicitly register the decomposed numeric, bounded-output,\ncustom-type and independent family regressions. Missing declared C++ sources\nare configuration/build errors, not silently omitted tests. CMake also runs\nthe seeded floating suite with `FFMT_PORTABLE_SHORTEST=1`.')
conformance=conformance.replace('The reference is an independent host build of fmt commit','For library usage see [API contracts](API.md), and for installation/CMake\noptions see [build and test integration](BUILD.md).\n\nThe reference is an independent host build of fmt commit')
conformance+='\nHosted coverage replaces a percentage regression gate with reporting; passing\nCI no longer guarantees nondecreasing coverage. See the explicit\n[coverage policy](contributing/COVERAGE.md). Independent compiler/runtime\n[reproducers are preserved in evaluation](contributing/REPRODUCERS.md).\n'
api_deps=['cmake-tests','ci-conformance','reproducer-relocation','benchmark-driver','tool-memory-cuda','tool-memory-hip','tool-memory-openmp','tool-memory-sycl','tool-memory-kokkos']
stage('api-index','Make library contracts and portable guides easy to navigate',api_deps,{'README.md':README,'docs/API.md':API,'docs/BACKENDS.md':backends,'docs/CONFORMANCE.md':conformance},'The top-level README combines setup, output contracts, all optional families and research links in one dense page.','#include <ffmt/base.hpp>\nffmt::println("value = {:04x}", 42);\n// Follow API/build/backend/conformance guides for the corresponding detail.','Keep one short entry page and move detailed output/customization/configuration contracts into a linked API guide. Feature guides remain with their implementations; build and conformance pages use the actual split test names.','Readers follow focused pages for detail. Documentation describes supported contracts and sampled tests rather than implying universal backend or fmt conformance.',['README.md','docs/API.md','docs/BUILD.md','docs/BACKENDS.md','docs/CONFORMANCE.md'],['Check all repository-relative Markdown links against the assembled checkout.','Review examples against the public base and optional-header interfaces; formatter implementation is unchanged.'],kind='documentation',limitations='Documentation/link checks are read-only. Existing portable tests substantiate examples; no hardware campaign rerun follows this navigation change.')
(OUT/'remaining-index.json').write_text(json.dumps(INVENTORY,indent=2)+'\n')
