# Reviewer-oriented library stack

This replaces the seven unmerged library PRs #9–15 with 64 focused
review decisions. 4 PRs form the initial ready wave;
later waves remain draft until prerequisite human review. All PRs stay unmerged.
The library builds and runs its portable tests without this evaluation repository.

Read wave 1 first, then choose independent branches from their common prerequisite.
The core is introduced behind an internal checked header while the original public
implementation remains selected. Public migration follows its component tests;
obsolete implementation deletion is a separate decision. Named arguments and enum
helpers branch from migration; ranges, chrono, standard types, styling and typed
printf branch independently from shared family support. Combined test files are
replaced by focused sources; only real cross-feature tests join siblings.

Multi-prerequisite PRs use `review-v2/base-*` branches containing clean merges of
their prerequisite heads. These bases contain no handwritten resolution or hidden
implementation decision. The final collection [`471627c31cd1`](https://github.com/nscottnichols/ffmt/commit/471627c31cd1e09a2d4587c0369ec662251f7356)
has no PR because it adds no reviewable source delta. Do not merge the collection
or an archive ref in place of reviewing the component PRs. After prerequisite
review, refresh or retarget dependent PR bases against the reviewed heads before
merging; readiness is advanced deliberately, never automatically by publication.

## Review graph

Each row is one PR. Dependencies below are logical prerequisite stage IDs; the
actual GitHub base and full immutable hashes are in
[stage-index.json](reviewer-stack-v2/stage-index.json).

| Wave | PR | Review decision | Prerequisites | Revision | State |
| --- | --- | --- | --- | --- | --- |
| 1 | [`ci-review-waves`](https://github.com/nscottnichols/ffmt/tree/review-v2/ci-review-waves) | Run hosted compiler CI when a review wave becomes ready | main | [`0ed1cb08f13e`](https://github.com/nscottnichols/ffmt/commit/0ed1cb08f13eaeabfcba22ab078bed28a46eed5a) | planned ready |
| 1 | [`ci-resource-bounds`](https://github.com/nscottnichols/ffmt/tree/review-v2/ci-resource-bounds) | Bound template-build concurrency and cancel stale CI revisions | `ci-review-waves` | [`7974eb6762e6`](https://github.com/nscottnichols/ffmt/commit/7974eb6762e6a15d67afba53a32b19996e3926e8) | planned ready |
| 1 | [`oracle-pin`](https://github.com/nscottnichols/ffmt/tree/review-v2/oracle-pin) | Pin the shared fmt oracle to an immutable revision | `ci-resource-bounds` | [`4667a850a000`](https://github.com/nscottnichols/ffmt/commit/4667a850a000fae69a7fd6a04888ee41df908c2d) | planned ready |
| 1 | [`build-registration`](https://github.com/nscottnichols/ffmt/tree/review-v2/build-registration) | Register portable capability tests without silently omitting sources | `oracle-pin` | [`d1e8f0e8e1eb`](https://github.com/nscottnichols/ffmt/commit/d1e8f0e8e1eba7c47829d1d410362f8cc73041d1) | planned ready |
| 2 | [`coverage-metrics`](https://github.com/nscottnichols/ffmt/tree/review-v2/coverage-metrics) | Report source-file region, executable-line and branch coverage | `build-registration` | [`5739add3e1f0`](https://github.com/nscottnichols/ffmt/commit/5739add3e1f03dff8deca692a0a75675be2c806f) | planned draft |
| 2 | [`coverage-policy`](https://github.com/nscottnichols/ffmt/tree/review-v2/coverage-policy) | Replace the blocking coverage regression gate with reporting | `coverage-metrics` | [`465cc67d7769`](https://github.com/nscottnichols/ffmt/commit/465cc67d7769713b36e3789919edafb86a0c0d71) | planned draft |
| 2 | [`core-prepare`](https://github.com/nscottnichols/ffmt/tree/review-v2/core-prepare) | Preserve the existing implementation behind a wrapper | `build-registration` | [`99bc52ec4682`](https://github.com/nscottnichols/ffmt/commit/99bc52ec468208a16956aa19a5d1e00819ebfefe) | planned draft |
| 2 | [`checked-config`](https://github.com/nscottnichols/ffmt/tree/review-v2/checked-config) | Extract the qualified compiler configuration | `core-prepare` | [`954454c422b8`](https://github.com/nscottnichols/ffmt/commit/954454c422b816fd8296074cd7852dc923396f6c) | planned draft |
| 2 | [`accounting`](https://github.com/nscottnichols/ffmt/tree/review-v2/accounting) | Count bounded output independently of formatting | `checked-config` | [`5e9a2cc28f45`](https://github.com/nscottnichols/ffmt/commit/5e9a2cc28f453419f2555b49894ff347c80a8670) | planned draft |
| 2 | [`build-compiler-selection`](https://github.com/nscottnichols/ffmt/tree/review-v2/build-compiler-selection) | Resolve AdaptiveCpp through the caller environment | `build-registration` | [`91ebaec92fa7`](https://github.com/nscottnichols/ffmt/commit/91ebaec92fa783b997f07bebff0d19c9bfc56564) | planned draft |
| 2 | [`build-header-dependencies`](https://github.com/nscottnichols/ffmt/tree/review-v2/build-header-dependencies) | Rebuild legacy test objects after any library header edit | `build-registration` | [`9fa6e8fa26c1`](https://github.com/nscottnichols/ffmt/commit/9fa6e8fa26c13f78962ad4ff0447a60a3f5cafa5) | planned draft |
| 2 | [`local-ignores`](https://github.com/nscottnichols/ffmt/tree/review-v2/local-ignores) | Keep local outputs and installations untracked | `build-registration` | [`c90c80e02ea7`](https://github.com/nscottnichols/ffmt/commit/c90c80e02ea7e070211693d329a7aaed21f7c089) | planned draft |
| 3 | [`tool-process`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-process) | Capture exact subprocess bytes and terminate timed-out children | `build-registration` | [`575165ea7f16`](https://github.com/nscottnichols/ffmt/commit/575165ea7f1623a5b06b9d666a769676d3e21c07) | planned draft |
| 3 | [`tool-negative`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-negative) | Require intended diagnostics in negative compilation tests | `tool-process` | [`c5b81a4d5288`](https://github.com/nscottnichols/ffmt/commit/c5b81a4d5288e7be393d83ea28332510285b765e) | planned draft |
| 3 | [`tool-host-oracle`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-host-oracle) | Compare host output with an independently compiled fmt oracle | `tool-process` | [`4f2b6d380f3b`](https://github.com/nscottnichols/ffmt/commit/4f2b6d380f3b03e453bf0d80a7ab2d26ec480c46) | planned draft |
| 3 | [`parsing`](https://github.com/nscottnichols/ffmt/tree/review-v2/parsing) | Parse and validate counted format strings | `accounting` | [`11199fa8fd88`](https://github.com/nscottnichols/ffmt/commit/11199fa8fd88f5278e8d17040b9313dee604290b) | planned draft |
| 3 | [`primitives`](https://github.com/nscottnichols/ffmt/tree/review-v2/primitives) | Format primitive values into bounded memory | `parsing` | [`5d7e0af475a3`](https://github.com/nscottnichols/ffmt/commit/5d7e0af475a3da5b8217842a02998229f7dc8536) | planned draft |
| 4 | [`unicode`](https://github.com/nscottnichols/ffmt/tree/review-v2/unicode) | Apply counted Unicode decoding and display rules | `primitives` | [`e285726a33a1`](https://github.com/nscottnichols/ffmt/commit/e285726a33a1d1fc0e3870a6e58589f25cd53c83) | planned draft |
| 4 | [`conversion-preparation`](https://github.com/nscottnichols/ffmt/tree/review-v2/conversion-preparation) | Isolate the qualified decimal conversion helpers | `primitives` | [`543f6913b4ad`](https://github.com/nscottnichols/ffmt/commit/543f6913b4ada63547df28004d7ca0273b617f09) | planned draft |
| 4 | [`floating-conversion`](https://github.com/nscottnichols/ffmt/tree/review-v2/floating-conversion) | Convert binary floating values with bounded integer storage | `conversion-preparation` | [`dbd0b9f5fb1b`](https://github.com/nscottnichols/ffmt/commit/dbd0b9f5fb1bf00982317161abdc7c66aa85aa17) | planned draft |
| 4 | [`floating-formatting`](https://github.com/nscottnichols/ffmt/tree/review-v2/floating-formatting) | Format float and double with exact presentation rules | `floating-conversion` | [`509dbd5a28fc`](https://github.com/nscottnichols/ffmt/commit/509dbd5a28fcd0b8b549876a317c0a254cc4ccc8) | planned draft |
| 4 | [`extended-integers`](https://github.com/nscottnichols/ffmt/tree/review-v2/extended-integers) | Format native 128-bit and bit-precise integers | `primitives` | [`61c59c73c12b`](https://github.com/nscottnichols/ffmt/commit/61c59c73c12bfaa9f413b71cb40596c98e3961ef) | planned draft |
| 4 | [`extended-floats`](https://github.com/nscottnichols/ffmt/tree/review-v2/extended-floats) | Preserve native long-double and binary128 representations | `floating-formatting`, `extended-integers` | [`e44145c128c8`](https://github.com/nscottnichols/ffmt/commit/e44145c128c8cafcc061ada1de8553fcbb79e179) | planned draft |
| 5 | [`formatter-compatibility`](https://github.com/nscottnichols/ffmt/tree/review-v2/formatter-compatibility) | Support parse/context formatters and correct forwarding | `primitives` | [`7ee21c2a808b`](https://github.com/nscottnichols/ffmt/commit/7ee21c2a808b38744643cbeaad9517436f6281a2) | planned draft |
| 5 | [`format-as`](https://github.com/nscottnichols/ffmt/tree/review-v2/format-as) | Map user values through ADL format_as | `formatter-compatibility` | [`e3c863ca8ee6`](https://github.com/nscottnichols/ffmt/commit/e3c863ca8ee6e46a90b65d8e8b93c7789c67b240) | planned draft |
| 5 | [`legacy-compatibility`](https://github.com/nscottnichols/ffmt/tree/review-v2/legacy-compatibility) | Adapt the existing static formatter protocol | `format-as` | [`083601f4aca6`](https://github.com/nscottnichols/ffmt/commit/083601f4aca62444539571ae9eac03ddde1545a0) | planned draft |
| 5 | [`transport`](https://github.com/nscottnichols/ffmt/tree/review-v2/transport) | Deliver counted bytes through host and accelerator stdout | `unicode`, `legacy-compatibility`, `floating-formatting` | [`105c853df03e`](https://github.com/nscottnichols/ffmt/commit/105c853df03ef06ff29b6de819e78f6b23dd4dcb) | planned draft |
| 5 | [`tool-snapshots`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-snapshots) | Qualify immutable headers from an independent source checkout | `tool-host-oracle` | [`4436d6208ed9`](https://github.com/nscottnichols/ffmt/commit/4436d6208ed94795ee5ba9376aa76b0d00b5fe11) | planned draft |
| 5 | [`tool-isolation`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-isolation) | Preserve failed batches before isolating individual cases | `tool-snapshots`, `tool-negative` | [`1d0552f3961a`](https://github.com/nscottnichols/ffmt/commit/1d0552f3961a9a7cecf415b444c258e218f60e86) | planned draft |
| 5 | [`tool-oracle-negatives`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-oracle-negatives) | Compare invalid literal rejection against the independent oracle | `tool-isolation` | [`661db66d492a`](https://github.com/nscottnichols/ffmt/commit/661db66d492a18c308ae55358a59372bd7bf541e) | planned draft |
| 6 | [`migration`](https://github.com/nscottnichols/ffmt/tree/review-v2/migration) | Select the checked engine through the public header | `transport`, `extended-floats`, `tool-oracle-negatives` | [`f50f24930fb7`](https://github.com/nscottnichols/ffmt/commit/f50f24930fb7875c6381e16cbb5db50ddec1eb1e) | planned draft |
| 6 | [`obsolete-deletion`](https://github.com/nscottnichols/ffmt/tree/review-v2/obsolete-deletion) | Delete the retired formatter implementation | `migration` | [`cd7fcfd406ba`](https://github.com/nscottnichols/ffmt/commit/cd7fcfd406baf316271d8b88dc03f712fd157d6a) | planned draft |
| 7 | [`shared-family`](https://github.com/nscottnichols/ffmt/tree/review-v2/shared-family) | Share nested output accounting and family alignment | `migration` | [`c325e8408f51`](https://github.com/nscottnichols/ffmt/commit/c325e8408f512f38861f56983a7ec9b748290118) | planned draft |
| 7 | [`enum-helpers`](https://github.com/nscottnichols/ffmt/tree/review-v2/enum-helpers) | Opt enums into integer formatting | `migration` | [`bdcea2b2afb8`](https://github.com/nscottnichols/ffmt/commit/bdcea2b2afb856a364e14b7578af9e4199bb7745) | planned draft |
| 7 | [`named-arguments`](https://github.com/nscottnichols/ffmt/tree/review-v2/named-arguments) | Add referenced named arguments | `migration` | [`26f1a22c34b8`](https://github.com/nscottnichols/ffmt/commit/26f1a22c34b885d9b982a5856ae976ef8742510d) | planned draft |
| 7 | [`cmake-package`](https://github.com/nscottnichols/ffmt/tree/review-v2/cmake-package) | Install a header-only CMake interface target | `obsolete-deletion` | [`58472a3e12d6`](https://github.com/nscottnichols/ffmt/commit/58472a3e12d68fd7941be8998456916d1fffd412) | planned draft |
| 7 | [`ci-sanitizers`](https://github.com/nscottnichols/ffmt/tree/review-v2/ci-sanitizers) | Restore bool validation in the host sanitizer jobs | `migration`, `coverage-policy` | [`584253ca2c15`](https://github.com/nscottnichols/ffmt/commit/584253ca2c158308def053f80e2537d34e052120) | planned draft |
| 7 | [`reproducer-relocation`](https://github.com/nscottnichols/ffmt/tree/review-v2/reproducer-relocation) | Remove preserved independent compiler controls from the library | `build-registration` | [`36b45e924da8`](https://github.com/nscottnichols/ffmt/commit/36b45e924da8da7312408f6f948ff63f6ea22594) | planned draft |
| 7 | [`backend-regression-selection`](https://github.com/nscottnichols/ffmt/tree/review-v2/backend-regression-selection) | Exercise the migrated buffer cases in Intel backend builds | `migration` | [`baaea4967310`](https://github.com/nscottnichols/ffmt/commit/baaea496731052b4d53657b8498708a7848e0d80) | planned draft |
| 8 | [`chrono`](https://github.com/nscottnichols/ffmt/tree/review-v2/chrono) | Format durations, calendar values and time points | `shared-family` | [`862369f1856e`](https://github.com/nscottnichols/ffmt/commit/862369f1856e7174106cacace253671be59e7271) | planned draft |
| 8 | [`ranges`](https://github.com/nscottnichols/ffmt/tree/review-v2/ranges) | Format ranges, tuples and joins | `shared-family` | [`241df53a29ac`](https://github.com/nscottnichols/ffmt/commit/241df53a29ac8cf096aacd20542c87b33540c0bf) | planned draft |
| 8 | [`standard-types`](https://github.com/nscottnichols/ffmt/tree/review-v2/standard-types) | Adapt standard value wrappers and complex numbers | `shared-family` | [`98a1c1e67fba`](https://github.com/nscottnichols/ffmt/commit/98a1c1e67fba095bd678e0a1769a2ab89efa5084) | planned draft |
| 8 | [`styling`](https://github.com/nscottnichols/ffmt/tree/review-v2/styling) | Add explicit ANSI color and emphasis wrappers | `shared-family` | [`ad9f041e98a3`](https://github.com/nscottnichols/ffmt/commit/ad9f041e98a32f730a9bd5e4e47e2aa496b826fb) | planned draft |
| 8 | [`typed-printf`](https://github.com/nscottnichols/ffmt/tree/review-v2/typed-printf) | Add checked typed percent formatting | `shared-family` | [`aa36d84aaa2a`](https://github.com/nscottnichols/ffmt/commit/aa36d84aaa2a050e56fbca8d7df5085e92040e48) | planned draft |
| 9 | [`feature-integration`](https://github.com/nscottnichols/ffmt/tree/review-v2/feature-integration) | Test names with independent range and standard adapters | `named-arguments`, `ranges`, `standard-types` | [`dd407fc38b59`](https://github.com/nscottnichols/ffmt/commit/dd407fc38b596fcda23152a122f12bf69829c18d) | planned draft |
| 9 | [`std23`](https://github.com/nscottnichols/ffmt/tree/review-v2/std23) | Format C++23 expected and unexpected values | `standard-types` | [`3a07a5f9e3ae`](https://github.com/nscottnichols/ffmt/commit/3a07a5f9e3aebd120ffb193a0723ba409ee3cfe3) | planned draft |
| 10 | [`tool-adapter-support`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-adapter-support) | Share explicit compiler target selection between execution adapters | `tool-isolation` | [`160bd04b3657`](https://github.com/nscottnichols/ffmt/commit/160bd04b3657bf2d33167f342bb0b360429f3c0b) | planned draft |
| 10 | [`tool-cuda`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-cuda) | Add independent CUDA differential execution adapter | `tool-adapter-support` | [`fe65f6fcdc74`](https://github.com/nscottnichols/ffmt/commit/fe65f6fcdc7443a587986283387848303809eb1c) | planned draft |
| 10 | [`tool-hip`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-hip) | Add independent HIP differential execution adapter | `tool-adapter-support` | [`f50afd9c6852`](https://github.com/nscottnichols/ffmt/commit/f50afd9c6852f5d60d9eabdb45ff094281bab2b6) | planned draft |
| 10 | [`tool-kokkos`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-kokkos) | Add independent KOKKOS differential execution adapter | `tool-isolation` | [`8c25ab61e046`](https://github.com/nscottnichols/ffmt/commit/8c25ab61e046087f5330127cd479befcadbe8cb4) | planned draft |
| 10 | [`tool-openmp`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-openmp) | Add independent OPENMP differential execution adapter | `tool-adapter-support` | [`93f6cb1ff2af`](https://github.com/nscottnichols/ffmt/commit/93f6cb1ff2af9a3d0488dfd73a38c3e2eb8f1cfc) | planned draft |
| 10 | [`tool-sycl`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-sycl) | Add independent SYCL differential execution adapter | `tool-isolation` | [`d7aecfab035f`](https://github.com/nscottnichols/ffmt/commit/d7aecfab035ffe7ff0963149ae7f25745cc0b365) | planned draft |
| 11 | [`tool-numeric-memory`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-numeric-memory) | Compare bounded numeric memory records with host fmt output | `tool-oracle-negatives`, `migration` | [`d729ba7b56c0`](https://github.com/nscottnichols/ffmt/commit/d729ba7b56c07ec711eb9a24e9e91553f661a69a) | planned draft |
| 11 | [`tool-memory-cuda`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-memory-cuda) | Execute numeric memory records through the CUDA adapter | `tool-numeric-memory`, `tool-cuda` | [`17288fc322f0`](https://github.com/nscottnichols/ffmt/commit/17288fc322f07956b78999bf438f10b7f3a4086b) | planned draft |
| 11 | [`tool-memory-hip`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-memory-hip) | Execute numeric memory records through the HIP adapter | `tool-numeric-memory`, `tool-hip` | [`fd5eeb4d4be8`](https://github.com/nscottnichols/ffmt/commit/fd5eeb4d4be89c45c2765713d133c264a3c00687) | planned draft |
| 11 | [`tool-memory-kokkos`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-memory-kokkos) | Execute numeric memory records through the KOKKOS adapter | `tool-numeric-memory`, `tool-kokkos` | [`50540f30832e`](https://github.com/nscottnichols/ffmt/commit/50540f30832e14ee0a67ee5bfbed173ecb694c83) | planned draft |
| 11 | [`tool-memory-openmp`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-memory-openmp) | Execute numeric memory records through the OPENMP adapter | `tool-numeric-memory`, `tool-openmp` | [`a0d74e7370dd`](https://github.com/nscottnichols/ffmt/commit/a0d74e7370ddf6aa612fd5c368c0a86d46ae30f3) | planned draft |
| 11 | [`tool-memory-sycl`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-memory-sycl) | Execute numeric memory records through the SYCL adapter | `tool-numeric-memory`, `tool-sycl` | [`2ce97b23c175`](https://github.com/nscottnichols/ffmt/commit/2ce97b23c175321e92dc4b700d24927033911f88) | planned draft |
| 12 | [`benchmark-primitives`](https://github.com/nscottnichols/ffmt/tree/review-v2/benchmark-primitives) | Add explicit memory and printing benchmark primitives | `migration` | [`75353cc601c8`](https://github.com/nscottnichols/ffmt/commit/75353cc601c85b52dc066f724bfd4a56fbf37a6e) | planned draft |
| 12 | [`benchmark-driver`](https://github.com/nscottnichols/ffmt/tree/review-v2/benchmark-driver) | Verify benchmark output before collecting timing samples | `benchmark-primitives`, `tool-snapshots` | [`d50fe860d042`](https://github.com/nscottnichols/ffmt/commit/d50fe860d0424ceb002ab69cef6a9e5b4c65e83d) | planned draft |
| 12 | [`benchmark-resources`](https://github.com/nscottnichols/ffmt/tree/review-v2/benchmark-resources) | Retain compiler resource reports independently of timing measurements | `benchmark-driver` | [`cf70347b467f`](https://github.com/nscottnichols/ffmt/commit/cf70347b467f436447b41ea74a493e74cdc2a3e7) | planned draft |
| 13 | [`cmake-tests`](https://github.com/nscottnichols/ffmt/tree/review-v2/cmake-tests) | Register every split portable suite explicitly in CTest | `cmake-package`, `migration`, `named-arguments`, `ranges`, `chrono`, `standard-types`, `std23`, `styling`, `enum-helpers`, `typed-printf`, `feature-integration`, `tool-numeric-memory` | [`6498c0c38449`](https://github.com/nscottnichols/ffmt/commit/6498c0c38449019200b962f978ef3dbef0511003) | planned draft |
| 13 | [`ci-conformance`](https://github.com/nscottnichols/ffmt/tree/review-v2/ci-conformance) | Run and retain independent host corpus checks in ready CI | `ci-sanitizers`, `tool-numeric-memory`, `named-arguments`, `ranges`, `chrono`, `standard-types`, `std23`, `styling`, `enum-helpers`, `typed-printf`, `feature-integration` | [`493137b96467`](https://github.com/nscottnichols/ffmt/commit/493137b96467eaefe225f5c423dcc354db1dd4d4) | planned draft |
| 13 | [`api-index`](https://github.com/nscottnichols/ffmt/tree/review-v2/api-index) | Make library contracts and portable guides easy to navigate | `cmake-tests`, `ci-conformance`, `reproducer-relocation`, `benchmark-driver`, `tool-memory-cuda`, `tool-memory-hip`, `tool-memory-openmp`, `tool-memory-sycl`, `tool-memory-kokkos` | [`77df1adccd04`](https://github.com/nscottnichols/ffmt/commit/77df1adccd0448a46e73af6be2af9c5a2efbc1ee) | planned draft |

## Snapshot mapping and source changes

The original split snapshot `4b8cf257fc68c5b20c0c493e34d1d90269e76fd9` and the
former seven-part tip `aeff043614725d58d383c8add086f548d77d05eb` have the same
tree, `f3cc9d33e0443dc9f1e1a1941c19843401988b19`. That earlier split was history
only. Both remain available through `archive/library-portable-20261022` and
`archive/review-stack-v1-20261023` respectively. The v1 tip retains every former
stack head through ancestry. Original PR bodies/metadata are preserved in
[original-pr-metadata.json](reviewer-stack-v2/original-pr-metadata.json).

The new collection is [`471627c31cd1`](https://github.com/nscottnichols/ffmt/commit/471627c31cd1e09a2d4587c0369ec662251f7356), tree `b2be548c7571f009bdcab254c4434b4ca240ebcd`.
This tree differs from the qualified snapshot. This restructuring includes source,
test, build and documentation changes; new commit IDs are not presented as a new
qualification of historical measurements. Exact stage inputs, tree IDs, merge
parents, old intermediate attempts and per-file hashes are recorded alongside
[the source review](reviewer-stack-v2/audits/final-source-review.json) and
[the final release preservation audit](reviewer-stack-v2/release-source-audit/release-source-preservation.json).
The [snapshot mapping](reviewer-stack-v2/snapshot-mapping.json) records every
old-to-new attempted stage, including failed revisions.

| Former PR/head | Replacement review areas |
| --- | --- |
| [#10](https://github.com/nscottnichols/ffmt/pull/10), `3845e997e481c7f3a29b472d7f5edb331ba708b6` | Process evidence, diagnostics, independent oracle, snapshots, isolation, backend adapters, numeric memory, coverage metrics/policy |
| [#11](https://github.com/nscottnichols/ffmt/pull/11), `2f7508c4fa2a2032eb9d7ce77a3d687ac34bb557` | Mechanical preparation, accounting, parsing, primitives, conversion, float presentation, extended types, Unicode, modern/ADL/legacy customization, transport, migration and deletion; named arguments separately |
| [#12](https://github.com/nscottnichols/ffmt/pull/12), `3e5ae22ba1a3dd84cd4dc539eb67e788bec69dfd` | Shared family support, ranges, iterator/forwarding tests, genuine feature integration |
| [#13](https://github.com/nscottnichols/ffmt/pull/13), `7bccd77f4bf5517c6657c7960b73c40802c42620` | Chrono, standard types, C++23 opt-in, enum helpers and styling |
| [#14](https://github.com/nscottnichols/ffmt/pull/14), `745088a005daea7abc9414916d4accb384c17bc3` | Typed printf and its own tests/docs |
| [#15](https://github.com/nscottnichols/ffmt/pull/15), `159fdf2a4ca1378ed38cf4c79dbddc5aba3a6f63` | Benchmark primitives, verified driver and resource capture |
| [#9](https://github.com/nscottnichols/ffmt/pull/9), `aeff043614725d58d383c8add086f548d77d05eb` | CMake package/testing, CI, API navigation, focused Make portability repairs and independent reproducer removal |

Mechanical preparation preserves the original public implementation bytes;
conversion-helper moves preserve their bodies and attribution. Recorded EOF
normalization is separate. Core headers are factored into reviewable capabilities;
optional headers and launcher code receive readability edits. No arithmetic
algorithm change is intended, and sampled oracle agreement is not a proof of
universal equivalence. The exact 54 positive fixture dictionaries, ordered nine
negative fixtures and all 26 original Python regression bodies are preserved.
The eight qualified legacy regression files are restored byte for byte, including
full untruncated oracle output, shortest float comparisons, null rejection and raw
stream equality. New tests strengthen empty output, conversion boundaries,
named errors and replayable family alignment. Optional compiler types return 77;
C++23 remains opt-in in both Make and CMake.

The coverage-policy PR **replaces a blocking percentage regression gate with
reporting**. Moving headers and changing template instantiation change the
denominator, so percentage drops need per-file review. Invalid/empty measurement
still fails, while genuine percentage regressions can now pass CI: automatic
nondecreasing-coverage protection is deliberately lost. Correctness and sanitizer
checks remain separate blocking checks.

## Validation and preserved evidence

The [validation records](reviewer-stack-v2/validation-summary.json) select only
passing evidence for the exact published stage commits. CPU qualification uses
separate Clang 22 and GCC 13 worktrees, header probes, affected capability suites,
Python regressions and relevant driver smokes. Clang header/Make checks enable
strict ASan/UBSan; standalone commands retain their own recorded flags. Migration
and collection run all registered suites and legacy host checks. CMake testing,
installation and an independent consumer are explicit checks. Optional skips,
not-applicable probes and cancelled jobs remain distinct from passes. Hosted CI
execution and accelerator execution are not established by CPU checks.

Earlier attempts exposed dropped legacy fixtures; their failures and cancelled
follow-up allocation remain recorded, with corrections and new revisions. Raw
commands, stdout/stderr, captured generated sources, hashes and scheduler receipts
are preserved losslessly. Handwritten headers, tests, scripts and C++ templates
remain visible in their repositories. Archive refs named
`archive/review-v2-attempt-20261023/*` retain the earlier attempted intermediate
commits, including failed ones; their presence does not assert conformance.

Historical hardware evidence, failures, source hashes, paper selections and local
installations remain intact in ffmt-evaluation. Existing
`qualified/20261022-{baseline,primary,postfix,final}` and
`archive/jlse-campaign-20261022` refs remain unchanged. The evaluation source and
runner pins remain `4b8cf257fc68c5b20c0c493e34d1d90269e76fd9`; fmt remains
`0fc31633e7d53ac895ae0a688b83b7d44f0b0c1f`. CPU requalification does not retag
historical measurements, and no GPU/Arm campaign is repeated for these source
reorganizations. The evaluation smoke uses the preserved pin independently.

The [review skill](../../skills/ffmt-review-stack/SKILL.md) and
[workflow scripts](../../tools/review_stack/README.md) describe reproduction and
publication. PR descriptions link here rather than duplicating the complete
stack and mapping.
