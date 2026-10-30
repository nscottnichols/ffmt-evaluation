#!/usr/bin/env python3
"""Verify clean assembly bases and absence of campaign additions in library history."""
import argparse
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("index", type=Path)
parser.add_argument("--repo", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
index = json.loads(args.index.read_text())


def git(*arguments):
    return subprocess.check_output(["git", "-C", str(args.repo), *arguments], text=True).strip()


proof = dict(schema_version=1, status="running", merge_replays=[], stages=[], source_additions=[])
verified = set()


def library_paths(paths):
    for path in paths:
        if path.startswith(("artifacts/", "software/", "platforms/", "skills/", "tools/jlse/",
                            "docs/results/", "docs/paper/", "docs/provenance/", "implementation_limitation/")):
            raise ValueError("campaign material added to library history: " + path)
    return paths
for base in index.get("assembly_bases", []):
    current, first = base["commit"], base["prerequisites"][0]
    while current != first:
        parents = git("show", "-s", "--format=%P", current).split()
        if len(parents) != 2:
            raise ValueError("unexpected assembly merge shape: " + current)
        if current not in verified:
            replay = git("merge-tree", "--write-tree", *parents).splitlines()[0]
            actual = git("rev-parse", current + "^{tree}")
            if replay != actual:
                raise ValueError("assembly base has non-mechanical resolution: " + current)
            proof["merge_replays"].append(dict(commit=current, parents=parents, tree=actual))
            verified.add(current)
        current = parents[0]
for stage in index["stages"]:
    parents = git("show", "-s", "--format=%P", stage["commit"]).split()
    if parents != [stage["base_commit"]]:
        raise ValueError("stage does not have exactly its recorded base parent: " + stage["id"])
    if stage.get("collection_only") and git("rev-parse", stage["commit"] + "^{tree}") != git(
            "rev-parse", stage["base_commit"] + "^{tree}"):
        raise ValueError("collection has a handwritten source delta")
    changed = library_paths(git("diff", "--name-only", "--diff-filter=AM",
                                stage["base_commit"], stage["commit"]).splitlines())
    proof["stages"].append(dict(id=stage["id"], commit=stage["commit"], parents=parents,
                                added_or_modified_paths=changed))
complete = next(stage for stage in index["stages"] if stage.get("collection_only"))
proof["source_additions"] = library_paths(git("diff", "--name-only", "--diff-filter=AM",
    index["base_commit"], complete["commit"]).splitlines())
proof["status"] = "pass"
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(proof, indent=2) + "\n")
print(f"Replayed {len(verified)} clean assembly merges; checked {len(proof['stages'])} single-decision parents.")
