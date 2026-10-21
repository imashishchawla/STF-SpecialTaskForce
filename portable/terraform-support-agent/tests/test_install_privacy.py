"""Offline installation checks; no home installation or live services."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

AGENT = Path(__file__).resolve().parents[1]


class InstallPrivacyTests(unittest.TestCase):
    def test_adapter_generates_all_skills_without_personal_source_paths(self):
        with tempfile.TemporaryDirectory() as target:
            subprocess.run([
                'bash', str(AGENT / 'export/scripts/generate-bob-adapter.sh'),
                '--target', target,
            ], check=True, capture_output=True)
            skills = list(Path(target).glob('*/SKILL.md'))
            self.assertEqual(len(skills), 7)
            for skill in skills:
                content = skill.read_text()
                self.assertIn('generated_from: export/skills/', content)
                self.assertNotIn(str(AGENT), content)

    def test_install_dry_run_plans_blank_preferences_without_writes(self):
        with tempfile.TemporaryDirectory() as target:
            root = Path(target)
            shutil.copy(AGENT / 'installer.sh', root)
            shutil.copytree(AGENT / 'export', root / 'export')
            (root / 'bin').mkdir()
            bob = root / 'bin/bob'
            bob.write_text('#!/bin/sh\nexit 0\n')
            bob.chmod(0o700)
            before = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in root.rglob('*') if p.is_file()}
            result = subprocess.run([
                'bash', str(root / 'installer.sh'), 'install', '--dry-run',
            ], input='skip\n', text=True, capture_output=True, check=True,
                env={**os.environ, 'PATH': str(root / 'bin') + ':' + os.environ['PATH']})
            self.assertIn('private blank preferences', result.stdout)
            after = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in root.rglob('*') if p.is_file()}
            self.assertEqual(before, after)

    def test_runtime_paths_ignored_and_template_trackable(self):
        runtime = ['memory/preferences.md', '.install-manifest', '.install-manifest.txt',
                   'checkpoints/closed-case.md', 'checkpoints/draft/case.json',
                   'evals/results/session-new.md', 'vault/.key', 'audit/run.jsonl',
                   'messages/run.jsonl', 'metrics/run.jsonl', 'stf.db-wal',
                   'a2a/.env', 'a2a/.a2a.pid', 'a2a/a2a-server.log',
                   'terraform-support-agent-test.tar.gz']
        for name in runtime:
            result = subprocess.run(['git', 'check-ignore', '--no-index', '-q',
                                     str(AGENT / name)])
            self.assertEqual(result.returncode, 0, name)
        result = subprocess.run(['git', 'check-ignore', '--no-index', '-q',
                                 str(AGENT / 'export/templates/preferences.example.md')])
        self.assertEqual(result.returncode, 1)

    def test_preferences_template_has_empty_operator_fields(self):
        content = (AGENT / 'export/templates/preferences.example.md').read_text()
        for key in ['operator_name', 'operator_title', 'operator_availability', 'agent_repo_path']:
            self.assertIn(key + ': ""', content)


if __name__ == '__main__':
    unittest.main()
