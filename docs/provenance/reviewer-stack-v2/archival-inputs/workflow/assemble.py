#!/usr/bin/env python3
"""Assemble a local, unpublished review DAG from explicit stage snapshots.

No network writes occur here. A multi-prerequisite stage gets a merge-only base;
git must merge it cleanly, rather than silently choosing a sibling's files.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--worktree", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    repo, worktree = args.repo.resolve(), args.worktree.resolve()
    plan = json.loads(args.plan.read_text())
    stages = {s["id"]: s for s in plan["stages"]}
    if len(stages) != len(plan["stages"]):
        parser.error("duplicate stage IDs")
    ordered, visiting = [], set()

    def visit(name):
        if name not in stages:
            raise ValueError("missing prerequisite " + name)
        if name in visiting:
            raise ValueError("dependency cycle at " + name)
        stage = stages[name]
        if stage in ordered:
            return
        visiting.add(name)
        for prerequisite in stage.get("dependencies", []):
            visit(prerequisite)
        visiting.remove(name)
        ordered.append(stage)

    for stage in plan["stages"]:
        visit(stage["id"])
    if not args.apply:
        print(json.dumps([dict(id=s["id"], dependencies=s.get("dependencies", []))
                          for s in ordered], indent=2))
        return

    def git(*command, cwd=worktree):
        try:
            return subprocess.check_output(["git", "-C", str(cwd), *command], text=True).strip()
        except subprocess.CalledProcessError as error:
            if error.output:
                print(error.output, flush=True)
            raise

    if worktree.exists():
        if git("status", "--porcelain"):
            raise ValueError("assembly worktree has uncommitted changes")
    else:
        git("worktree", "add", "--detach", str(worktree), plan["base_commit"], cwd=repo)
    cache_path = args.index.with_suffix(".cache.json")
    previous = json.loads((cache_path if cache_path.exists() else args.index).read_text()) if (
        cache_path.exists() or args.index.exists()) else {}
    old_stages = {s["id"]: s for s in previous.get("stages", [])}
    old_bases = {s["stage"]: s for s in previous.get("assembly_bases", [])}
    result = dict(schema_version=2, base_commit=plan["base_commit"],
                  original_commit=plan["original_commit"], stages=[], assembly_bases=[])
    records = {}
    args.index.parent.mkdir(parents=True, exist_ok=True)

    def save():
        temporary = args.index.with_suffix(".tmp")
        temporary.write_text(json.dumps(result, indent=2) + "\n")
        temporary.replace(args.index)
        # A partial failed attempt must not discard reusable later snapshots.
        cache = dict(stages=list(old_stages.values()), assembly_bases=list(old_bases.values()))
        cache_temporary = cache_path.with_suffix(".tmp")
        cache_temporary.write_text(json.dumps(cache, indent=2) + "\n")
        cache_temporary.replace(cache_path)

    def path_for(relative):
        destination = (worktree / relative).resolve()
        if not destination.is_relative_to(worktree):
            raise ValueError("stage path escapes checkout: " + relative)
        return destination

    for stage in ordered:
        name = stage["id"]
        prerequisites = [records[x] for x in stage.get("dependencies", [])]
        # A prerequisite already contained in another head does not need a
        # redundant merge-only base. Keep logical dependencies in the index.
        prerequisites = [candidate for candidate in prerequisites if not any(
            other["commit"] != candidate["commit"] and subprocess.run(
                ["git", "-C", str(worktree), "merge-base", "--is-ancestor",
                 candidate["commit"], other["commit"]], capture_output=True).returncode == 0
            for other in prerequisites)]
        base = prerequisites[0]["commit"] if prerequisites else plan["base_commit"]
        base_branch = prerequisites[0]["branch"] if prerequisites else "main"
        git("switch", "--detach", base)
        if len(prerequisites) > 1:
            old_base = old_bases.get(name)
            if old_base and old_base["prerequisites"] == [x["commit"] for x in prerequisites]:
                git("switch", "--detach", old_base["commit"])
            else:
                for other in prerequisites[1:]:
                    if subprocess.run(["git", "-C", str(worktree), "merge-base", "--is-ancestor",
                                       other["commit"], "HEAD"], capture_output=True).returncode == 0:
                        continue
                    # Conflicts stop assembly for explicit review; never auto-select ours/theirs.
                    git("merge", "--no-ff", "--no-edit", other["commit"])
            base = git("rev-parse", "HEAD")
            base_branch = "review-v2/base-" + name
            git("branch", "-f", base_branch, base)
            result["assembly_bases"].append(dict(stage=name, branch=base_branch, commit=base,
                prerequisites=[x["commit"] for x in prerequisites], policy="clean git merges only"))
            old_bases[name] = result["assembly_bases"][-1]
        directory = Path(stage["directory"]).resolve()
        source = directory / "files"
        for relative_patch in stage.get("patches", []):
            patch = (directory / relative_patch).resolve()
            if not patch.is_relative_to(directory):
                raise ValueError("patch escapes stage directory")
            git("apply", "--check", str(patch))
            git("apply", str(patch))
        for old in stage.get("remove", []):
            target = path_for(old)
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
        changed = []
        if source.exists():
            for file in sorted(source.rglob("*")):
                if file.is_file():
                    relative = str(file.relative_to(source))
                    target = path_for(relative)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(file, target)
                    changed.append(relative)

        suites = []
        for relative in changed:
            path = Path(relative)
            if path.parent != Path("test/conformance") or not re.fullmatch(r"test_.+\.cpp", path.name):
                continue
            suite = path.stem.removeprefix("test_")
            standard = "c++23" if "std23" in suite else "c++20"
            flags = []
            if "fast_math" in suite:
                flags.append("-ffast-math")
            optional = bool(re.search(r"\breturn\s+77\b", path_for(relative).read_text()))
            # fmt is a separate object, never a dependency of the installed headers.
            reference = bool(re.search(r"#include\s*[<\"]fmt/", path_for(relative).read_text()))
            if not reference:
                for helper in re.findall(r'#include\s*"([^\"]+)"', path_for(relative).read_text()):
                    candidate = path_for(str(path.parent / helper))
                    if candidate.exists() and "fmt/" in candidate.read_text():
                        reference = True
            registration = worktree / "test/conformance/suites" / (suite + ".mk")
            registration.parent.mkdir(parents=True, exist_ok=True)
            registration.write_text(
                "FFMT_CAPABILITIES += " + suite + "\n" +
                "FFMT_SOURCE_" + suite + " := " + relative + "\n" +
                "FFMT_STANDARD_" + suite + " := " + standard + "\n" +
                ("FFMT_FLAGS_" + suite + " := " + " ".join(flags)).rstrip() + "\n" +
                "FFMT_REFERENCE_" + suite + " := " + str(int(reference)) + "\n" +
                "FFMT_OPTIONAL_" + suite + " := " + str(int(optional)) + "\n")
            suites.append(dict(name=suite, source=relative, standard=standard,
                               flags=flags, reference=reference,
                               optional=optional))
        for suite in stage.get("additional_suites", []):
            if any(item["name"] == suite["name"] for item in suites):
                raise ValueError("duplicate additional suite " + suite["name"])
            registration = path_for("test/conformance/suites/" + suite["name"] + ".mk")
            if not registration.is_file() or not path_for(suite["source"]).is_file():
                raise ValueError("additional suite requires its source and explicit registration")
            suites.append(suite)
        commands = []
        tests = stage.get("tests", [])
        tests = tests.get("commands", []) if isinstance(tests, dict) else tests
        for command in tests:
            if isinstance(command, list):
                commands.append(command)
            elif isinstance(command, str) and command.startswith("python3 "):
                commands.append(shlex.split(command))
        git("add", "-A")
        git("diff", "--cached", "--check")
        candidate_tree = git("write-tree")
        cached = old_stages.get(name)
        if cached and cached["base_commit"] == base and cached["tree"] == candidate_tree:
            # This scratch tree has just been proven identical to the old commit;
            # reuse it so extending a plan cannot invalidate earlier qualification.
            git("switch", "--detach", "--discard-changes", cached["commit"])
        else:
            git("commit", "--allow-empty", "-m", stage["title"])
        commit = git("rev-parse", "HEAD")
        branch = "review-v2/" + name
        git("branch", "-f", branch, commit)
        record = dict(stage, commit=commit, tree=git("rev-parse", "HEAD^{tree}"),
                      base_commit=base, base_branch=base_branch, branch=branch,
                      suites=suites, validation_commands=commands,
                      stage_files_sha256={str(file.relative_to(directory)): hashlib.sha256(file.read_bytes()).hexdigest()
                                          for file in sorted(directory.rglob("*")) if file.is_file()},
                      stage_input_sha256=hashlib.sha256((directory / "stage.json").read_bytes()).hexdigest())
        records[name] = record
        old_stages[name] = record
        result["stages"].append(record)
        save()
        print(name + " " + commit, flush=True)


if __name__ == "__main__":
    main()
