#include <ffmt/base.hpp>
#include <cstring>
int main() { char out[8] = {}; auto r = ffmt::format_to_n(out, sizeof out, "{:04x}", 42); return !r || r.written != 4 || r.required != 4 || std::memcmp(out, "002a", 4) != 0; }
