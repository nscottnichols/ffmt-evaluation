from pathlib import Path
p=Path('/vast/projects/datascience/nnichols/ffmt_project/ffmt/artifacts/reviewer-v2/build_core_stages.py')
s=p.read_text()
s=s.replace('#include <fmt/format.h>\n#include <fmt/xchar.h>\n#include <cassert>', '#include <fmt/format.h>\n#include <fmt/xchar.h>\n#include <algorithm>\n#include <cassert>')
s=s.replace('    assert(bounded && bounded.required==expected.size() && bounded.written==bound);\n    assert(actual.substr(0,bound)==expected.substr(0,bound) && actual[bound]==\'~\');', '''    const auto retained = std::min(bound, expected.size());
    assert(bounded && bounded.required==expected.size() && bounded.written==retained);
    assert(actual.substr(0,retained)==expected.substr(0,retained));
    assert(actual[retained]=='~' && actual[bound]=='~');''')
s=s.replace('  compare("a{}b",char(0));', '  compare(""); compare("{}", std::string{});\n  compare("a{}b",char(0));')
a=s.index("test('conversion',r'''"); b=s.index("\nemit('floating-conversion'",a)
s=s[:a]+'''test('conversion',r\'''template <typename T> void shortest_matches_oracle(T value) {
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
  for (const auto& sample : {rounding_case{9.5,"1",1}, {2.5,"2",0}, {3.5,"4",0}}) {
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
}\''','#include <fmt/format.h>\\n#include <cstdint>\\n')'''+s[b:]
needle="FILES={}; PREVIOUS={}; STAGES=[]; D='include/ffmt/detail/'"
insert="""# Clarify internal conversion contracts without changing its algorithms.
F['floating.hpp']=F['floating.hpp'].replace('template <unsigned Capacity> struct precise_decimal {', '// Capacity counts decimal digits, not requested output precision. Callers\\n// provide enough storage for the complete exact finite magnitude and interval\\n// endpoints; the supported IEEE layouts have bounded exponent/significand sizes.\\ntemplate <unsigned Capacity> struct precise_decimal {')
F['floating.hpp']=F['floating.hpp'].replace('template <typename T> FMT_HD int portable_shortest(char *out, T value) {', '// Internal precondition: value has a supported finite representation. This\\n// renders the magnitude only; callers classify nonfinite values and emit signs.\\n// The output buffer must hold a shortest representation (64 bytes suffices for\\n// all supported formats). Decimal capacities conservatively cover exact binary64\\n// expansions and endpoints (1100), and native80/binary128 endpoints (16520).\\n// For binary128 the worst negative exponent is -16494; even after multiplying\\n// its <=113-bit significand by 5^16496 for midpoint endpoints, fewer than 11570\\n// decimal digits are needed. These bounds do not limit requested precision.\\ntemplate <typename T> FMT_HD int portable_shortest(char *out, T value) {')
"""
assert needle in s; s=s.replace(needle,insert+needle)
# Expand the permanent API/internal design note with assumptions and tests.
s=s.replace("'This uses more code than forwarding to libc, but avoids locale and allocation dependencies.'", "'This uses more code than forwarding to libc, but avoids locale and allocation dependencies. Internal conversion accepts supported finite representations and renders their magnitude; callers handle signs and nonfinite spellings. Capacities 1100 and 16520 count decimal digits needed for exact supported IEEE values and interval endpoints, not requested output precision. Binary128 midpoint coefficients require fewer than 11570 digits, leaving conservative headroom. Direct oracle tests cover adjacent powers of two, subnormal/normal transitions, maximum finite values and notation transitions; decimal tests exercise rounding carry and ties.'")
p.write_text(s)
