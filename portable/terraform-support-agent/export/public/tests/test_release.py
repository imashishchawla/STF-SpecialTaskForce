"""Offline release checks. Installs only into disposable test workspaces."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and '.git' not in p.parts
            and '__pycache__' not in p.parts}


class ReleaseTests(unittest.TestCase):
    def fixture(self, directory):
        target = Path(directory) / 'preview'
        manifest = json.loads((ROOT / 'release-manifest.json').read_text())
        for name in [*manifest['files'], 'release-manifest.json']:
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        return target

    def run_install(self, root, *args):
        return subprocess.run([sys.executable, '-B', str(root / 'install.py'), '--no-open', *args],
                              text=True, capture_output=True)

    def test_integrity(self):
        manifest = json.loads((ROOT / 'release-manifest.json').read_text())
        for name, expected in manifest['files'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected, name)
            self.assertFalse((ROOT / name).is_symlink())

    def test_public_source_has_no_runtime_data_or_detected_private_identity(self):
        manifest = json.loads((ROOT / 'release-manifest.json').read_text())
        for name in manifest['files']:
            self.assertNotIn(name.split('/')[0],
                             ('memory', 'vault', 'a2a', 'plan', 'checkpoints', '.git'))
            text = (ROOT / name).read_text()
            text = text.replace('imashishchawla/terraform-support-agent', 'PUBLIC_PROJECT')
            # Test strings use concatenation so the literal scan does not match itself.
            self.assertNotRegex(text, r'(?i)' + 'ash' + 'ish')
            self.assertNotRegex(text, r'/Use' + r'rs/|github\.' + r'ibm\.com')
            self.assertNotRegex(text, r'[A-Za-z0-9._%+-]+' + '@' + r'[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
        for path in (ROOT / 'export/agents').glob('*.md'):
            self.assertTrue(path.read_text().startswith('---\n'))

    def test_runtime_files_are_ignored_by_release_gitignore(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            result = subprocess.run(['git', '-C', str(root), 'init', '-q'], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in ('memory/preferences.md', 'memory/patterns/case.md',
                         '.env', 'vault/.key', 'outputs/draft.md', 'stf.db-wal',
                         'checkpoints/case.json', '.install-manifest.json',
                         '.bob/skills/terraform-intake/SKILL.md', '.bob/custom_modes.yaml',
                         'a2a/config.py', 'plan/archive/internal.pdf',
                         'export/mcp/terraform-mcp.yaml'):
                result = subprocess.run(['git', '-C', str(root), '-c',
                                         'core.excludesFile=/dev/null', 'check-ignore',
                                         '--no-index', '-q', name])
                self.assertEqual(result.returncode, 0, name)

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            before = snapshot(root)
            result = self.run_install(root, '--dry-run')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(before, snapshot(root))
            self.assertFalse((root / '.bob').exists())

    def test_install_reinstall_and_personal_preferences_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            result = self.run_install(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(list((root / '.bob/skills').glob('*/SKILL.md'))), 5)
            prefs = root / 'memory/preferences.md'
            self.assertEqual(prefs.stat().st_mode & 0o777, 0o600)
            prefs.write_text('Synthetic local preference\n')
            result = self.run_install(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(prefs.read_text(), 'Synthetic local preference\n')
            mode = (root / '.bob/custom_modes.yaml').read_text()
            self.assertIn('customModes:', mode)
            self.assertNotIn('      - mcp', mode)
            self.assertNotIn('      - execute', mode)
            for path in (root / '.bob/skills').glob('*/SKILL.md'):
                text = path.read_text()
                self.assertIn('description:', text)
                self.assertNotIn(str(root), text)

    def test_conflicting_mode_refused_before_any_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            (root / '.bob').mkdir()
            (root / '.bob/custom_modes.yaml').write_text('Existing configuration\n')
            before = snapshot(root)
            result = self.run_install(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(before, snapshot(root))

    def test_symlink_escape_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            external = Path(tmp) / 'external'
            external.mkdir()
            (root / '.bob').symlink_to(external, target_is_directory=True)
            result = self.run_install(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(external.iterdir()), [])

    def test_tampered_skill_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            (root / 'export/skills/intake.md').write_text('tampered')
            result = self.run_install(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / '.bob').exists())

    def load_installer(self, root):
        spec = importlib.util.spec_from_file_location('preview_installer', root / 'install.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_guide_opens_only_after_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            installer = self.load_installer(root)
            def opened(uri, new):
                self.assertTrue((root / '.install-manifest.json').exists())
                self.assertEqual(uri, (root / 'docs/welcome.html').as_uri())
                self.assertEqual(new, 2)
                return True
            with mock.patch.object(installer.webbrowser, 'open', side_effect=opened) as browser:
                installer.install()
                browser.assert_called_once()

    def test_dry_run_and_no_open_never_launch_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            installer = self.load_installer(root)
            with mock.patch.object(installer.webbrowser, 'open') as browser:
                installer.install(dry_run=True)
                self.assertFalse((root / '.install-manifest.json').exists())
                installer.install(open_guide=False)
                browser.assert_not_called()

    def test_browser_failure_preserves_successful_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            installer = self.load_installer(root)
            with mock.patch.object(installer.webbrowser, 'open', side_effect=OSError('No display')):
                installer.install()
            self.assertTrue((root / '.install-manifest.json').exists())

    def test_welcome_is_offline_and_internal_links_exist(self):
        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.ids, self.fragments = set(), []
                self.remote_assets = []
                self.headings = 0
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if 'id' in attrs:
                    self.ids.add(attrs['id'])
                if tag == 'h1':
                    self.headings += 1
                href = attrs.get('href', '')
                if href.startswith('#'):
                    self.fragments.append(href[1:])
                if tag in ('script', 'iframe', 'img') or (tag == 'link' and attrs.get('rel') == 'stylesheet'):
                    self.remote_assets.append(tag)
        page = (ROOT / 'docs/welcome.html').read_text()
        parser = Links()
        parser.feed(page)
        self.assertEqual(parser.headings, 1)
        self.assertEqual(parser.remote_assets, [])
        self.assertTrue(set(parser.fragments) <= parser.ids)
        self.assertIn('name="viewport"', page)
        self.assertNotIn('localStorage', page)


if __name__ == '__main__':
    unittest.main()
