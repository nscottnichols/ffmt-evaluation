#!/usr/bin/env python3
"""Publish an already qualified review DAG, preserving explicit readiness waves.

The input is a reviewed publication manifest, not an assembly plan. Bodies must
exist on disk and match recorded hashes. This script never merges a PR and never
changes an existing PR's readiness automatically. It can resume after interruption.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def verify_remote_refs(repo, repository, records):
    """Require the pushed PR inputs to match the qualified local snapshots."""
    output = subprocess.check_output(
        ["git", "-C", str(repo), "ls-remote", "--heads",
         "https://github.com/" + repository + ".git"], text=True)
    remote = dict((ref, commit) for commit, ref in
                  (line.split() for line in output.splitlines()))
    for record in records:
        for branch_key, commit_key in (("head", "commit"), ("base", "base_commit")):
            ref = "refs/heads/" + record[branch_key]
            if remote.get(ref) != record[commit_key]:
                raise ValueError("unqualified or missing remote " + branch_key + ": "
                                 + record["id"] + " (" + ref + ")")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    environment = dict(os.environ, GOMAXPROCS="2")
    repository = manifest["github_repository"]
    records = manifest["prs"]
    for record in records:
        body = Path(record["body_file"])
        if hashlib.sha256(body.read_bytes()).hexdigest() != record["body_sha256"]:
            raise ValueError("body changed: " + record["id"])
        commit = subprocess.check_output(
            ["git", "-C", str(args.repo), "rev-parse", record["head"]], text=True).strip()
        if commit != record["commit"] or record.get("qualified") is not True:
            raise ValueError("unqualified or moving head: " + record["id"])
        base = subprocess.check_output(
            ["git", "-C", str(args.repo), "rev-parse", record["base"]], text=True).strip()
        if base != record["base_commit"]:
            raise ValueError("moving base: " + record["id"])
    if not args.apply:
        print(json.dumps([dict(id=r["id"], head=r["head"], base=r["base"],
                              draft=r["draft"]) for r in records], indent=2))
        return

    # Read all remote refs once before the first GitHub write. A local branch
    # check cannot detect an omitted push or an independently moved remote.
    verify_remote_refs(args.repo, repository, records)

    def gh(*command):
        return subprocess.check_output(["gh", *command], text=True, env=environment).strip()

    existing = json.loads(gh("pr", "list", "--repo", repository, "--state", "open",
                             "--limit", "200", "--json", "number,url,headRefName,baseRefName,isDraft"))
    by_head = {pr["headRefName"]: pr for pr in existing}

    def save():
        temporary = args.manifest.with_suffix(".tmp")
        temporary.write_text(json.dumps(manifest, indent=2) + "\n")
        temporary.replace(args.manifest)

    for record in records:
        prior = by_head.get(record["head"])
        if prior:
            if prior["baseRefName"] != record["base"] or prior["isDraft"] != record["draft"]:
                raise ValueError("existing PR has different base/readiness: " + record["id"])
            gh("pr", "edit", str(prior["number"]), "--repo", repository,
               "--title", record["title"], "--body-file", record["body_file"])
            record.update(number=prior["number"], url=prior["url"])
        else:
            command = ["pr", "create", "--repo", repository, "--head", record["head"],
                       "--base", record["base"], "--title", record["title"],
                       "--body-file", record["body_file"]]
            if record["draft"]:
                command.append("--draft")
            url = gh(*command)
            record.update(number=int(url.rsplit("/", 1)[1]), url=url)
        save()
        print(record["id"] + " " + record["url"], flush=True)


if __name__ == "__main__":
    main()
