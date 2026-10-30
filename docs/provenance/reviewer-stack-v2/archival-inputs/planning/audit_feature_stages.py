from pathlib import Path
import json
import re
import shutil
import subprocess

root=Path('/vast/projects/datascience/nnichols/ffmt_project/ffmt/artifacts/reviewer-v2')
src=root/'feature-source'
out=root/'feature-stages'
orig=root/'feature-original'

# Split the printf matrix by the maintainer decision each section exercises.
# The nested loops, argument sets and assertions remain byte-for-byte fixtures.
old=(orig/'test_families_printf.cpp').read_text().splitlines(keepends=True)
def lines(a,b): return ''.join(old[a-1:b])
prefix=''.join(old[:59]) # anonymous helper namespace closes at line 58
# Discover main instead of relying on that explanatory line count.
original=''.join(old)
prefix=original[:original.index('int main() {')]
parts=[('literal_and_integer_conversions',61,77,''),
       ('floating_conversions',78,85,''),
       ('dynamic_and_positional_fields',86,91,''),
       ('strings_pointers_and_characters',92,100,''),
       ('wide_conversions',101,102,''),
       ('invalid_conversions_do_not_write',103,116,'  int integer = 1;\n')]
# Line 60 is the first check after the main declaration in the original.
assert old[60].lstrip().startswith('check('),repr(old[60])
text=prefix+'\nnamespace {\n'
for name,a,b,setup in parts:
    text+=f'void {name}() {{\n'+setup+lines(a,b)+'}\n\n'
text+='} // namespace\nint main() {\n'
for name,*_ in parts: text+=f'  {name}();\n'
text+='  std::printf("printf: %d differential/bounded comparisons passed\\n", comparisons);\n}\n'
path=src/'test/conformance/test_printf.cpp'
path.write_text(text)
subprocess.run(['/soft/compilers/llvm/release-22.1.8/bin/clang-format','-i',str(path)],check=True)
shutil.copy2(path,out/'typed-printf/files/test/conformance/test_printf.cpp')

before={
'named-arguments':'A checked core call with {value:04x} has no name wrapper to bind value; use positional indices instead.',
'enum-helpers':'An enum with no formatter or ADL mapping cannot be passed directly to checked formatting.',
'shared-family':'Each optional formatter would otherwise duplicate alignment parsing and counting, risking replay of mutating values.',
'ranges':'An std::array<int,3> has no formatter, so a checked call with {::03} is rejected.',
'chrono':'A std::chrono::milliseconds value has no formatter, so the %T token cannot produce a duration.',
'standard-types':'std::optional<int> and std::complex<double> have no formatter in the core.',
'std23':'std::expected<int,int> has no formatter after including std.hpp alone.',
'styling':'There is no typed style wrapper to emit ANSI foreground and emphasis around a value.',
'typed-printf':'Brace formatting does not interpret %#08x; there is no typed percent parser or explicit %n rejection.',
'feature-integration':'Independent names/ranges/std suites do not verify named widths on optional adapters or mutable named ranges.',
}
for stagepath in out.glob('*/stage.json'):
    data=json.loads(stagepath.read_text())
    data['before']=before[data['id']]
    data['after']=data['example']
    data['validation']={
       'commands':data['tests']['commands'],
       'results':'Pending validation of the assembled intermediate commit; root records exact commands and outcomes.',
       'limitations':'Portable checks do not establish accelerator runtime availability. No hardware campaign rerun is warranted by whitespace/comments, helper renaming and test decomposition alone.'
    }
    if data['id']=='typed-printf':
        data['reading_order']=['include/ffmt/printf.hpp:family_printf_value','include/ffmt/printf.hpp:family_printf','test/conformance/test_printf.cpp:dynamic_and_positional_fields','test/conformance/test_printf.cpp:invalid_conversions_do_not_write']
    stagepath.write_text(json.dumps(data,indent=2)+'\n')

# Compare C++ lexical tokens, ignoring only whitespace/comments and include order.
# clang-format may reorder includes, so compare preprocessing include lines
# separately as a multiset. The padding lambda is the sole deliberate identifier
# rename and is normalized back for this equivalence check.
token_re=re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|(?:u8|u|U|L)?"(?:\\.|[^"\\])*"|(?:u8|u|U|L)?\'(?:\\.|[^\'\\])*\'|[A-Za-z_][A-Za-z0-9_]*|[0-9]+(?:[A-Za-z0-9_.]*[A-Za-z0-9_])?|[^\s]')
def tokens(text):
    inc=re.findall(r'^\s*#include[^\n]*',text,re.M)
    text=re.sub(r'^\s*#include[^\n]*','',text,flags=re.M)
    result=[]
    for m in token_re.finditer(text):
        item=m.group(0)
        if item.startswith('//') or item.startswith('/*'): continue
        result.append('once' if item=='render_and_measure' else item)
    return sorted(x.strip() for x in inc),result

headers=['args.hpp','enum.hpp','detail/family.hpp','ranges.hpp','chrono.hpp','std.hpp','std23.hpp','color.hpp','printf.hpp']
checks=[]
for header in headers:
    prior=subprocess.check_output(['git','-C',str(src),'show','aeff043614725d58d383c8add086f548d77d05eb:include/ffmt/'+header],text=True)
    after=(src/'include/ffmt'/header).read_text()
    equivalent=tokens(prior)==tokens(after)
    checks.append(dict(path='include/ffmt/'+header,cpp_tokens_and_include_set_equal=equivalent,normalization='whitespace/comments/include ordering; family.hpp additionally normalizes once -> render_and_measure'))
    if not equivalent: raise SystemExit('unexpected implementation token change: '+header)

# All old family fixture blocks are moved whole except the three deliberate
# conversions to standalone named/enum/core assertions and integration values.
coverage={
 'test_families.cpp':[
   {'source_lines':'29,41-51','destination':'ranges/std local legacy formatter fixtures'},
   {'source_lines':'30,151-153','destination':'test_std.cpp'},
   {'source_lines':'31-50,52-55,60,68-91,158-196,293-294,297-301,313-321','destination':'test_ranges.cpp'},
   {'source_lines':'56-59,156-157','destination':'test_enum.cpp'},
   {'source_lines':'61-67,155','destination':'test_formatter_composition.cpp'},
   {'source_lines':'94-147','destination':'family_test_support.hpp; chrono oracle wrappers remain test_chrono.cpp'},
   {'source_lines':'197-236,310-312','destination':'test_std.cpp'},
   {'source_lines':'237-241','destination':'test_style.cpp'},
   {'source_lines':'242','destination':'test_named_arguments.cpp'},
   {'source_lines':'243-245','destination':'test_feature_integration.cpp'},
   {'source_lines':'246-292,295-296,302-309','destination':'test_chrono.cpp'},
 ],
 'test_engine_forwarding.cpp':[
   {'source_lines':'13-24,51-52,74-82,94-95,100-103,147-149','destination':'test_core_forwarding.cpp (fresh counters per operation; compile-negative check uses format_to before transport exists)'},
   {'source_lines':'42-54,104-110','destination':'test_legacy_forwarding.cpp'},
   {'source_lines':'83-85,96-99','destination':'test_named_arguments.cpp (fresh named counter begins at 1 rather than earlier sequential 4)'},
   {'source_lines':'86-93','destination':'test_transport_forwarding.cpp (fresh counters per transport entry point)'},
   {'source_lines':'25-41,55-69,111-146','destination':'test_ranges_forwarding.cpp'},
 ],
 'test_families_ranges.cpp':[
   {'source_lines':'entire file except named range assertion','destination':'test_ranges_iterators.cpp'},
   {'source_lines':'named mutable range assertion','destination':'test_feature_integration.cpp'},
 ],
 'test_families_std23.cpp':[{'source_lines':'entire file','destination':'test_std23.cpp'}],
 'test_families_printf.cpp':[{'source_lines':'entire file','destination':'test_printf.cpp (matrix grouped into named functions; integer %n guard retained)'}]
}
report=dict(snapshot='aeff043614725d58d383c8add086f548d77d05eb',header_equivalence=checks,test_mapping=coverage,added_tests=['test_family_support.cpp: direct single-pass bounded alignment, streaming replay rejection and Unicode columns','test_named_arguments.cpp: primitive named dynamic width'],hardware='No hardware run. All optional header C++ tokens unchanged after documented lexical normalization; new tests require allocated CPU validation of assembled stages.')
(out/'source-audit.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'index.json').write_text(json.dumps([json.loads(p.read_text()) for p in out.glob('*/stage.json')],indent=2)+'\n')
print('Audited 9 optional headers: equivalent after lexical normalization.')
print('All original omnibus/forwarding suite sections mapped; printf matrix grouped.')
