#!/usr/bin/env python3
"""Write the single stack overview from explicit immutable publication records."""
import argparse
import json
from pathlib import Path

LIB = "https://github.com/nscottnichols/ffmt"


def revision(value):
    return "[`" + value[:12] + "`](" + LIB + "/commit/" + value + ")"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path)
    parser.add_argument("--publication", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    index = json.loads(args.index.read_text())
    published = json.loads(args.publication.read_text())["prs"] if args.publication else []
    prs = {record["id"]: record for record in published}
    complete = next(stage for stage in index["stages"] if stage["id"] == "complete")
    rows = sorted((s for s in index["stages"] if not s.get("collection_only")),
                  key=lambda s: (s["wave"], list(index["stages"]).index(s)))
    ready = sum(not pr["draft"] for pr in published)
    text = f"""# Reviewer-oriented library stack

This replaces the seven unmerged library PRs #9–15 with {len(rows)} focused
review decisions. {ready if published else 4} PRs form the initial ready wave;
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
implementation decision. The final collection {revision(complete['commit'])}
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
"""
    for stage in rows:
        pr = prs.get(stage["id"], {})
        link = (f"[#{pr['number']}]({pr['url']})" if pr.get("number") else
                "[`" + stage["id"] + "`](" + LIB + "/tree/" + stage["branch"] + ")")
        dependencies = ", ".join("`" + name + "`" for name in stage.get("dependencies", [])) or "main"
        state = "ready" if stage["wave"] == 1 else "draft"
        if not published:
            state = "planned " + state
        text += f"| {stage['wave']} | {link} | {stage['title']} | {dependencies} | {revision(stage['commit'])} | {state} |\n"
    text += f"""
## Snapshot mapping and source changes

The original split snapshot `4b8cf257fc68c5b20c0c493e34d1d90269e76fd9` and the
former seven-part tip `aeff043614725d58d383c8add086f548d77d05eb` have the same
tree, `f3cc9d33e0443dc9f1e1a1941c19843401988b19`. That earlier split was history
only. Both remain available through `archive/library-portable-20261022` and
`archive/review-stack-v1-20261023` respectively. The v1 tip retains every former
stack head through ancestry. Original PR bodies/metadata are preserved in
[original-pr-metadata.json](reviewer-stack-v2/original-pr-metadata.json).

The new collection is {revision(complete['commit'])}, tree `{complete['tree']}`.
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
`qualified/20261022-{{baseline,primary,postfix,final}}` and
`archive/jlse-campaign-20261022` refs remain unchanged. The evaluation source and
runner pins remain `4b8cf257fc68c5b20c0c493e34d1d90269e76fd9`; fmt remains
`0fc31633e7d53ac895ae0a688b83b7d44f0b0c1f`. CPU requalification does not retag
historical measurements, and no GPU/Arm campaign is repeated for these source
reorganizations. The evaluation smoke uses the preserved pin independently.

The [review skill](../../skills/ffmt-review-stack/SKILL.md) and
[workflow scripts](../../tools/review_stack/README.md) describe reproduction and
publication. PR descriptions link here rather than duplicating the complete
stack and mapping.
"""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text)


if __name__ == "__main__":
    main()
