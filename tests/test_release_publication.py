"""Release audit must accept archives, normal Git checkouts and worktrees."""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import chat10_release_audit as audit

class TestPublicationAudit(unittest.TestCase):
    def check_metadata(self, as_file):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'source'
            shutil.copytree(audit.ROOT, root, ignore=shutil.ignore_patterns('.git', '__pycache__'))
            git = root / '.git'
            if as_file:
                git.write_text('gitdir: /example/worktree-metadata\n')
            else:
                git.mkdir()
            with patch.object(audit, 'ROOT', root):
                report = audit.run()
            self.assertTrue(all(report['checks'].values()))
            self.assertTrue(report['repository_metadata_present'])
            self.assertTrue(report['checks']['no_embedded_private_key_candidates'])
    def test_git_checkout(self):
        self.check_metadata(False)
    def test_git_worktree(self):
        self.check_metadata(True)
