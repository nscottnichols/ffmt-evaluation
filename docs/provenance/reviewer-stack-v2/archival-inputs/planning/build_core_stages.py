from pathlib import Path
import subprocess,json,re,hashlib,shutil
ROOT=Path('/vast/projects/datascience/nnichols/ffmt_project/ffmt'); WORK=ROOT/'artifacts/reviewer-v2/core-source'; OUT=ROOT/'artifacts/reviewer-v2/core-stages'; OUT.mkdir(exist_ok=True)
def orig(p,rev='aeff043'): return subprocess.check_output(['git','show',f'{rev}:{p}'],cwd=WORK,text=True)
C=orig('include/ffmt/core.hpp'); B=orig('include/ffmt/base.hpp'); N=orig('include/ffmt/detail/numeric.hpp')
def part(s,a,b): return s[s.index(a):s.index(b,s.index(a))]
def ff(s): return '#pragma once\nnamespace ffmt {\n'+s+'\n}\n'
def dd(s): return '#pragma once\nnamespace ffmt::detail {\n'+s+'\n}\n'
F={}
F['config.hpp']='#pragma once\n'+part(B,'#if defined(__ADAPTIVECPP__)','// The following Dragonbox')
F['result.hpp']='#pragma once\n'+part(C,'namespace ffmt {','namespace detail {\ntemplate <std::size_t N')+'}\n'
args=part(C,'template <std::size_t N, typename Char = char> struct fixed_string','template <typename Char> FMT_HD constexpr bool is_digit'); F['arguments.hpp']=dd(args)
ph=part(C,'template <typename Char> FMT_HD constexpr bool is_digit','// Counted views never')
dec=part(C,'// Counted views never','} // namespace detail\n\ntemplate <typename Char> class basic_format_parse_context')
pc=part(C,'template <typename Char> class basic_format_parse_context','namespace detail {\ntemplate <typename Char> struct basic_format_spec')
sp=part(C,'template <typename Char> struct basic_format_spec','template <typename T, typename Char>\ninline constexpr bool character')
walk=part(C,'// Shared parser. A handler validates','template <typename T, typename Char>\nFMT_HD constexpr format_error\nvalidate_one')
F['parse.hpp']=ff('namespace detail {\n'+ph+dec+'}\n'+pc+'namespace detail {\n'+sp+walk+'}\n')
F['type_traits.hpp']=dd(part(C,'template <typename T, typename Char>\ninline constexpr bool character','} // namespace detail\n\n// The primary formatter'))
full_traits=part(C,'template <typename T, typename Char>\ninline constexpr bool character','} // namespace detail\n\n// The primary formatter')
cut=full_traits.index('template <typename T>\nconcept has_format_as')
F['type_categories.hpp']=dd(full_traits[:cut])
F['type_traits.hpp']=dd(full_traits[cut:])
primary=part(C,'// The primary formatter','namespace detail {\ntemplate <typename Tuple, typename F, std::size_t... I>')
visit=part(C,'template <typename Tuple, typename F, std::size_t... I>','} // namespace detail\n\ntemplate <typename OutputIt, typename Char,')
F['formatters.hpp']=ff(primary+'namespace detail {\n'+visit+'}\n')
ct=part(C,'template <typename OutputIt, typename Char,\n          typename ArgsTuple','namespace detail {\ntemplate <typename T, typename Char> consteval bool formatter_invocable')
ft=part(C,'template <typename T, typename Char> consteval bool formatter_invocable','namespace detail {\ntemplate <typename Context>\nFMT_HD constexpr void put')
hp=part(C,'template <typename Context>\nFMT_HD constexpr void put','// An output iterator whose copies share a sink.')
F['context.hpp']=ff(ct+'namespace detail {\n'+ft+'namespace detail {\n'+hp+'}\n')
F['output.hpp']=dd(part(C,'// An output iterator whose copies share a sink.','// Shared parser. A handler validates'))
F['validation.hpp']=ff('namespace detail {\n'+part(C,'template <typename T, typename Char>\nFMT_HD constexpr format_error\nvalidate_one','// The engine below is independent of the destination'))
F['execution.hpp']=ff(part(C,'// The engine below is independent of the destination','template <typename OutputIt, typename Char, typename... Args>\nFMT_HD auto format_to_n'))
F['memory.hpp']=ff(part(C,'template <typename OutputIt, typename Char, typename... Args>\nFMT_HD auto format_to_n','} // namespace ffmt\n\n#include "detail/numeric.hpp"'))
F['unicode_width.hpp']=dd(part(B,'struct wide_cp_range','// Decode the multi-byte UTF-8 sequence'))
dragon=part(B,'namespace dragonbox {','struct wide_cp_range'); exact=part(B,'struct exact_decimal','} // namespace ffmt::detail\n#ifdef _OPENMP')
def omp(s): return '#pragma once\n#ifdef _OPENMP\n#pragma omp declare target\n#endif\nnamespace ffmt::detail {\n'+s+'}\n#ifdef _OPENMP\n#pragma omp end declare target\n#endif\n'
F['dragonbox.hpp']=part(B,'// The following Dragonbox','#ifdef _OPENMP')+omp(dragon); F['exact_decimal.hpp']=omp(exact)
F['unicode_width.hpp']=omp(part(B,'struct wide_cp_range','// Decode the multi-byte UTF-8 sequence'))
F['legacy_emit.hpp']='#pragma once\n'+part(B,'// Compatibility for instrumentation','\n#include "core.hpp"')
suffix=B[B.index('#if defined(SYCL_LANGUAGE_VERSION) || FFMT_COMPILER_ACPP',B.index('#include "core.hpp"')):]; m=suffix.index('// Convenience macro')
F['sycl_formatters.hpp']='#pragma once\n'+suffix[:m]; F['print_macros.hpp']='#pragma once\n'+suffix[m:]
integer=part(N,'template <typename Context, typename Char, typename Body>','struct decimal_digits'); F['integer.hpp']=dd(integer)
F['numeric.hpp']=N.replace('#include "floating.hpp"','#include "floating.hpp"\n#include "integer.hpp"').replace(integer,'')
for n in ('floating','extended','text','unicode','transport'): F[n+'.hpp']=orig('include/ffmt/detail/'+n+'.hpp')
value_body=part(F['text.hpp'],'template <typename Context, typename T, typename Char>','} // namespace ffmt::detail')
F['value.hpp']=dd(value_body)
F['text.hpp']=F['text.hpp'].replace(value_body,'')
# Clarify internal conversion contracts without changing its algorithms.
F['floating.hpp']=F['floating.hpp'].replace('template <unsigned Capacity> struct precise_decimal {', '// Capacity counts decimal digits, not requested output precision. Callers\n// provide enough storage for the complete exact finite magnitude and interval\n// endpoints; the supported IEEE layouts have bounded exponent/significand sizes.\ntemplate <unsigned Capacity> struct precise_decimal {')
F['floating.hpp']=F['floating.hpp'].replace('template <typename T> FMT_HD int portable_shortest(char *out, T value) {', '// Internal precondition: value has a supported finite representation. This\n// renders the magnitude only; callers classify nonfinite values and emit signs.\n// The output buffer must hold a shortest representation (64 bytes suffices for\n// all supported formats). Decimal capacities conservatively cover exact binary64\n// expansions and endpoints (1100), and native80/binary128 endpoints (16520).\n// For binary128 the worst negative exponent is -16494. Midpoint endpoints\n// need at most 115 significand bits and powers of five through 5^16496,\n// requiring fewer than 11570 decimal digits. These bounds do not limit requested precision.\ntemplate <typename T> FMT_HD int portable_shortest(char *out, T value) {')
FILES={}; PREVIOUS={}; STAGES=[]; D='include/ffmt/detail/'
def put(p,s):
 if p.endswith('.cpp') or p.endswith('core_compare.hpp') or p.endswith('type_traits.hpp') or (p.endswith('text.hpp') and 'unicode.hpp' not in s):
  s=subprocess.run(['/soft/compilers/llvm/release-22.1.8/bin/clang-format','-style=LLVM'],input=s,text=True,capture_output=True,check=True).stdout
 FILES[p]=s
def detail(n,s=None): put(D+n,F[n] if s is None else s)
def checked(names): detail('checked.hpp','// Internal entry used to qualify the engine before public migration.\n#pragma once\n'+''.join('#include "'+n+'"\n' for n in names))
def test(n,body,includes=''):
 put('test/conformance/test_core_'+n+'.cpp','#ifdef NDEBUG\n#undef NDEBUG\n#endif\n#include <ffmt/detail/checked.hpp>\n#include <cassert>\n#include <string>\n#include <limits>\n'+includes+'\n'+body+'\n')
def emit(id,title,problem,example,design,tradeoffs,reading,tests=(),kind='source-refactor',remove=()):
 global PREVIOUS
 doc='docs/api/'+id+'.md'; put(doc,'# '+title+'\n\n'+problem+'\n\n```cpp\n'+example+'\n```\n\n'+design+'\n\n'+tradeoffs+'\n')
 folder=OUT/id; shutil.rmtree(folder/'files',ignore_errors=True); (folder/'files').mkdir(parents=True,exist_ok=True)
 for p,s in FILES.items():
  if PREVIOUS.get(p)==s: continue
  f=folder/'files'/p; f.parent.mkdir(parents=True,exist_ok=True); f.write_text(s)
 meta=dict(id=id,title=title,dependencies=[STAGES[-1]] if STAGES else [],change_kind=kind,remove=list(remove),tests=list(tests),docs=[doc],problem=problem,example=example,design=design,tradeoffs=tradeoffs,reading_order=reading)
 (folder/'stage.json').write_text(json.dumps(meta,indent=2)+'\n'); PREVIOUS=FILES.copy(); STAGES.append(id)
def handoff(id):
 folder=ROOT/'artifacts/reviewer-v2/feature-stages/core-handoff'/id/'files'
 if folder.exists():
  for p in folder.rglob('*'):
   if p.is_file(): put(str(p.relative_to(folder)),p.read_text())
put('include/ffmt/detail/legacy_base.hpp',orig('include/ffmt/base.hpp','3fe258a'))
put('include/ffmt/base.hpp','#pragma once\n// Keep the original implementation active until migration.\n#include "detail/legacy_base.hpp"\n')
emit('core-prepare','Preserve the existing implementation behind a wrapper','The replacement engine needs independent qualification while current callers remain usable.','#include <ffmt/base.hpp> // still selects the original implementation','The legacy header is copied byte for byte from upstream 3fe258a; the public wrapper only selects it.','The temporary extra include is removed once migration is validated.',['include/ffmt/base.hpp','include/ffmt/detail/legacy_base.hpp'],['legacy-host'],kind='mechanical-move')
detail('config.hpp')
(OUT/'config-move-proof.json').write_text(json.dumps({'source_commit':'aeff043614725d58d383c8add086f548d77d05eb','source_file':'include/ffmt/base.hpp','destination_file':'include/ffmt/detail/config.hpp','body_sha256':hashlib.sha256(part(B,'#if defined(__ADAPTIVECPP__)','// The following Dragonbox').encode()).hexdigest(),'comparison':'destination after pragma once is byte-identical to the selected source span'},indent=2)+'\n')
emit('checked-config','Extract the qualified compiler configuration','The standalone checked engine needs the same compiler and backend configuration as the qualified implementation.','#include <ffmt/detail/config.hpp>','Compiler macros and standard includes are copied without changes from aeff043. The extraction hash records the exact body.','This header is internal; callers continue including base.hpp. It does not activate the replacement engine.',['include/ffmt/detail/config.hpp'],['legacy-host'],kind='mechanical-extraction')
detail('result.hpp')
out=F['output.hpp']; a=out.index('  // Family adapters can align'); b=out.index('\n};\ntemplate <typename OutputIt',a); out=out[:a]+out[b:]; a=out.index('  struct padding_mark'); b=out.index('  FMT_HD void push(Char c)',a); out=out[:a]+out[b:]
detail('output.hpp',out); checked(['config.hpp','result.hpp','output.hpp'])
test('accounting',r'''int main() {
  char bytes[4] = {'!', '!', '!', '!'};
  ffmt::detail::iterator_sink<char*, char> sink{bytes+1, 2};
  ffmt::detail::sink_iterator out{&sink};
  auto copy=out; *out++='a'; *copy++='b'; copy.repeat('c',5);
  assert(sink.required==7 && sink.written==2);
  assert(bytes[0]=='!' && bytes[1]=='a' && bytes[2]=='b' && bytes[3]=='!');
  ffmt::detail::iterator_sink<char*,char> count{nullptr,0};
  count.repeat('x',std::numeric_limits<std::size_t>::max()); count.push('x');
  assert(count.error==ffmt::format_error::output_overflow && count.written==0);
}''')
emit('accounting','Count bounded output independently of formatting','Truncation must retain the complete required length without writing beyond caller capacity.','sink.repeat(\'x\', 7); // capacity 2: written=2, required=7','All iterator copies share a sink. Required-length overflow is detected before arithmetic wraps.','Counts describe code units, not display columns; family alignment hooks arrive with shared family support.',['include/ffmt/detail/result.hpp','include/ffmt/detail/output.hpp','test/conformance/test_core_accounting.cpp'],['test_core_accounting'])
args_basic=args
for pattern in [r'#if defined\(__SIZEOF_INT128__\).*?#endif\n',r'#if defined\(__SIZEOF_FLOAT128__\).*?#endif\n',r'#if defined\(__BITINT_MAXWIDTH__\).*?#endif\n']: args_basic=re.sub(pattern,'',args_basic,flags=re.S)
args_basic=args_basic.replace('static constexpr bool value = std::is_floating_point_v<T>;','static constexpr bool value = std::is_same_v<T,float> || std::is_same_v<T,double>;')
detail('arguments.hpp',dd(args_basic))
sp_ascii=sp; a=sp_ascii.index('  if constexpr (sizeof(Char) == 1)'); b=sp_ascii.index('  if (units && static_cast<std::size_t>(end - p) > units',a); sp_ascii=sp_ascii[:a]+sp_ascii[b:]
detail('parse.hpp',ff('namespace detail {\n'+ph+'}\n'+pc+'namespace detail {\n'+sp_ascii+walk+'}\n')); checked(['config.hpp','result.hpp','arguments.hpp','parse.hpp','output.hpp'])
test('parsing',r'''struct handler {
  std::string literal_text; int count=0;
  void literal(char c) { literal_text+=c; }
  ffmt::format_error argument(int index,ffmt::string_view,ffmt::format_parse_context& pc) {
    assert(index==count++); auto spec=ffmt::detail::parse_standard_specs(pc);
    assert(spec.width==4 && spec.type=='x'); return pc.error();
  }
};
int main() {
  handler events;
  assert(ffmt::detail::walk_format<char>("{{{:04x}}}",events)==ffmt::format_error::none);
  assert(events.literal_text=="{}" && events.count==1);
  for (const char* bad : {"{","}","{00}","{0} {}","{999999999999999}"}) {
    struct reject {
      void literal(char) {}
      ffmt::format_error argument(int,ffmt::string_view,ffmt::format_parse_context& pc) {
        ffmt::detail::parse_standard_specs(pc); return pc.error();
      }
    } h;
    assert(ffmt::detail::walk_format<char>(bad,h)!=ffmt::format_error::none);
  }
  ffmt::format_parse_context invalid{{nullptr,1}};
  assert(invalid.error()==ffmt::format_error::invalid_format);
}''')
emit('parsing','Parse and validate counted format strings','Runtime execution and literal validation need a single grammar.','walk_format("{{{:04x}}}", handler); // literal braces and one field','A handler receives parsed fields; parse context tracks index modes and checks dynamic references without producing output.','This prefix supports ASCII fill; counted Unicode decoding is introduced with its tests.',['include/ffmt/detail/parse.hpp','test/conformance/test_core_parsing.cpp'],['test_core_accounting','test_core_parsing'])
traits_plain=F['type_traits.hpp']; a=traits_plain.index('template <typename T>\nconcept has_format_as'); b=traits_plain.index('template <typename Context, typename T, typename Char>',a)
traits_plain=traits_plain[:a]+'''template <typename T> inline constexpr bool has_format_as = false;
template <typename T> FMT_HD constexpr decltype(auto) mapped_value(const T &x) { return x; }
template <typename T> using mapped_argument_t = T;
template <typename T> inline constexpr bool legacy_formatter = false;
'''+traits_plain[b:]
categories_nofloat=F['type_categories.hpp'].replace('constexpr bool flt = floating<T>;','constexpr bool flt = false;').replace('integer<T> || floating<T> || std::is_pointer_v<T>','integer<T> || std::is_pointer_v<T>'); categories_primitive=categories_nofloat.replace(" || t == '?'",'').replace(" || (ch && t == '?')",''); detail('type_categories.hpp',categories_primitive); detail('type_traits.hpp',traits_plain)
formatter_plain=F['formatters.hpp']; a=formatter_plain.index('template <detail::fixed_string Fmt, typename... Args> struct formatted'); b=formatter_plain.index('namespace detail {\ntemplate <typename Tuple',a); formatter_plain=formatter_plain[:a]+formatter_plain[b:]; detail('formatters.hpp',formatter_plain)
context_plain=F['context.hpp'].replace('  return requires(F &f, basic_format_parse_context<Char> &pc) {\n    f.parse(pc);\n  } && formatter_invocable<T, Char>();','  return false;')
context_plain=context_plain.replace('  using Value = std::remove_reference_t<T>;\n  if constexpr (legacy_formatter<U>)', '  using Value = std::remove_reference_t<T>;\n  using F = formatter<U, Char>;\n  if constexpr (requires { typename F::ffmt_primary_type; }) {\n    if constexpr (!std::is_same_v<typename F::ffmt_primary_type, U>) return false;\n  } else return false;\n  if constexpr (legacy_formatter<U>)'); detail('context.hpp',context_plain)
val=F['validation.hpp']; a=val.index('  if constexpr (legacy_formatter<U>) {'); b=val.index('    formatter<U, Char> fmt;',a); val=val[:a]+'  {\n'+val[b:]; detail('validation.hpp',val)
exe=F['execution.hpp']; a=exe.index('  } else if constexpr (legacy_formatter<U>) {'); b=exe.index('  } else {\n    formatter<U, Char> fmt;',a); exe=exe[:a]+exe[b:]; a=exe.index('// Adapt the original static formatter protocol'); b=exe.index('template <typename Context, typename Tuple> struct execution_handler',a); exe=exe[:a]+exe[b:]; exe=exe.replace('  } else if constexpr (legacy_formatter<U>)\n    format_selected(ctx, value, pc);\n  else {','  } else {'); detail('execution.hpp',exe)
for n in ('memory.hpp','integer.hpp'): detail(n)
text_ascii='''#pragma once
namespace ffmt::detail {
template <typename Context,typename Char>
FMT_HD void write_string(Context& ctx,basic_string_view<Char> value,basic_format_spec<Char> spec,bool=false) {
  spec=resolved(ctx,spec); auto size=value.size();
  if (spec.precision>=0 && size>static_cast<std::size_t>(spec.precision)) size=spec.precision;
  write_padded(ctx,spec,size,[&](auto& out) { append(out,value.data(),size); },'<');
}
'''+'}\n'
value_basic=F['value.hpp'].replace('  } else if constexpr (floating<U>)\n    write_float(ctx, value, s);','  } else if constexpr (floating<U>)\n    ctx.on_error(format_error::unsupported_type);'); detail('text.hpp',text_ascii); detail('value.hpp',value_basic)
INC=['config.hpp','result.hpp','arguments.hpp','parse.hpp','type_categories.hpp','type_traits.hpp','formatters.hpp','context.hpp','output.hpp','validation.hpp','execution.hpp','memory.hpp','integer.hpp','text.hpp','value.hpp']; checked(INC); PRIMITIVE_INC=INC.copy()
put('test/conformance/core_compare.hpp',r'''#pragma once
#include <ffmt/detail/checked.hpp>
#include <fmt/format.h>
#include <fmt/xchar.h>
#include <algorithm>
#include <cassert>
#include <cstdlib>
#include <iostream>
#include <string>
#include <cstdint>
template <typename... Args>
void compare(ffmt::string_view pattern,const Args&... args) {
  auto expected=fmt::format(fmt::runtime(fmt::string_view{pattern.data(),pattern.size()}),args...);
  std::string actual(expected.size()+8,'~');
  auto result=ffmt::format_to_n(actual.data(),expected.size(),ffmt::runtime(pattern),args...);
  if (!result || result.required!=expected.size() || result.written!=expected.size() || actual.substr(0,result.written)!=expected) {
    std::cerr<<"pattern="<<pattern<<" expected="<<expected<<" actual="<<actual.substr(0,result.written)<<'\n'; std::abort();
  }
  assert(actual.substr(expected.size())==std::string(8,'~'));
  for (std::size_t bound : {std::size_t(0),std::size_t(1),expected.size()/2}) {
    actual.assign(expected.size()+8,'~');
    auto bounded=ffmt::format_to_n(actual.data(),bound,ffmt::runtime(pattern),args...);
    const auto retained = std::min(bound, expected.size());
    assert(bounded && bounded.required==expected.size() && bounded.written==retained);
    assert(actual.substr(0,retained)==expected.substr(0,retained));
    assert(actual[retained]=='~' && actual[bound]=='~');
  }
}
''')
test('primitives',r'''int main() {
  compare(""); compare("{}", std::string{});
  compare("a{}b",char(0)); compare("{0} {0} {1}",42,"hello"); compare("[{0:>{1}}]",42,400);
  compare("{}",ffmt::string_view{"x\0y",3});
  []<std::size_t... I>(std::index_sequence<I...>) { compare("{0:>{139}}",int(I)...); }(std::make_index_sequence<140>{});
  std::string pattern(513,'x'); pattern+="{0}"; for(int i=0;i<32;++i) pattern+="{0}"; compare(pattern,123);
  std::uint64_t state=0x4d595df4d0f33173ull;
  for(unsigned i=0;i<4096;++i) {
    state^=state<<13; state^=state>>7; state^=state<<17;
    compare("{:#020x} {:#070b} {:o}",state,state,state); compare("{}",static_cast<std::int64_t>(state));
  }
  char out[32]; auto embedded=ffmt::format_to(out,"a\0{}",7);
  assert(embedded.written==3 && out[0]=='a' && out[1]==0 && out[2]=='7');
  auto large=ffmt::format_to_n(out,2,"{:100000}",7); assert(large && large.required==100000 && large.written==2);
  auto nullstring=ffmt::format_to_n(out,sizeof out,ffmt::runtime("{}"),static_cast<const char*>(nullptr));
  assert(nullstring.error==ffmt::format_error::invalid_format);
  for(const char* bad : {"{","}","{} {}","{0} {}","{0:!}","{99}","{999999999999999999999}"}) assert(!ffmt::format_to_n(out,sizeof out,ffmt::runtime(bad),42));
  auto negative=ffmt::format_to_n(out,sizeof out,ffmt::runtime("{:{}}"),42,-1);
  auto invalid=ffmt::format_to_n(out,sizeof out,ffmt::runtime("{:{}}"),42,1.5);
  assert(negative.error==ffmt::format_error::invalid_dynamic_spec && invalid.error==ffmt::format_error::invalid_dynamic_spec);
  wchar_t wide[32]; auto result=ffmt::format_to(wide,L"{} {:d}",'a','a');
  assert(result && std::wstring(wide,result.written)==L"a 97");
}''','#include "core_compare.hpp"\n')
emit('primitives','Format primitive values into bounded memory','The old print-only interface cannot safely target caller-owned memory or report the full required size.','format_to_n(buffer, 2, "{:04x}", 42); // stores "00", required=4','Builtin formatters share one parser and counted sink. Signs, base prefixes, padding and digits have separate output responsibilities.','Floating, Unicode display rules and customization protocols are introduced separately.',['include/ffmt/detail/integer.hpp','include/ffmt/detail/memory.hpp','include/ffmt/detail/execution.hpp','test/conformance/test_core_primitives.cpp'],['test_core_primitives'])
for n in ('dragonbox.hpp','exact_decimal.hpp'): detail(n)
for license_file in ('NOTICE','LICENSES/fmt.txt','LICENSES/dragonbox-Boost.txt'): put(license_file,orig(license_file))
(OUT/'conversion-move-proof.json').write_text(json.dumps({n:{'source_commit':'aeff043614725d58d383c8add086f548d77d05eb','source_file':'include/ffmt/base.hpp','body_sha256':hashlib.sha256(s.encode()).hexdigest()} for n,s in [('dragonbox.hpp',dragon),('exact_decimal.hpp',exact)]},indent=2)+'\n')
emit('conversion-preparation','Isolate the qualified decimal conversion helpers','The qualified conversion routines were embedded in the public base header.','// Existing handwritten bodies move into detail/dragonbox.hpp and detail/exact_decimal.hpp.','Bodies are copied unchanged from aeff043. Only namespace and OpenMP-region wrappers are added; extraction hashes are recorded.','The helpers are not activated until conversion integration. Handwritten logic remains explicitly handwritten.',['include/ffmt/detail/dragonbox.hpp','include/ffmt/detail/exact_decimal.hpp'],['test_core_primitives'],kind='mechanical-extraction')
fb=F['floating.hpp']; a=fb.index('  } else if constexpr (floating_traits<T>::precision == 53'); b=fb.index('  return p;',a); fb=fb[:a]+'  } else\n    p.supported = false;\n'+fb[b:]; detail('floating.hpp',fb)
INC[INC.index('text.hpp'):INC.index('text.hpp')]=['dragonbox.hpp','exact_decimal.hpp','floating.hpp']; checked(INC)
test('conversion',r'''template <typename T> void shortest_matches_oracle(T value) {
  const auto parts = ffmt::detail::split_binary(value);
  assert(parts.supported && parts.finite && !parts.negative);
  char output[64];
  const auto size = ffmt::detail::portable_shortest(output, value);
  assert(std::string(output, size) == fmt::format("{}", value));
}
void binary64_boundaries() {
  // Adjacent representations exercise asymmetric intervals at powers of two,
  // the largest subnormal, the first normals, and the largest finite values.
  constexpr std::uint64_t bits[] = {
    0, 1, 2, 3,
    0x000fffffffffffffull, 0x0010000000000000ull, 0x0010000000000001ull,
    0x3fdfffffffffffffull, 0x3fe0000000000000ull, 0x3fe0000000000001ull,
    0x3fefffffffffffffull, 0x3ff0000000000000ull, 0x3ff0000000000001ull,
    0x3fffffffffffffffull, 0x4000000000000000ull, 0x4000000000000001ull,
    0x433fffffffffffffull, 0x4340000000000000ull, 0x4340000000000001ull,
    0x7feffffffffffffeull, 0x7fefffffffffffffull
  };
  for (auto representation : bits)
    shortest_matches_oracle(__builtin_bit_cast(double, representation));
  for (double value : {9.999999999999998, 10.0, 10.000000000000002,
                       0.0001, 0.00001, 1e15, 1e16})
    shortest_matches_oracle(value);
}
void binary32_boundaries() {
  constexpr std::uint32_t bits[] = {
    0, 1, 2, 3,
    0x007fffffu, 0x00800000u, 0x00800001u,
    0x3effffffu, 0x3f000000u, 0x3f000001u,
    0x3f7fffffu, 0x3f800000u, 0x3f800001u,
    0x3fffffffu, 0x40000000u, 0x40000001u,
    0x4b7fffffu, 0x4b800000u, 0x4b800001u,
    0x7f7ffffeu, 0x7f7fffffu
  };
  for (auto representation : bits)
    shortest_matches_oracle(__builtin_bit_cast(float, representation));
  for (float value : {0.0001f, 0.00001f, 1e6f, 1e7f})
    shortest_matches_oracle(value);
}
void decimal_rounding_carries_and_ties() {
  struct rounding_case { double input; const char* digits; int exponent; };
  constexpr rounding_case cases[] = {{9.5,"1",1}, {2.5,"2",0}, {3.5,"4",0}};
  for (const auto& sample : cases) {
    ffmt::detail::precise_decimal<1100> value(ffmt::detail::split_binary(sample.input));
    value.round(1);
    assert(std::string(value.data,value.size)==sample.digits && value.exponent==sample.exponent);
  }
  ffmt::detail::precise_decimal<1100> exact(ffmt::detail::split_binary(0.125));
  assert(std::string(exact.data,exact.size)=="125" && exact.exponent==-1);
}
void classification_is_separate_from_magnitude_rendering() {
  const auto zero=ffmt::detail::split_binary(-0.0);
  assert(zero.zero() && zero.negative && zero.finite);
  const auto minimum=ffmt::detail::split_binary(std::numeric_limits<double>::denorm_min());
  assert(minimum.words[0]==1 && minimum.exponent==-1074);
  const auto infinity=ffmt::detail::split_binary(std::numeric_limits<double>::infinity());
  const auto nan=ffmt::detail::split_binary(std::numeric_limits<double>::quiet_NaN());
  assert(!infinity.finite && !infinity.nan && !nan.finite && nan.nan);
}
int main() {
  binary64_boundaries();
  binary32_boundaries();
  decimal_rounding_carries_and_ties();
  classification_is_separate_from_magnitude_rendering();
}''','#include <fmt/format.h>\n#include <cstdint>\n')
emit('floating-conversion','Convert binary floating values with bounded integer storage','Device environments cannot consistently provide host conversion services.','portable_shortest(buffer, std::numeric_limits<double>::denorm_min()); // "5e-324"','Representation bits drive classification and exact interval comparisons. Bounded integer limbs hold decimal expansions without output-capacity limits.','This uses more code than forwarding to libc, but avoids locale and allocation dependencies. Internal conversion accepts supported finite representations and renders their magnitude; callers handle signs and nonfinite spellings. Capacities 1100 and 16520 count decimal digits needed for exact supported IEEE values and interval endpoints, not requested output precision. Binary128 midpoint coefficients require fewer than 11570 digits, leaving conservative headroom. Direct oracle tests cover adjacent powers of two, subnormal/normal transitions, maximum finite values and notation transitions; decimal tests exercise rounding carry and ties.',['include/ffmt/detail/floating.hpp','test/conformance/test_core_conversion.cpp'],['test_core_conversion'])
nb=F['numeric.hpp'].replace('#include "extended.hpp"','').replace('    write_extended_float(ctx, arg, s);','    ctx.on_error(format_error::unsupported_type);'); detail('numeric.hpp',nb); detail('type_categories.hpp',F['type_categories.hpp'].replace(" || t == '?'",'').replace(" || (ch && t == '?')",''))
detail('value.hpp')
INC.insert(INC.index('text.hpp'),'numeric.hpp'); checked(INC)
test('floating',r'''int main() {
  compare("{:.180f}",0.125); compare("{:.2000f}",0.125); compare("{:.2000e}",0.125); compare("{:#.2000g}",0.125);
  compare("{:.0f} {:.0f} {:.0f} {:.0f}",0.5,1.5,2.5,9.5);
  compare("{} {}",std::numeric_limits<double>::min(),std::numeric_limits<double>::denorm_min());
  std::uint64_t state=0x4d595df4d0f33173ull;
  for(unsigned i=0;i<4096;++i) {
    state^=state<<13; state^=state>>7; state^=state<<17;
    auto d=__builtin_bit_cast(double,state); auto f=__builtin_bit_cast(float,static_cast<std::uint32_t>(state));
    compare("{}",d); compare("{}",f);
    for(const char* spec : {"{:.0f}","{:.6f}","{:.17g}","{:.5e}","{:#020.5a}"}) { compare(spec,d); compare(spec,f); }
  }
  char out[8]; auto huge=ffmt::format_to_n(out,2,"{:#.2147483647g}",0.125);
  assert(huge && huge.required==2147483649ull && huge.written==2);
}''','#include "core_compare.hpp"\n')
put('test/conformance/test_engine_fast_math.cpp',orig('test/conformance/test_engine_fast_math.cpp').replace('#include <ffmt/base.hpp>','#include <ffmt/detail/checked.hpp>'))
emit('floating-formatting','Format float and double with exact presentation rules','Floating fields need correct rounding even when requested precision exceeds stored output.','format_to_n(buffer, 2, "{:.2000f}", 0.125); // required=2002','Shortest formatting uses Dragonbox normally and integer interval conversion for fast-math and SPIR-V. Requested trailing zeros stream through counted sinks.','The oracle stays strictly compiled. Host fast-math tests use separately established expected strings and do not qualify device runtimes.',['include/ffmt/detail/numeric.hpp','test/conformance/test_core_floating.cpp','test/conformance/test_engine_fast_math.cpp'],['test_core_floating','test_engine_fast_math'])
ai=re.sub(r'#if defined\(__SIZEOF_FLOAT128__\).*?#endif\n','',args,flags=re.S).replace('static constexpr bool value = std::is_floating_point_v<T>;','static constexpr bool value = std::is_same_v<T,float> || std::is_same_v<T,double>;'); detail('arguments.hpp',dd(ai))
put('test/conformance/test_engine_bitint.cpp',orig('test/conformance/test_engine_bitint.cpp').replace('#include <ffmt/base.hpp>','#include <ffmt/detail/checked.hpp>'))
test('int128',r'''int main() {
#if defined(__SIZEOF_INT128__)
  using U=unsigned __int128; U value=(U(1)<<100)+42;
  compare("{} {:#x} {:#b}",value,value,value); compare("{}",-static_cast<__int128>(value));
#endif
}''','#include "core_compare.hpp"\n')
emit('extended-integers','Format native 128-bit and bit-precise integers','Standard type traits do not consistently recognize native extended integers.','using U = unsigned __int128;\nformat_to(buffer, "{:#x}", U(1) << 100);','Explicit signed and unsigned traits preserve the native width. _BitInt support follows the oracle surface through 64 bits.','Compiler extensions are conditional. Wider _BitInt values report unsupported rather than narrowing.',['include/ffmt/detail/arguments.hpp','test/conformance/test_core_int128.cpp','test/conformance/test_engine_bitint.cpp'],['test_core_int128','test_engine_bitint'])
for n in ('arguments.hpp','floating.hpp','extended.hpp','numeric.hpp'): detail(n)
for n in ('test_engine_extended.cpp','test_engine_quad.cpp'): put('test/conformance/'+n,orig('test/conformance/'+n).replace('#include <ffmt/base.hpp>','#include <ffmt/detail/checked.hpp>'))
emit('extended-floats','Preserve native long-double and binary128 representations','Passing extended values through double loses range and precision before formatting.','format_to(buffer, "{:.21g}", 1.234567890123456789L);','Native 80-bit and 128-bit decomposition feeds the same exact decimal algorithm. Formatting does not require quadmath conversion.','Layouts and availability are target dependent. Unsupported representations return a checked status.',['include/ffmt/detail/floating.hpp','include/ffmt/detail/extended.hpp','test/conformance/test_engine_extended.cpp','test/conformance/test_engine_quad.cpp'],['test_engine_extended','test_engine_quad'])
for n in ('unicode_width.hpp','unicode.hpp','parse.hpp','text.hpp'): detail(n)
detail('type_categories.hpp',categories_nofloat)
INC.insert(INC.index('parse.hpp'),'unicode_width.hpp'); unicode_inc=PRIMITIVE_INC.copy(); unicode_inc.insert(unicode_inc.index('parse.hpp'),'unicode_width.hpp'); checked(unicode_inc)
test('unicode',r'''int main() {
  compare("[{:.3}] [{:─^9}]","静夜思","é"); compare("{:?}","a\n\t\"\\\x7f"); compare("{:?}",'\n'); compare("{:.3?}","a\nb");
  compare("{:.2?}","界"); compare("{:.3?}","界"); compare("{:.4?}","界"); compare("{:.2?}","😀");
  std::uint32_t point; const char truncated[]={'\xf0','\x9f'};
  assert(ffmt::detail::decode_utf8(truncated,sizeof truncated,point)==1 && point==ffmt::detail::invalid_code_point);
}''','#include "core_compare.hpp"\n')
emit('unicode','Apply counted Unicode decoding and display rules','Byte counts alone misalign multibyte text, and decoding must respect counted boundaries.','format_to(buffer, "{:─^9}", "é");','Counted UTF-8 decoding, display-width tables and printability tables govern fill, alignment, precision and debug escapes. Wide output follows code-unit semantics.','These are qualified fmt semantics, not terminal-specific grapheme measurement. Unicode can still be disabled explicitly.',['include/ffmt/detail/parse.hpp','include/ffmt/detail/unicode_width.hpp','include/ffmt/detail/text.hpp','test/conformance/test_core_unicode.cpp'],['test_core_unicode'])
detail('context.hpp'); handoff('formatter-compatibility')
test('formatters',r'''struct parsed { int value; };
template <typename Char> struct ffmt::formatter<parsed,Char> : ffmt::formatter<int,Char> {
  template <typename Context> auto format(const parsed& value,Context& ctx) const { return ffmt::formatter<int,Char>::format(value.value,ctx); }
};
struct unsupported {};
static_assert(ffmt::has_formatter<int> && ffmt::has_formatter<parsed> && !ffmt::has_formatter<unsupported>);
int main() {
  char out[32]; auto result=ffmt::format_to(out,"{:04x}",parsed{42}); assert(result && std::string(out,result.written)=="002a");
}''')
emit('formatter-compatibility','Support parse/context formatters and correct forwarding','User-defined values need to consume specs and write into the caller context.','struct formatter<point> : formatter<int> { /* parse and format */ };','Eligibility checks inspect the cv-qualified reference accepted by format. Shared sink iterators preserve nested counts without copying user objects.','The protocol is template based with checked statuses; it does not provide exception services or type-erased stores.',['include/ffmt/detail/formatters.hpp','include/ffmt/detail/context.hpp','test/conformance/test_core_formatters.cpp','test/conformance/test_core_forwarding.cpp'],['test_core_formatters','test_core_forwarding','test_formatter_composition'])
ta=F['type_traits.hpp'].replace('template <typename T>\nconcept legacy_formatter = requires(T &x) { formatter<T>::format(x); };','template <typename T> inline constexpr bool legacy_formatter = false;'); detail('type_traits.hpp',ta)
test('format_as',r'''struct mapped { unsigned value; };
constexpr auto format_as(mapped value) { return value.value; }
static_assert(ffmt::has_formatter<mapped>);
int main() {
  char out[32]; auto result=ffmt::format_to(out,"{:#x}",mapped{42}); assert(result && std::string(out,result.written)=="0x2a");
  compare("{:>{}}",42,mapped{7}); auto width=ffmt::format_to(out,"{:>{}}",42,mapped{7});
  assert(width && std::string(out,width.written)=="     42");
}''','#include "core_compare.hpp"\n')
emit('format-as','Map user values through ADL format_as','Small wrappers should reuse primitive formatting without a full formatter specialization.','constexpr auto format_as(status value) { return value.code; }','ADL mapping participates in parsing, output and dynamic width validation. Values retain references until mapping occurs.','Mappings terminate at primitive representations; they are not a recursive serialization interface.',['include/ffmt/detail/type_traits.hpp','test/conformance/test_core_format_as.cpp'],['test_core_format_as'])
for n in ('type_traits.hpp','formatters.hpp','validation.hpp','execution.hpp'): detail(n)
handoff('legacy-compatibility')
test('legacy',r'''struct point { int x,y; };
template <> struct ffmt::formatter<point> {
  static constexpr auto format(point value) { return ffmt::formatted<ffmt::detail::fixed_string{"({1}, {0})"},int,int>{{value.x,value.y}}; }
};
static_assert(ffmt::has_formatter<point>);
int main() {
  char out[32]; auto result=ffmt::format_to(out,"{}",point{2,7}); assert(result && std::string(out,result.written)=="(7, 2)");
  wchar_t wide[32]; auto actual=ffmt::format_to(wide,L"{}",point{2,7});
  assert(actual && std::wstring(wide,actual.written)==L"(7, 2)");
}''','#include "core_compare.hpp"\n')
emit('legacy-compatibility','Adapt the existing static formatter protocol','Existing ffmt formatters return a literal and a tuple from static format functions.','static auto format(point p) { return formatted<"({}, {})", int, int>{{p.x, p.y}}; }','Legacy values expand through the counted engine. Narrow nested literals are converted for wide destinations without allocating.','Legacy custom formatters accept empty specs; modern parse/context formatters remain the spec-aware interface.',['include/ffmt/detail/execution.hpp','test/conformance/test_core_legacy.cpp','test/conformance/test_legacy_forwarding.cpp'],['test_core_legacy','test_legacy_forwarding'])
for n in ('legacy_emit.hpp','transport.hpp','print_macros.hpp'): detail(n)
detail('type_categories.hpp')
INC+=['legacy_emit.hpp','transport.hpp','print_macros.hpp']; checked(INC)
for n in ('test_engine_transport.cpp','test_engine_legacy_hook.cpp'): put('test/conformance/'+n,orig('test/conformance/'+n).replace('#include <ffmt/base.hpp>','#include <ffmt/detail/checked.hpp>'))
handoff('transport')
emit('transport','Deliver counted bytes through host and accelerator stdout','Long output and percent signs must reach stdout without reinterpretation as format syntax.','try_print("a{}b", char(0)); // counted chunk hooks preserve the NUL','A bounded sink emits counted chunks. Backend printf uses fixed conversion formats; compatibility hooks receive safe escaped pieces.','Some backend or legacy transports cannot preserve embedded NULs and report errors. Host captures validate contracts, not accelerator runtime behavior.',['include/ffmt/detail/transport.hpp','include/ffmt/detail/legacy_emit.hpp','test/conformance/test_engine_transport.cpp','test/conformance/test_engine_legacy_hook.cpp'],['test_engine_transport','test_engine_legacy_hook','test_transport_forwarding'])
(OUT/'family-output-hooks.hpp').write_text(F['output.hpp'])
detail('sycl_formatters.hpp')
put('include/ffmt/core.hpp','// Internal compatibility include. Applications include ffmt/base.hpp.\n#pragma once\n#include "detail/checked.hpp"\n')
put('include/ffmt/base.hpp','// Allocation-free formatting on hosts and accelerator devices.\n#pragma once\n#include "detail/checked.hpp"\n#include "detail/sycl_formatters.hpp"\n')
put('test/conformance/test_core_migration.cpp',r'''#ifdef NDEBUG
#undef NDEBUG
#endif
#include <ffmt/base.hpp>
#include <fmt/format.h>
#include <fmt/xchar.h>
#include <algorithm>
#include <cassert>
#include <string>
struct point { int x,y; };
template <> struct ffmt::formatter<point> {
  static constexpr auto format(point value) {
    return ffmt::formatted<ffmt::detail::fixed_string{"({1}, {0})"},int,int>{{value.x,value.y}};
  }
};
int main() {
  wchar_t wide[128];
  auto actual=ffmt::format_to(wide,L"[{:>8}] {:.3f} {}",L"静夜",1.25,point{2,7});
  auto expected=fmt::format(L"[{:>8}] {:.3f} ({}, {})",L"静夜",1.25,7,2);
  assert(actual && std::wstring(wide,actual.written)==expected);
}
''')
(OUT/'core-test-mapping.json').write_text(json.dumps({'test_engine.cpp':['test_core_primitives.cpp','test_core_floating.cpp','test_core_unicode.cpp','test_core_formatters.cpp','test_core_format_as.cpp','test_core_legacy.cpp','test_core_migration.cpp'],'test_engine_forwarding.cpp':['test_core_forwarding.cpp','test_legacy_forwarding.cpp','test_transport_forwarding.cpp','optional-feature forwarding tests owned by named/ranges stages'],'unchanged_native_suites':['test_engine_extended.cpp','test_engine_quad.cpp','test_engine_bitint.cpp','test_engine_fast_math.cpp','test_engine_transport.cpp','test_engine_legacy_hook.cpp'],'mixed_assertion':'The original wide string + float + legacy formatter composition assertion is retained at public migration so it does not introduce artificial feature dependencies.'},indent=2)+'\n')
emit('migration','Select the checked engine through the public header','The separately qualified engine must replace both old output paths while preserving API spellings.','#include <ffmt/base.hpp>\nauto result = ffmt::try_print("{:04x}", 42);','The public wrapper selects the same engine tested throughout this stack. Existing macros, static formatters and built-in SYCL formatters remain available.','Void compatibility calls discard checked status. Host checks do not replace preserved accelerator campaign evidence.',['include/ffmt/base.hpp','include/ffmt/detail/checked.hpp','include/ffmt/detail/sycl_formatters.hpp'],['legacy-host','core-all','test_core_migration','negative','fast-math'])
FILES.pop('include/ffmt/detail/legacy_base.hpp'); emit('obsolete-deletion','Delete the retired formatter implementation','The public header no longer references the old implementation after migration.','#include <ffmt/base.hpp> // unchanged for callers','Only the unused legacy implementation is deleted; archived snapshots retain it for comparison.','The static formatter protocol and legacy emit-hook adapter remain supported by the new implementation.',['include/ffmt/base.hpp'],['legacy-host','core-all'],kind='obsolete-code-deletion',remove=['include/ffmt/detail/legacy_base.hpp'])
for p,s in FILES.items():
 f=WORK/p; f.parent.mkdir(parents=True,exist_ok=True); f.write_text(s)
dependencies={
 'checked-config':['core-prepare'],'accounting':['checked-config'],'parsing':['accounting'],
 'primitives':['parsing'],'conversion-preparation':['primitives'],
 'floating-conversion':['conversion-preparation'],'floating-formatting':['floating-conversion'],
 'extended-integers':['primitives'],'extended-floats':['floating-formatting','extended-integers'],
 'unicode':['primitives'],'formatter-compatibility':['primitives'],
 'format-as':['formatter-compatibility'],'legacy-compatibility':['format-as'],
 'transport':['unicode','legacy-compatibility','floating-formatting'],
 'migration':['transport','extended-floats'],'obsolete-deletion':['migration']}
for id,parents in dependencies.items():
 path=OUT/id/'stage.json'; meta=json.loads(path.read_text()); meta['dependencies']=parents; path.write_text(json.dumps(meta,indent=2)+'\n')
(OUT/'index.json').write_text(json.dumps(STAGES,indent=2)+'\n'); print(json.dumps({'stages':STAGES,'files':len(FILES)},indent=2))
