"""Historical source equivalence must not require changing a live checkout."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import verify_provenance as provenance


class HistoricalLibraryTests(unittest.TestCase):
    def git(self, checkout, *arguments):
        return subprocess.check_output(["git", "-C", str(checkout), *arguments],
                                       stderr=subprocess.PIPE, text=True).strip()

    def commit(self, checkout, message):
        self.git(checkout, "add", ".")
        self.git(checkout, "-c", "user.name=ffmt test", "-c", "user.email=test@example.invalid",
                 "-c", "core.hooksPath=/dev/null", "commit", "--quiet", "--no-gpg-sign", "-m", message)
        return self.git(checkout, "rev-parse", "HEAD")

    def fixture(self, root, *, history):
        checkout = root / "library"
        header = checkout / "include/ffmt/base.hpp"
        corpus = checkout / "test/conformance/cases.py"
        for path, text in ((header, "qualified header\n"), (corpus, "CASES = ['qualified']\n")):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        headers = {"include/ffmt/base.hpp": provenance.digest(header)}
        ledger = root / "split.json"
        ledger.write_text(json.dumps(dict(
            schema_version=1, preserved_evidence=[], preserved_campaign_configuration=[], qualified_snapshots=[],
            source_equivalence=dict(header_files=headers,
                canonical_header_sha256=provenance.canonical_digest(headers),
                corpus=dict(path="test/conformance/cases.py", sha256=provenance.digest(corpus))))))
        if history:
            self.git(checkout, "init", "--quiet", "--template=")
            revision = self.commit(checkout, "qualified source")
        else:
            revision = None
        return checkout, header, corpus, ledger, revision

    def verify(self, checkout, ledger, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = provenance.main(["--ffmt-checkout", str(checkout), "--manifest", str(ledger), *arguments])
        return result, stdout.getvalue(), stderr.getvalue()

    def test_historical_headers_and_corpus_pass_while_head_and_worktree_differ(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkout, header, corpus, ledger, qualified = self.fixture(Path(temporary), history=True)
            header.write_text("new committed header\n")
            corpus.write_text("CASES = ['new HEAD']\n")
            extra = checkout / "include/ffmt/new.hpp"
            extra.write_text("new committed header inventory\n")
            head = self.commit(checkout, "different source")
            header.write_text("keep this uncommitted header edit\n")
            untracked = checkout / "keep-untracked.txt"
            untracked.write_text("keep this untracked input\n")
            status = self.git(checkout, "status", "--porcelain")
            index = (checkout / ".git/index").read_bytes()
            contents = {path.relative_to(checkout): path.read_bytes() for path in checkout.rglob("*")
                        if path.is_file() and ".git" not in path.relative_to(checkout).parts}

            result, stdout, stderr = self.verify(checkout, ledger, "--library-revision", qualified)
            self.assertEqual(result, 0, stderr)
            self.assertIn(qualified + " (local Git objects)", stdout)
            self.assertEqual(self.verify(checkout, ledger)[0], 1)
            self.assertEqual(self.verify(checkout, ledger, "--library-revision", head)[0], 1)
            self.assertEqual(self.git(checkout, "rev-parse", "HEAD"), head)
            self.assertEqual((checkout / ".git/index").read_bytes(), index)
            self.assertEqual({path: (checkout / path).read_bytes() for path in contents}, contents)
            self.assertEqual(self.git(checkout, "status", "--porcelain"), status)

    def test_default_worktree_verification_needs_no_git_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkout, header, _, ledger, _ = self.fixture(Path(temporary), history=False)
            result, stdout, stderr = self.verify(checkout, ledger)
            self.assertEqual(result, 0, stderr)
            self.assertIn("WORKTREE " + str(checkout), stdout)
            header.write_text("changed live source\n")
            self.assertEqual(self.verify(checkout, ledger)[0], 1)
            self.assertFalse((checkout / ".git").exists())

    def test_mutable_and_abbreviated_revisions_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkout, _, _, ledger, qualified = self.fixture(Path(temporary), history=True)
            for revision in ("HEAD", "main", "WORKTREE", qualified[:12], "g" * 40, qualified + "^{commit}"):
                with self.subTest(revision=revision), contextlib.redirect_stderr(io.StringIO()), \
                        self.assertRaises(SystemExit) as error:
                    self.verify(checkout, ledger, "--library-revision", revision)
                self.assertEqual(error.exception.code, 2)

    def test_missing_commit_and_tag_object_are_not_silently_substituted(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkout, _, _, ledger, qualified = self.fixture(Path(temporary), history=True)
            result, _, stderr = self.verify(checkout, ledger, "--library-revision", "f" * 40)
            self.assertEqual(result, 1)
            self.assertIn("Cannot inspect pinned library revision", stderr)
            self.git(checkout, "-c", "user.name=ffmt test", "-c", "user.email=test@example.invalid",
                     "tag", "--no-sign", "-a", "qualification", "-m", "tag fixture", qualified)
            tag_object = self.git(checkout, "rev-parse", "qualification")
            result, _, stderr = self.verify(checkout, ledger, "--library-revision", tag_object)
            self.assertEqual(result, 1)
            self.assertIn("must identify a commit object directly", stderr)
            self.assertEqual(self.git(checkout, "rev-parse", "HEAD"), qualified)


if __name__ == "__main__":
    unittest.main()
