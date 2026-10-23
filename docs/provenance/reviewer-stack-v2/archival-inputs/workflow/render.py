#!/usr/bin/env python3
"""Render review bodies from scoped stage notes and passing immutable evidence."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shlex

OVERVIEW = ("https://github.com/nscottnichols/ffmt-evaluation/blob/"
            "evaluation-campaign/docs/provenance/reviewer-stack-v2.md")
LIBRARY = "https://github.com/nscottnichols/ffmt"


def checks(row):
    for compiler in row.get("compilers", []):
        yield from compiler.get("steps", [])
    yield from row.get("commands", [])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path)
    parser.add_argument("--evidence", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    index = json.loads(args.index.read_text())
    qualified = {}
    for path in args.evidence:
        evidence = json.loads(path.read_text())
        for row in evidence["stages"]:
            if row["status"] in ("pass", "pass_with_skips"):
                qualified[(row["id"], row["commit"])] = (row, path, evidence)
    args.output.mkdir(parents=True, exist_ok=True)
    publication = dict(schema_version=2, github_repository="nscottnichols/ffmt", prs=[])
    for stage in index["stages"]:
        if stage.get("collection_only"):
            continue
        key = stage["id"], stage["commit"]
        if key not in qualified:
            raise ValueError("No passing immutable qualification for " + stage["id"])
        row, evidence_path, evidence = qualified[key]
        observed = list(checks(row))
        counts = Counter(item["status"] for item in observed)
        if counts["failure"]:
            raise ValueError("Contradictory qualification for " + stage["id"])
        draft = stage["wave"] != 1
        introduction = stage["problem"].rstrip(".") + ".\n\n"
        example = stage.get("example", "")
        if example:
            introduction += "For example:\n\n```text\n" + example.strip() + "\n```\n\n"
        design = stage["design"].rstrip(".") + ". " + stage["tradeoffs"].rstrip(".") + ".\n\n"
        reading = []
        for item in stage.get("reading_order", []):
            path, separator, symbol = item.partition(":")
            reading.append("- [" + path + "](" + LIBRARY + "/blob/" + stage["commit"] + "/" + path + ")"
                           + (" — " + symbol if separator else ""))
        read = "Read in this order:\n\n" + "\n".join(reading) + "\n\n" if reading else ""
        host = evidence.get("host", {})
        profiles = []
        for compiler in row.get("compilers", []):
            name = {"clang22": "Clang 22", "gcc13": "GCC 13"}.get(
                compiler["name"], compiler["name"])
            profiles.append(name + " at `-" + compiler["optimization"] + "`"
                            + (" with ASan/UBSan" if compiler.get("sanitizers") else ""))
        validation = ("Validated this exact commit on allocated CPU node `"
                      + host.get("name", "unknown") + "` (`"
                      + host.get("machine", "unknown") + "`). ")
        if profiles:
            validation += ("Header probes and affected C++ Make suites used "
                           + "; ".join(profiles) + ". ")
        validation += f"{counts['pass']} recorded steps passed"
        if counts["skip"]:
            validation += f"; {counts['skip']} optional capability checks returned 77 (unsupported)"
        if counts["not_applicable"]:
            validation += f"; {counts['not_applicable']} probes were inapplicable before their header existed"
        validation += ".\n\n"
        if any(item.get("reported_skips") for item in observed):
            validation += "A compound command also reported optional skips; their exact names and output remain in the evidence.\n\n"
        # The flags below describe the selected Make/header profile. Additional
        # drivers retain their own flags and environment in the evidence.
        selected = next(iter(row.get("compilers", [])), None)
        selected_environment = {}
        if selected:
            selected_environment = next((step["environment"] for step in selected.get("steps", [])
                                         if step.get("environment")), {})
        commands = []
        for command in stage.get("validation_commands", []):
            command = [part.replace("{cxx}", '"$CXX"').replace("{fmt_dir}", '"$FMT_DIR"')
                       .replace("{output}", '"$OUT"').replace("{source}", ".")
                       .replace("{repo}", '"$FFMT_CHECKOUT"').replace("{revision}", stage["commit"])
                       .replace("{python}", "python3") for part in command]
            # Display substitutions intentionally; evidence retains literal argv.
            commands.append(" ".join(part if "$" in part else shlex.quote(part) for part in command))
        suites = stage.get("suites", [])
        if suites:
            commands[:0] = ["make -j2 " + " ".join("build/cap_" + s["name"] for s in suites)
                            + ' CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT"'
                            + ' EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"',
                            "\n".join("./build/cap_" + s["name"] for s in suites)]
        if not commands:
            commands = ["printf '#include <ffmt/base.hpp>\\n' > base-header-probe.cpp",
                        '"$CXX" -std=c++20 "$HOST_OPT" -fno-fast-math -Wall -Werror'
                        ' -Iinclude $EXTRA_CXXFLAGS -c base-header-probe.cpp -o base-header-probe.o']
        if selected:
            commands[:0] = ["export CXX=" + shlex.quote(selected["executable"]),
                            "export HOST_OPT=" + shlex.quote("-" + selected["optimization"]),
                            "export EXTRA_CXXFLAGS=" + shlex.quote(
                                selected_environment.get("EXTRA_CXXFLAGS", ""))]
            for key in ("FFMT_FLAGS_HOST_BUFFER", "FFMT_FLAGS_HOST_SPECIFIERS"):
                if key in selected_environment and stage.get("validation_commands"):
                    commands.insert(3, "export " + key + "=" + shlex.quote(selected_environment[key]))
        validation += ("Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` "
                       "is the clean pinned oracle, `OUT` is a fresh evidence directory, and "
                       "`FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; "
                       "the evidence also retains the GCC probes and affected suites:\n\n```sh\n"
                       + "\n".join(commands) + "\n```\n\n")
        validation += ("The immutable evidence retains the complete argv, flags, header probes, raw logs, "
                       "source hashes and results. ASan/UBSan applies to the affected C++ Make suites "
                       "and header probes above. Standalone differential, benchmark, CMake and "
                       "compiler-rejection commands use their separately recorded flags; this "
                       "does not claim sanitizer coverage for every command. ")
        if stage["id"].startswith("tool-memory-") or stage["id"] in (
                "tool-cuda", "tool-hip", "tool-sycl", "tool-openmp", "tool-kokkos"):
            validation += ("These portable tests inspect adapter generation and launch contracts; "
                           "they do not qualify accelerator execution. ")
        if stage["id"].startswith("ci-"):
            validation += "Hosted workflow execution is not established by these local checks. "
        validation += ("This is representative host validation, not exhaustive fmt compatibility. "
                       "Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.\n\n")
        readiness = ("Ready for the first review wave." if not draft else
                     f"Draft review wave {stage['wave']}; it remains draft until prerequisite human review.")
        dependencies = stage.get("dependencies", [])
        footer = ("---\n" + readiness + "\n\nBase: [`" + stage["base_branch"] + "`]("
                  + LIBRARY + "/tree/" + stage["base_branch"] + "); "
                  + str(len(dependencies)) + " logical prerequisite"
                  + ("s" if len(dependencies) != 1 else "")
                  + ". [Stack overview, evidence and old→new snapshot mapping](" + OVERVIEW + ").\n")
        body = args.output / (stage["id"] + ".md")
        body.write_text(introduction + design + read + validation + footer)
        publication["prs"].append(dict(id=stage["id"], title=stage["title"],
            head=stage["branch"], base=stage["base_branch"], commit=stage["commit"],
            base_commit=stage["base_commit"], wave=stage["wave"], draft=draft, qualified=True,
            body_file=str(body.resolve()), body_sha256=hashlib.sha256(body.read_bytes()).hexdigest(),
            qualification_manifest=str(evidence_path), qualification_job=evidence["cobalt_jobid"],
            qualification_manifest_sha256=hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            result_counts=dict(counts)))
    (args.output / "publication.json").write_text(json.dumps(publication, indent=2) + "\n")


if __name__ == "__main__":
    main()
