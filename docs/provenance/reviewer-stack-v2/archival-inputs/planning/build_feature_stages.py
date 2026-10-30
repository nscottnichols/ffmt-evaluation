from pathlib import Path
import ast
import json
import re
import shutil
import subprocess

ROOT = Path('/vast/projects/datascience/nnichols/ffmt_project/ffmt/artifacts/reviewer-v2')
SRC = ROOT / 'feature-source'
OUT = ROOT / 'feature-stages'
ORIG = ROOT / 'feature-original'
ORIG.mkdir(exist_ok=True)
for filename in ['test_families.cpp', 'test_families_ranges.cpp', 'test_engine_forwarding.cpp', 'test_families_std23.cpp', 'test_families_printf.cpp']:
    target = ORIG / filename
    if not target.exists():
        shutil.copy2(SRC / 'test/conformance' / filename, target)

def put(path, text):
    p = SRC / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)

def lines(name, first, last):
    return ''.join((ORIG / name).read_text().splitlines(keepends=True)[first-1:last])

SUPPORT = r'''// Test-only differential helpers. Each suite includes only its own family headers.
#pragma once
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <ffmt/base.hpp>
#include <fmt/format.h>
#include <fmt/xchar.h>
#include <array>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <string_view>

namespace ffmt_test {
// Specialize only where the oracle exposes a different wrapper type, such as
// fmt::year versus std::chrono::year. Other suites need no calendar dependency.
template <typename T> struct oracle_argument {
  static const T& get(const T& value) { return value; }
};
template <typename T> decltype(auto) oracle_arg(const T& value) {
  return oracle_argument<T>::get(value);
}

class differential_suite {
  const char* name_;
  int comparisons_ = 0;
public:
  explicit differential_suite(const char* name) : name_(name) {}
  void record() { ++comparisons_; }
  void report() const {
    std::printf("%s: %d differential cases passed\n", name_, comparisons_);
  }
  template <typename... T>
  void equal_expected(std::string_view pattern, const std::string& expected,
                      const T&... args) {
    char buffer[16384];
    auto result = ffmt::format_to_n(buffer, sizeof(buffer), ffmt::runtime(pattern), args...);
    auto actual = std::string(buffer, result.written);
    if (result.error != ffmt::format_error::none || actual != expected ||
        result.required != expected.size()) {
      std::fprintf(stderr,
          "%s mismatch format=%.*s error=%d actual=%s expected=%s\n",
          name_, int(pattern.size()), pattern.data(), int(result.error),
          actual.c_str(), expected.c_str());
      std::abort();
    }
    record();
  }
  template <typename... T>
  void check(std::string_view pattern, const T&... args) {
    std::string expected;
    try {
      expected = fmt::format(fmt::runtime(pattern), oracle_arg(args)...);
    } catch (const fmt::format_error& error) {
      std::fprintf(stderr, "%s oracle rejected fixture format=%.*s: %s\n",
          name_, int(pattern.size()), pattern.data(), error.what());
      std::abort();
    }
    equal_expected(pattern, expected, args...);
  }
  template <typename... T>
  void check_wide(std::wstring_view pattern, const T&... args) {
    wchar_t buffer[2048];
    auto expected = fmt::format(fmt::runtime(pattern), oracle_arg(args)...);
    auto result = ffmt::format_to_n(buffer, std::size(buffer), ffmt::runtime(pattern), args...);
    assert(result.error == ffmt::format_error::none);
    assert(std::wstring(buffer, result.written) == expected);
    record();
  }
  template <typename... T>
  void reject(std::string_view pattern, const T&... args) {
    bool rejected = false;
    try { (void)fmt::format(fmt::runtime(pattern), oracle_arg(args)...); }
    catch (const fmt::format_error&) { rejected = true; }
    if (!rejected) {
      std::fprintf(stderr, "%s oracle accepted negative fixture format=%.*s\n",
          name_, int(pattern.size()), pattern.data());
      std::abort();
    }
    char buffer[1024];
    assert(ffmt::format_to_n(buffer, sizeof(buffer), ffmt::runtime(pattern), args...).error !=
           ffmt::format_error::none);
    record();
  }
};
} // namespace ffmt_test
'''
put('test/conformance/family_test_support.hpp', SUPPORT)

FAMILIES = 'test_families.cpp'
def family_group(function, first, last, prefix=''):
    body = lines(FAMILIES, first, last)
    for name in ['equal_expected', 'check_wide', 'check', 'reject']:
        body = re.sub(r'\b' + name + r'\(', 'suite.' + name + '(', body)
    body = body.replace('++count;', 'suite.record();')
    return f'void {function}() {{\n' + prefix + body + '}\n\n'

# Ordinary custom fixtures are local to the family using them; no family header
# is pulled in only to reuse another family's test fixture.
legacy_fixture = lines(FAMILIES, 29, 29) + lines(FAMILIES, 41, 51)
mapped_fixture = lines(FAMILIES, 52, 55)
range_fixtures = lines(FAMILIES, 31, 51) + mapped_fixture + lines(FAMILIES, 60, 60) + lines(FAMILIES, 68, 91)
RANGES_PREFIX = '''// Ranges, tuples and joins; independent of named, chrono, std and color adapters.
#define FMT_TUPLE_JOIN_SPECIFIERS 1
#include <ffmt/ranges.hpp>
#include <fmt/ranges.h>
#include "family_test_support.hpp"
#include <array>
#include <list>
#include <map>
#include <set>
#include <span>
#include <tuple>
#include <vector>
struct legacy_point { int x, y; };
'''
text = RANGES_PREFIX + range_fixtures + '\nnamespace {\nffmt_test::differential_suite suite("ranges");\n'
text += family_group('sequences_and_nested_specs',158,174,'  std::array<int, 3> numbers{1, -2, 33};\n')
text += family_group('associative_ranges_and_tuples',175,187)
text += family_group('string_range_customization',188,191)
text += family_group('join_views',192,196,'  std::array<int, 3> numbers{1, -2, 33};\n')
text += family_group('wide_ranges_and_tuples',293,294)
text += family_group('invalid_specs',297,301,'  std::array<int, 3> numbers{1, -2, 33};\n')
text += family_group('large_bounded_prefix',313,321)
text += '''} // namespace
int main() {
  sequences_and_nested_specs();
  associative_ranges_and_tuples();
  string_range_customization();
  join_views();
  wide_ranges_and_tuples();
  invalid_specs();
  large_bounded_prefix();
  suite.report();
}
'''
put('test/conformance/test_ranges.cpp',text)

STD_PREFIX='''// Standard-type adapters; independent of ranges, chrono, styling and names.
#include <ffmt/std.hpp>
#include <fmt/std.h>
#include "family_test_support.hpp"
struct unformattable {};
'''
text=STD_PREFIX + legacy_fixture + mapped_fixture + '\nnamespace {\nffmt_test::differential_suite suite("std");\n'
text += family_group('optional_and_variant',197,206)
text += family_group('bitsets_and_scalar_wrappers',207,220)
text += family_group('source_and_pointer_views',221,227,'  int ref = 42;\n')
text += family_group('complex_numbers',228,236)
text += family_group('invalid_specs',310,312)
text += '''} // namespace
int main() {
  static_assert(!ffmt::is_formattable<unformattable>);
  static_assert(!ffmt::is_formattable<std::variant<unformattable, int>>);
  static_assert(!fmt::is_formattable<std::variant<unformattable, int>>::value);
  optional_and_variant();
  bitsets_and_scalar_wrappers();
  source_and_pointer_views();
  complex_numbers();
  invalid_specs();
  suite.report();
}
'''
put('test/conformance/test_std.cpp',text)

text='''// Calendar oracle wrappers differ between fmt and the C++20 standard library.
#include <ffmt/chrono.hpp>
#include <fmt/chrono.h>
#include "family_test_support.hpp"
namespace ffmt_test {
'''
for typ,expr in [('year','fmt::year(int(value))'),('month','fmt::month(unsigned(value))'),('day','fmt::day(unsigned(value))'),('weekday','fmt::weekday(value.c_encoding())'),('year_month_day','fmt::year_month_day(fmt::year(int(value.year())), fmt::month(unsigned(value.month())), fmt::day(unsigned(value.day())))')]:
    text+=f'template <> struct oracle_argument<std::chrono::{typ}> {{\n  static auto get(std::chrono::{typ} value) {{ return {expr}; }}\n}};\n'
text+='''template <typename Duration>
struct oracle_argument<std::chrono::local_time<Duration>> {
  static auto get(std::chrono::local_time<Duration> value) {
    return fmt::local_time<Duration>(value.time_since_epoch());
  }
};
} // namespace ffmt_test
namespace {
ffmt_test::differential_suite suite("chrono");
'''
text+=family_group('duration_units_and_precision',246,265)
text+=family_group('calendar_and_time_points',266,282)
text+=family_group('tm_and_composite_tokens',283,292)
text+=family_group('wide_chrono',295,296)
text+=family_group('invalid_specs',302,309,'  std::tm tm{};\n')
text+='''} // namespace
int main() {
  duration_units_and_precision();
  calendar_and_time_points();
  tm_and_composite_tokens();
  wide_chrono();
  invalid_specs();
  suite.report();
}
'''
put('test/conformance/test_chrono.cpp',text)

text='''#include <ffmt/color.hpp>
#include <fmt/color.h>
#include "family_test_support.hpp"
namespace {
ffmt_test::differential_suite suite("style");
'''+family_group('explicit_ansi_styles',237,241)+'''} // namespace
int main() { explicit_ansi_styles(); suite.report(); }
'''
put('test/conformance/test_style.cpp',text)

# Shared family support gets direct tests rather than depending on a later
# range/chrono/std formatter merely to test its own alignment strategies.
put('test/conformance/test_family_support.cpp',r'''#ifdef NDEBUG
#undef NDEBUG
#endif
#include <ffmt/detail/family.hpp>
#include <array>
#include <cassert>
#include <iterator>
#include <string>

struct counted_body { int calls = 0; };
template <> struct ffmt::formatter<counted_body> {
  ffmt::detail::basic_format_spec<char> spec;
  constexpr auto parse(ffmt::format_parse_context& ctx) {
    return ffmt::detail::family_outer_specs(ctx, spec);
  }
  template <typename Context>
  auto format(counted_body& value, Context& ctx) const {
    return ffmt::detail::family_padded(ctx, spec, [&](auto& body) {
      ++value.calls;
      ffmt::detail::family_ascii(body, "body");
    }, false);
  }
};

void bounded_alignment_renders_once() {
  for (const char* pattern : {"{:*>8}", "{:*^9}", "{:*<8}"}) {
    const std::string expected = pattern[3] == '>' ? "****body" :
        pattern[3] == '^' ? "**body***" : "body****";
    for (std::size_t capacity = 0; capacity <= expected.size() + 1; ++capacity) {
      counted_body value;
      std::array<char, 32> output;
      output.fill('!');
      auto result = ffmt::format_to_n(output.data() + 1, capacity,
                                      ffmt::runtime(pattern), value);
      assert(result && result.required == expected.size());
      assert(result.written == std::min(capacity, expected.size()));
      assert(std::string(output.data() + 1, result.written) == expected.substr(0, capacity));
      assert(value.calls == 1);
      assert(output[0] == '!' && output[capacity + 1] == '!');
    }
  }
}
void single_pass_iterators_have_an_explicit_limit() {
  counted_body left;
  std::string output;
  auto result = ffmt::format_to(std::back_inserter(output), "{:*<8}", left);
  assert(result && output == "body****" && left.calls == 1);
  for (const char* pattern : {"{:*>8}", "{:*^9}"}) {
    counted_body value;
    output.clear();
    auto rejected = ffmt::format_to(std::back_inserter(output), ffmt::runtime(pattern), value);
    assert(rejected.error == ffmt::format_error::unsupported_type);
    assert(output.empty() && value.calls == 0);
  }
}
void display_column_counting() {
  ffmt::detail::family_counter<char> counter;
  for (char c : std::string("静é")) counter.push(c);
  assert(counter.size() == 3);
  counter.push(char(0xff));
  assert(counter.size() == 4);
  ffmt::detail::family_counter<wchar_t> wide;
  wide.push(L'静');
  assert(wide.size() == 1);
}
int main() {
  bounded_alignment_renders_once();
  single_pass_iterators_have_an_explicit_limit();
  display_column_counting();
}
''')

# Name tests are deliberately self-contained so the args branch needs no
# shared-family dependency merely to borrow an assertion helper.
put('test/conformance/test_named_arguments.cpp',r'''#ifdef NDEBUG
#undef NDEBUG
#endif
#include <ffmt/args.hpp>
#include <fmt/format.h>
#include <cassert>
#include <string>

struct counter {
  int value = 0;
  counter() = default;
  counter(const counter&) = delete;
  counter(counter&&) = delete;
};
template <> struct ffmt::formatter<counter> : ffmt::formatter<int> {
  template <typename Context> auto format(counter& value, Context& ctx) const {
    return ffmt::formatter<int>::format(++value.value, ctx);
  }
};
void names_resolve_fields_and_widths() {
  char output[128];
  auto result = ffmt::format_to_n(output, sizeof(output), "{value:04} {width}",
                                 ffmt::arg("value", 42), ffmt::arg("width", 7));
  auto expected = fmt::format("{value:04} {width}", fmt::arg("value", 42), fmt::arg("width", 7));
  assert(result && result.required == expected.size());
  assert(std::string(output, result.written) == expected);
  auto padded = ffmt::format_to_n(output, sizeof(output), "{value:>{width}}",
                                 ffmt::arg("value", 42), ffmt::arg("width", 7));
  expected = fmt::format("{value:>{width}}", fmt::arg("value", 42), fmt::arg("width", 7));
  assert(padded && std::string(output, padded.written) == expected);
}
void named_values_preserve_mutability_without_copying() {
  char output[32];
  counter value;
  auto named = ffmt::format_to(output, "{item}", ffmt::arg("item", value));
  assert(named && std::string(output, named.written) == "1" && value.value == 1);
  auto temporary = ffmt::format_to(output, "{item}", ffmt::arg("item", counter{}));
  assert(temporary && std::string(output, temporary.written) == "1");
}
int main() {
  names_resolve_fields_and_widths();
  named_values_preserve_mutability_without_copying();
}
''')
put('test/conformance/test_enum.cpp',r'''#ifdef NDEBUG
#undef NDEBUG
#endif
#include <ffmt/enum.hpp>
#include <fmt/std.h>
#include <cassert>
#include <string>
namespace enum_example {
using ffmt::enums::format_as;
enum class status : int { warning = -3, success = 42 };
}
int main() {
  char output[64];
  auto result = ffmt::format_to_n(output, sizeof(output), "{:+05}", enum_example::status::warning);
  auto expected = fmt::format("{:+05}", fmt::enums::format_as(enum_example::status::warning));
  assert(result && std::string(output, result.written) == expected);
  auto underlying = ffmt::format_to_n(output, sizeof(output), "{:#04x}",
                                      ffmt::underlying(enum_example::status::success));
  expected = fmt::format("{:#04x}", fmt::underlying(enum_example::status::success));
  assert(underlying && std::string(output, underlying.written) == expected);
}
''')

# Move existing iterator tests unchanged except for the named/range interaction.
text=(ORIG/'test_families_ranges.cpp').read_text()
text=text.replace('#include <ffmt/args.hpp>\n','')
start=text.index('  auto named = ffmt::format_to_n(')
end=text.index('  const auto& immutable',start)
text=text[:start]+text[end:]
put('test/conformance/test_ranges_iterators.cpp',text)

FORWARD='test_engine_forwarding.cpp'
# Core memory forwarding: each operation starts with a fresh value. This tests
# the operation rather than an incidental sequence of seven previous mutations.
common_counter=lines(FORWARD,13,24)
put('test/conformance/test_core_forwarding.cpp',r'''#ifdef NDEBUG
#undef NDEBUG
#endif
#include <ffmt/detail/checked.hpp>
#include <cassert>
#include <string>
'''+common_counter+r'''
static_assert(ffmt::is_formattable<counter>);
static_assert(!ffmt::is_formattable<const counter>);
void unbounded_memory_preserves_reference() {
  char output[32];
  counter value;
  auto result = ffmt::format_to(output, "{}", value);
  assert(result && std::string(output, result.written) == "1" && value.value == 1);
}
void bounded_memory_preserves_reference() {
  char output[32];
  counter value;
  auto result = ffmt::format_to_n(output, sizeof(output), ffmt::runtime("{}"), value);
  assert(result && std::string(output, result.written) == "1" && value.value == 1);
}
void size_query_and_temporary() {
  counter value;
  auto size = ffmt::formatted_size("{}", value);
  assert(size && size.required == 1 && value.value == 1);
  char output[32];
  auto temporary = ffmt::format_to(output, "{}", counter{});
  assert(temporary && std::string(output, temporary.written) == "1");
}
void const_value_is_rejected() {
  char output[32];
  const counter immutable;
  auto result = ffmt::format_to(output, ffmt::runtime("{}"), immutable);
  assert(result.error == ffmt::format_error::incompatible_type && result.written == 0);
#ifdef FFMT_TEST_CONST_REJECT
  ffmt::format_to(output, "{}", immutable);
#endif
}
int main() {
  unbounded_memory_preserves_reference();
  bounded_memory_preserves_reference();
  size_query_and_temporary();
  const_value_is_rejected();
}
''')
put('test/conformance/test_legacy_forwarding.cpp',r'''#ifdef NDEBUG
#undef NDEBUG
#endif
#include <ffmt/detail/checked.hpp>
#include <cassert>
#include <string>
'''+lines(FORWARD,42,50)+r'''
static_assert(ffmt::is_formattable<legacy_counter>);
static_assert(!ffmt::is_formattable<const legacy_counter>);
int main() {
  char output[32];
  legacy_counter value;
  auto result = ffmt::format_to(output, "{}", value);
  assert(result && value.value == 1 && std::string(output, result.written) == "1");
  const legacy_counter immutable;
  auto rejected = ffmt::format_to(output, ffmt::runtime("{}"), immutable);
  assert(rejected.error == ffmt::format_error::incompatible_type);
}
''')
put('test/conformance/test_transport_forwarding.cpp',r'''#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cstddef>
#include <string>
static std::string bytes;
static void capture(const char* data, std::size_t size) { bytes.append(data, size); }
#define FFMT_EMIT_CHUNK(data, size) capture(data, size)
#include <ffmt/detail/checked.hpp>
#include <cassert>
'''+common_counter+r'''
int main() {
  counter print_value;
  ffmt::print("{}", print_value);
  assert(bytes == "1" && print_value.value == 1);
  bytes.clear();
  counter checked_value;
  auto result = ffmt::try_print<"{}">(checked_value);
  assert(result && bytes == "1" && checked_value.value == 1);
  bytes.clear();
  counter line_value;
  ffmt::println("{}", line_value);
  assert(bytes == "1\n" && line_value.value == 1);
}
''')
# Ordinary nested formatter composition previously lived in the family omnibus.
put('test/conformance/test_formatter_composition.cpp',r'''#ifdef NDEBUG
#undef NDEBUG
#endif
#include <ffmt/detail/checked.hpp>
#include <cassert>
#include <string>
'''+lines(FAMILIES,61,67)+r'''
int main() {
  char output[64];
  auto result = ffmt::format_to_n(output, sizeof(output), "{}", named_value{"ordinary", 42});
  assert(result && result.required == 11);
  assert(std::string(output, result.written) == "ordinary=42");
}
''')

text=r'''#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <array>
#include <cstddef>
#include <string>
static std::string bytes;
static void capture(const char* data, std::size_t size) { bytes.append(data, size); }
#define FFMT_EMIT_CHUNK(data, size) capture(data, size)
#include <ffmt/ranges.hpp>
'''+common_counter+lines(FORWARD,25,41)+lines(FORWARD,55,70)+r'''
void const_elements_are_rejected() {
  static_assert(!ffmt::is_formattable<const std::array<counter, 2>>);
  char output[32];
  const std::array<counter, 2> values;
  auto result = ffmt::format_to(output, ffmt::runtime("{}"), values);
  assert(result.error == ffmt::format_error::incompatible_type && result.written == 0 && values[0].value == 0);
}
void bounded_padding_invokes_each_formatter_once() {
'''+lines(FORWARD,116,126)+r'''
}
void nested_padding_invokes_each_formatter_once() {
'''+lines(FORWARD,127,136)+r'''
}
void stream_padding_documents_replay_limit() {
'''+lines(FORWARD,137,146)+r'''
}
int main() {
  const_elements_are_rejected();
  bounded_padding_invokes_each_formatter_once();
  nested_padding_invokes_each_formatter_once();
  stream_padding_documents_replay_limit();
}
'''
put('test/conformance/test_ranges_forwarding.cpp',text)

# Cross-feature behavior alone joins the otherwise independent branches.
put('test/conformance/test_feature_integration.cpp',r'''#include <ffmt/args.hpp>
#include <ffmt/ranges.hpp>
#include <ffmt/std.hpp>
#include <fmt/ranges.h>
#include <fmt/std.h>
#include "family_test_support.hpp"
#include <array>
struct mutable_numbers {
  int* first;
  int* last;
  int* begin() { return first; }
  int* end() { return last; }
};
namespace {
ffmt_test::differential_suite suite("feature integration");
void named_range_width() {
  std::array<int, 3> numbers{1, -2, 33};
  suite.equal_expected("{values:*>{width}:03}",
      fmt::format("{values:*>{width}:03}", fmt::arg("values", numbers), fmt::arg("width", 25)),
      ffmt::arg("values", numbers), ffmt::arg("width", 25));
}
void named_complex_width() {
  auto value = std::complex<double>{1, -2.2};
  suite.equal_expected("{value:>{width}.2f}",
      fmt::format("{value:>{width}.2f}", fmt::arg("value", value), fmt::arg("width", 25)),
      ffmt::arg("value", value), ffmt::arg("width", 25));
}
void named_mutable_range() {
  int numbers[] = {1, -2, 33};
  mutable_numbers value{numbers, numbers + 3};
  std::array<char, 256> output;
  auto result = ffmt::format_to_n(output.data(), output.size(), "{items:*>20:03}", ffmt::arg("items", value));
  assert(result.error == ffmt::format_error::none);
  assert(std::string(output.data(), result.written) == fmt::format("{:*>20:03}", value));
  suite.record();
}
} // namespace
int main() { named_range_width(); named_complex_width(); named_mutable_range(); suite.report(); }
''')

# C++23 and typed printf retain all fixtures; only their file names and layout
# change. Named test groups in the printf suite are handled below.
put('test/conformance/test_std23.cpp',(ORIG/'test_families_std23.cpp').read_text())
put('test/conformance/test_printf.cpp',(ORIG/'test_families_printf.cpp').read_text())

# Clarify view lifetime and the three family padding strategies without changing
# the algorithm or storage model.
args=SRC/'include/ffmt/args.hpp'
s=args.read_text().replace('// Named arguments own their name view and refer to the supplied value.',
'''// Named arguments hold a name view and a reference to the supplied value.
// Neither the characters nor the value are copied. Keep both alive while the
// wrapper is used; a temporary value is safe within the formatting expression.''')
args.write_text(s)
fam=SRC/'include/ffmt/detail/family.hpp'
s=fam.read_text()
s=s.replace('  auto once = [&] {','''  // Render while measuring columns. This path never invokes a formatter twice.
  auto render_and_measure = [&] {''').replace('auto columns = once();','auto columns = render_and_measure();')
s=s.replace("  if (!spec.align || spec.align == '<') {",'''  // Left padding needs only the completed body width, so every iterator can
  // stream the body once and append its trailing padding.
  if (!spec.align || spec.align == '<') {''')
s=s.replace('  if constexpr (family_can_reorder<OutputIt>()) {','''  // A bounded writable buffer can insert leading padding after rendering. Its
  // accounting retains the full required size even when the stored prefix ends.
  if constexpr (family_can_reorder<OutputIt>()) {''')
s=s.replace('  } else {\n    if (!replayable)', '''  } else {
    // Other iterators cannot insert bytes before the body. Measure, then replay
    // only when the formatter and input explicitly permit a second traversal.
    if (!replayable)''')
fam.write_text(s)

# Per-feature fixture modules preserve original case IDs and handwritten C++
# expressions. No handwritten algorithm is relabelled as generated code.
original_cases=(SRC/'test/conformance/cases.py').read_text()
tree=ast.parse(original_cases)
case_calls={n.args[0].value:n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='case' and n.args and isinstance(n.args[0],ast.Constant)}
module_ids={
 'named':['named-fields'],
 'ranges':['range-nested-spec','tuple','join','bounded-family-padding','stream-left-family-padding'],
 'chrono':['chrono-duration','chrono-calendar'],
 'std':['optional','complex'],
 'style':['styled'],
 'printf':['printf-style'],
}
for module,ids in module_ids.items():
    module_text='"""Handwritten '+module+' fixtures introduced with their formatter implementation."""\nfrom case_support import case\n\n'
    if module=='ranges':
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id.startswith('_PADDING_') for t in node.targets):
                module_text+=ast.get_source_segment(original_cases,node)+'\n\n'
    module_text+='CASES = [\n'
    for case_id in ids:
        module_text+='    '+ast.get_source_segment(original_cases,case_calls[case_id])+',\n'
    module_text+=']\n'
    put(f'test/conformance/cases_{module}.py',module_text)

# Public docs describe the behavior at the stage that introduces it. The main
# README need only link each page as its PR lands; root owns that integration.
docs={
'named-arguments':('Named arguments','''#include <ffmt/args.hpp>
char out[16];
auto result = ffmt::format_to_n(out, sizeof out, "{value:04x}", ffmt::arg("value", 42));
// out contains "002a"; result.written == result.required == 4.''','''`ffmt::arg(name, value)` stores a name view and a value reference. The name
characters and value must outlive use of the wrapper; temporary values remain
valid through the formatting expression. Names and named width/precision fields
are resolved at runtime. Literal parsing checks structural syntax, but cannot
fully validate a named field's type/specification because names are runtime data.
Use checked results to observe unresolved names or incompatible specifications.'''),
'family-support':('Shared formatting-family support','''// Internal support, used by optional formatter headers:
return ffmt::detail::family_padded(ctx, spec, [&](auto& body) {
  ffmt::detail::family_ascii(body, "body");
}, /* replayable = */ false);''','''The internal helpers share outer alignment parsing, display-column accounting,
debug defaults and nested formatting. Left-aligned output renders once on any
iterator. Bounded writable pointer buffers also support right/center alignment
in one pass by inserting padding while retaining the exact truncated prefix.
Other iterators require replayable values for right/center alignment; unknown
custom formatters and consuming ranges return `unsupported_type` before invoking
the formatter. These helpers are implementation details, not a public extension
API. Optional formatters should document which input operations are device callable.'''),
'ranges':('Ranges, tuples and joins','''#include <ffmt/ranges.hpp>
std::array<int, 3> values{1, -2, 33};
ffmt::println("{::03}", values);  // [001, -02, 033]
ffmt::println("{:02x}", ffmt::join(values, ","));''','''Ranges select sequence, set, map, string or debug-string presentation. Tuples
and container adaptors have explicit adapters; nested specifications follow the
second colon, while `n` removes delimiters. `range_format_kind` customizes string
versus debug-string treatment. Joins hold iterator/delimiter views; keep their
underlying objects alive. Mutable and move-only input iterators are preserved.
Right/center alignment on streaming iterators requires repeatable element
formatters and forward ranges; bounded writable buffers handle consuming ranges
without replay. The standard-library operations used by the range must be
callable on the selected device.'''),
'chrono':('Locale-independent chrono formatting','''#include <ffmt/chrono.hpp>
ffmt::println("{:%T}", std::chrono::milliseconds{-123456}); // -00:02:03.456
ffmt::println("{:%G-W%V-%u}", std::chrono::year{2021}/1/1); // 2020-W53-5''','''The header supports durations, C++20 calendar values, `std::tm`, system time
points and local time points using civil-date arithmetic and explicit tokens.
Fractional precision, negative timestamps and ISO week years follow the pinned
fmt reference. This implementation provides locale-independent formatting; it
does not query clocks, a timezone database or locale services. Local time points
therefore reject zone/offset tokens. Device use requires the involved standard
chrono operations to be available on that device.'''),
'standard-types':('Standard-library type adapters','''#include <ffmt/std.hpp>
ffmt::println("{}", std::optional<int>{42});  // optional(42)
ffmt::println("{:.2f}", std::complex<double>{1, -2.2}); // (1.00-2.20i)''','''Optional and variant values use debug presentation for contained text; bitsets,
bytes, reference wrappers, atomics, complex numbers, source locations and pointer
views have explicit adapters. `ffmt::ptr` makes a raw/smart pointer printable
without dereferencing it. Atomic formatting loads the current value; a format
call is not an atomic snapshot across multiple arguments. These adapters do not
supply filesystem, streams, RTTI, thread-ID or exception-traversal services.
Standard-library types and their operations must themselves be device callable.'''),
'std23':('C++23 expected values','''#include <ffmt/std23.hpp>
ffmt::println("{}", std::expected<int, int>{42}); // expected(42)''','''`std23.hpp` adds `std::expected` and `std::unexpected` adapters when the selected
standard library exposes C++23 expected support. C++20 users can omit the header.
The contained value and error must be formattable. Optional tests report skip
(exit 77) when the standard library lacks the feature; that skip is not evidence
of conformance. Enable the suite with a C++23 compiler mode.'''),
'styling':('Explicit ANSI styling','''#include <ffmt/color.hpp>
ffmt::println("{}", ffmt::styled(42, ffmt::fg(ffmt::rgb(255,20,30)) | ffmt::emphasis::bold));''','''Styles explicitly emit ANSI escape bytes around the formatted value and reset
when a nonempty style ends. There is no terminal detection; captured output also
contains those bytes. RGB, terminal palette colors and emphasis flags compose
with `operator|`. Incompatible repeated terminal colors report `invalid_format`.
The wrapped formatter still owns ordinary value parsing and width semantics.'''),
'enums':('Enum underlying-value helpers','''#include <ffmt/enum.hpp>
namespace status_example {
using ffmt::enums::format_as;
enum class status : int { warning = -3 };
}
ffmt::println("{:+05}", status_example::status::warning); // -0003''','''`ffmt::underlying(value)` explicitly exposes an enum's underlying integer.
Opting into `ffmt::enums::format_as` in the enum's namespace enables ADL mapping
with the integer formatter's specifications. This prints integer values rather
than discovering symbolic names. The opt-in avoids globally making every enum
formattable.'''),
'printf':('Checked typed percent formatting','''#include <ffmt/printf.hpp>
char out[32];
auto result = ffmt::printf_to_n(out, sizeof out, "%#08x %.3f", 42u, 1.25);
// out contains "0x00002a 1.250".''','''The percent parser uses typed arguments rather than C varargs and shares the
bounded output/error contract of brace formatting. It supports positional
arguments, dynamic width/precision, integer length modifiers and narrow/wide
output. Invalid conversions report errors; `%n` is rejected and never writes
through a pointer. Floating arguments follow printf's float-to-double promotion.
This parser is intentionally separate from brace parsing so each grammar can be
reviewed and tested independently.'''),
'feature-integration':('Named arguments with optional families','''#include <ffmt/args.hpp>
#include <ffmt/ranges.hpp>
std::array<int, 3> values{1, -2, 33};
ffmt::println("{values:*>{width}:03}", ffmt::arg("values", values), ffmt::arg("width", 25));''','''Named argument wrappers preserve the referenced family's mutability and provide
runtime names for outer width fields. The interaction tests combine names with
ranges and standard-type adapters. Each family and named arguments also has an
independent test suite, so this integration adds no prerequisite between those
features.'''),
}
for name,(title,example,description) in docs.items():
    put(f'docs/features/{name}.md',f'# {title}\n\n```cpp\n{example}\n```\n\n{description}\n')

# Format handwritten source, not generated declarations. This improves newly
# introduced implementation readability while preserving C++ tokens except the
# documented family lambda rename and comments above.
fmt='/soft/compilers/llvm/release-22.1.8/bin/clang-format'
headers=['args.hpp','enum.hpp','detail/family.hpp','ranges.hpp','chrono.hpp','std.hpp','std23.hpp','color.hpp','printf.hpp']
new_tests=['family_test_support.hpp','test_family_support.cpp','test_named_arguments.cpp','test_enum.cpp','test_ranges.cpp','test_ranges_iterators.cpp','test_ranges_forwarding.cpp','test_chrono.cpp','test_std.cpp','test_std23.cpp','test_style.cpp','test_printf.cpp','test_feature_integration.cpp','test_core_forwarding.cpp','test_legacy_forwarding.cpp','test_transport_forwarding.cpp','test_formatter_composition.cpp']
subprocess.run([fmt,'-i',*[str(SRC/'include/ffmt'/h) for h in headers],*[str(SRC/'test/conformance'/t) for t in new_tests]],check=True)

stages=[
('named-arguments','Add referenced named arguments',['migration'],['args.hpp'],['named_arguments'],['named'],'named-arguments','Resolve human-readable field names while retaining typed value references.','Name lookup is runtime; wrappers do not allocate or own their referents.'),
('enum-helpers','Opt enums into integer formatting',['migration'],['enum.hpp'],['enum'],[],'enums','Expose enum underlying values without globally accepting every enum.','Small ADL opt-in shares the integer parser and avoids symbolic-name reflection.'),
('shared-family','Share nested output accounting and family alignment',['migration'],['detail/family.hpp'],['family_support'],[],'family-support','Optional formatters need consistent nested alignment without buffering or replaying mutations.','One pass on bounded writable destinations; explicit replay limit on streaming destinations.'),
('ranges','Format ranges, tuples and joins',['shared-family'],['ranges.hpp'],['ranges','ranges_iterators','ranges_forwarding'],['ranges'],'ranges','Format structured containers using element formatters while preserving iterator semantics.','Range detection and constrained formatter specializations; standard operations remain device-dependent.'),
('chrono','Format durations, calendar values and time points',['shared-family'],['chrono.hpp'],['chrono'],['chrono'],'chrono','Format chrono values without host locale, timezone-database or strftime services.','Civil-date arithmetic and explicit tokens preserve device callability; locale/timezone queries remain unsupported.'),
('standard-types','Adapt standard value wrappers and complex numbers',['shared-family'],['std.hpp'],['std'],['std'],'standard-types','Format common standard wrappers through existing contained-value formatters.','Explicit adapters avoid streams and RTTI; each standard operation must be available on the target.'),
('std23','Format C++23 expected and unexpected values',['standard-types'],['std23.hpp'],['std23'],[],'std23','Represent expected values and errors when the standard library supports C++23.','Separate opt-in header and skip semantics preserve C++20 portability.'),
('styling','Add explicit ANSI color and emphasis wrappers',['shared-family'],['color.hpp'],['style'],['style'],'styling','Request ANSI styling explicitly around an existing formattable value.','Typed composition emits deterministic bytes without terminal detection.'),
('typed-printf','Add checked typed percent formatting',['shared-family'],['printf.hpp'],['printf'],['printf'],'printf','Support percent formatting without unsafe C varargs or the writing conversion %n.','A separate typed grammar shares primitive conversion and bounded sinks, but does not implement %n.'),
('feature-integration','Test names with independent range and standard adapters',['named-arguments','ranges','standard-types'],[],['feature_integration'],[],'feature-integration','Verify cross-feature composition without making optional adapters depend on each other.','Integration-only fixtures sit above independent feature branches.'),
]

for id,title,deps,hs,suites,mods,doc,problem,design in stages:
    stage=OUT/id
    files=stage/'files'
    paths=[f'include/ffmt/{h}' for h in hs]+[f'test/conformance/test_{s}.cpp' for s in suites]+[f'test/conformance/cases_{m}.py' for m in mods]+[f'docs/features/{doc}.md']
    if id=='shared-family': paths+=['test/conformance/family_test_support.hpp']
    for path in paths:
        target=files/path
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(SRC/path,target)
    commands=[f'make build/focused_{s} CXX="$CXX" && ./build/focused_{s}' for s in suites]
    if id=='std23': commands=['make test-cxx23 CXX="$CXX" # compiler mode must be C++23; exit 77 is unsupported']
    record=dict(id=id,title=title,dependencies=deps,change_kind='feature' if id not in ['shared-family','feature-integration'] else 'preparatory-refactor' if id=='shared-family' else 'integration-tests',remove=[],tests=dict(suites=suites,commands=commands),problem=problem,example=docs[doc][1],design=design,tradeoffs=docs[doc][2],reading_order=[f'include/ffmt/{h}' for h in hs]+[f'test/conformance/test_{s}.cpp' for s in suites],docs=[f'docs/features/{doc}.md'],source_provenance=dict(snapshot='aeff043614725d58d383c8add086f548d77d05eb',source_changes='Header whitespace/comments, family padding lambda rename, and decomposed tests; no intended behavior change.'),minimal_wiring=dict(focused_suites=suites,fixture_modules=[f'cases_{m}.py' for m in mods]))
    (stage/'stage.json').write_text(json.dumps(record,indent=2)+'\n')

# Core-owner handoff fragments are not optional feature PRs.
for stage_id,suite in [('formatter-compatibility','core_forwarding'),('formatter-compatibility','formatter_composition'),('legacy-compatibility','legacy_forwarding'),('transport','transport_forwarding')]:
    target=OUT/'core-handoff'/stage_id/'files/test/conformance'/f'test_{suite}.cpp'
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(SRC/'test/conformance'/f'test_{suite}.cpp',target)
(OUT/'core-handoff/README.txt').write_text('Core test fragments extracted from old forwarding and omnibus families tests. No optional family dependencies. Include checked.hpp as requested by core owner. Add formatter_composition and core_forwarding to formatter-compatibility; legacy_forwarding to legacy-compatibility; transport_forwarding to transport.\n')
(OUT/'index.json').write_text(json.dumps([json.loads((OUT/s[0]/'stage.json').read_text()) for s in stages],indent=2)+'\n')
print(f'Exported {len(stages)} feature stages to {OUT}')
