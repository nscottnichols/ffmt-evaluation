#!/usr/bin/env python3
"""Check local Markdown file destinations in an existing library checkout."""
import argparse
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("checkout", type=Path)
args = parser.parse_args()
root = args.checkout.resolve()
tracked = subprocess.check_output(["git", "-C", str(root), "ls-files", "*.md"], text=True).splitlines()
missing, checked = [], 0
for relative in tracked:
    file = root / relative
    text = re.sub(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$", "", file.read_text())
    text = re.sub(r"(`+).*?\1", "", text)
    for match in re.finditer(r"\[[^\]\n]*\]\(([^)\n]+)\)", text):
        target = match.group(1).split(' "', 1)[0].strip("<>")
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        path = unquote(parsed.path)
        destination = root / path.lstrip("/") if path.startswith("/") else file.parent / path
        checked += 1
        if not destination.exists():
            missing.append(f"{relative}: {target}")
if missing:
    raise SystemExit("Missing local Markdown destinations:\n" + "\n".join(missing))
print(f"Verified {checked} local destinations across {len(tracked)} tracked Markdown files.")
