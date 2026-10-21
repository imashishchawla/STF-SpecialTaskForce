"""Offline, workspace-only Bob preview installer. No home or network writes."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import webbrowser

ROOT = Path(__file__).resolve().parent
VERSION = '0.1.0-preview.2'
SKILLS = ('intake', 'diagnosis', 'source-check', 'reproduction', 'communication')

MODE = '''customModes:
  - slug: terraform-support-preview
    name: Terraform Support Preview
    description: Diagnose synthetic Terraform cases and draft reviewed guidance.
    roleDefinition: >-
      You are a Terraform support coordinator. Follow AGENTS.md and load
      export/agents/coordinator.md. Use only independently redacted synthetic
      input. Use intake, diagnosis, source-check, reproduction and communication
      skills as needed. Perform specialist review steps sequentially in this
      conversation. Never spawn subagents, execute commands, connect MCP, read
      credentials, or change customer systems. Never claim a source was retrieved
      unless its contents were actually supplied and verified. Offer a manual
      public documentation check when retrieval is unavailable. Draft only;
      never send messages or close cases.
    whenToUse: Synthetic Terraform support diagnosis and communication drafts.
    customInstructions: >-
      Follow AGENTS.md. Preferences are optional; leave unknown signature fields
      as placeholders. No personal information is required to start. Never read
      .env, vaults, raw logs, or other private stores. Any request for live actions
      or real customer data is outside this preview. Stop and explain the limit.
    groups:
      - read
      - skill
'''


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_path(relative):
    path = ROOT / relative
    if path != ROOT and ROOT not in path.parents:
        raise ValueError('Path outside workspace')
    for item in (path, *path.parents):
        if item == ROOT:
            break
        if item.is_symlink():
            raise ValueError('Symlink refused: ' + relative)
    return path


def verify_release():
    manifest = json.loads((ROOT / 'release-manifest.json').read_text())
    if manifest['version'] != VERSION:
        raise ValueError('Release version mismatch')
    for name, expected in manifest['files'].items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or '\\' in name:
            raise ValueError('Invalid release path')
        path = check_path(name)
        if not path.is_file() or digest(path) != expected:
            raise ValueError('Integrity mismatch: ' + name)
    return manifest


def planned_files():
    files = {}
    for slug in SKILLS:
        source = 'export/skills/' + slug + '.md'
        text = (ROOT / source).read_text()
        if not text.startswith('---\n') or '\n---\n' not in text[4:]:
            raise ValueError('Missing canonical front matter: ' + source)
        body = text.split('\n---\n', 1)[1]
        content = ('---\nname: terraform-' + slug + '\ndescription: ' + {
            'intake': 'Classify a synthetic Terraform support report and identify missing evidence.',
            'diagnosis': 'Evaluate supplied Terraform evidence and rank testable hypotheses.',
            'source-check': 'Verify version-specific Terraform claims using supplied public sources.',
            'reproduction': 'Draft an isolated Terraform reproduction plan without executing it.',
            'communication': 'Draft a Terraform support reply from reviewed findings.',
        }[slug] + '\nmetadata:\n  version: "' + VERSION +
            '"\n  generated_from: ' + source + '\n---\n' + body)
        files['.bob/skills/terraform-' + slug + '/SKILL.md'] = content
    files['.bob/custom_modes.yaml'] = MODE
    if not (ROOT / 'memory/preferences.md').exists():
        files['memory/preferences.md'] = (ROOT / 'export/templates/preferences.example.md').read_text()
    return files


def install(dry_run=False, open_guide=True):
    verify_release()
    check_path('memory/preferences.md')
    files = planned_files()
    # Validate every destination before the first write. Never overwrite a
    # different Bob mode/skill or follow a link into another workspace.
    for name, content in files.items():
        path = check_path(name)
        if path.exists() and (not path.is_file() or path.read_text() != content):
            raise ValueError('Existing file differs; review manually: ' + name)
    check_path('.install-manifest.json')
    for name, content in files.items():
        path = ROOT / name
        print(('Would ensure: ' if dry_run else 'Ensure: ') + name)
        if not dry_run and not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with path.open('x', encoding='utf-8') as stream:
                stream.write(content)
            path.chmod(0o600)
    print(('Would write: ' if dry_run else 'Write: ') + '.install-manifest.json')
    if not dry_run:
        manifest = {'version': VERSION, 'files': sorted(
            [name for name in files if name != 'memory/preferences.md'])}
        old_umask = os.umask(0o077)
        try:
            (ROOT / '.install-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
            (ROOT / '.install-manifest.json').chmod(0o600)
        finally:
            os.umask(old_umask)
    if dry_run:
        if open_guide:
            print('Would open local welcome guide: docs/welcome.html')
    elif open_guide:
        guide = (ROOT / 'docs/welcome.html').as_uri()
        try:
            opened = webbrowser.open(guide, new=2)
        except Exception:
            opened = False
        if not opened:
            print('Installation succeeded. Open docs/welcome.html manually in your browser.')
    else:
        print('Welcome guide: docs/welcome.html (automatic opening disabled)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--no-open', action='store_true', help='Do not open the local welcome guide')
    args = parser.parse_args()
    try:
        install(args.dry_run, open_guide=not args.no_open)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, 'Installation refused: ' + str(error) + '\n')
