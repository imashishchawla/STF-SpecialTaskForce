"""Build an allowlisted public Bob preview; never copy history or runtime data."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

AGENT = Path(__file__).resolve().parents[2]
PUBLIC = AGENT / 'export/public'
VERSION = '0.1.0-preview.2'
SKILLS = ('intake', 'diagnosis', 'source-check', 'reproduction', 'communication')
ROLES = ('coordinator', 'diagnostics', 'source-researcher', 'validation-reviewer',
         'communication-specialist', 'memory-curator')
TEMPLATES = ('customer-reply', 'customer-reply-initial', 'handoff', 'closure',
             'internal-update', 'can-report', 'rca', 'kb-draft', 'preferences.example')
PUBLIC_FILES = ('README.md', 'AGENTS.md', 'LICENSE', 'SECURITY.md', '.gitignore',
                '.bobignore', 'install.py', 'tests/test_release.py', 'docs/welcome.html',
                '.github/ISSUE_TEMPLATE/bug_report.md',
                '.github/ISSUE_TEMPLATE/feature_request.md',
                '.github/ISSUE_TEMPLATE/config.yml')


def public_text(text):
    # Draft source references point into STF-only design documentation. Omit
    # those pointers from the standalone profile; do not copy internal docs.
    text = re.sub(r'^> Full specification:.*\n', '', text, flags=re.M)
    text = text.replace('portable/terraform-support-agent/export/', 'export/')
    text = text.replace('## Style rules (authoritative source: plan §10)',
                        '## Default style rules')
    text = re.sub(r'^.*registry-routing-internal.*\n', '', text, flags=re.M)
    text = re.sub(r'^.*screen_capture_session.*\n', '', text, flags=re.M)
    text = text.replace('## Templates (✅ complete — all 9 files in export/templates/)',
                        '## Draft templates in export/templates/')
    return text


def contents():
    files = {name: (PUBLIC / name).read_text() for name in PUBLIC_FILES}
    for slug in SKILLS:
        text = public_text((AGENT / ('export/skills/' + slug + '.md')).read_text())
        if slug == 'intake':
            start = text.index('## Onboarding check')
            end = text.index('## Purpose', start)
            text = text[:start] + '''## Optional preferences

Read memory/preferences.md if it exists. Empty fields are valid: do not request
a personal name, title, working hours, or filesystem path to begin a synthetic
case. Keep signatures as placeholders. Never store input without approval.

''' + text[end:]
            text = text.replace('Read calibrated values from `memory/patterns/time-estimates.md` before estimating.',
                                'If no locally approved calibration exists, label estimates as uncalibrated.')
        if slug == 'communication':
            text = text.replace('> Never hard-code a name here. If `preferences.md` is unpopulated, the intake onboarding check\n> will have halted the session before this skill is reached.',
                                '> Never hard-code a name. Leave empty signature fields as placeholders.')
        files['export/skills/' + slug + '.md'] = text
    for role in ROLES:
        text = public_text((AGENT / ('export/agents/' + role + '.md')).read_text())
        front, body = text.split('\n---\n', 1)
        text = front + '\n---\n\n> Public preview: perform this review role sequentially in the same conversation; no spawning or live actions. Follow AGENTS.md.\n\n' + body
        if role == 'coordinator':
            start = text.index('## Sub-agent delegation')
            end = text.index('## Boundary constraints', start)
            text = text[:start] + '## Review sequence\nIntake → diagnostics → source review → validation → communication.\nPerform all steps sequentially within this conversation.\n\n' + text[end:]
            text = text.replace('- spawn_subagent (approval required each time)\n', '')
        files['export/agents/' + role + '.md'] = text
    for name in TEMPLATES:
        files['export/templates/' + name + '.md'] = public_text(
            (AGENT / ('export/templates/' + name + '.md')).read_text())
    files['export/templates/README.md'] = '# Draft templates\n\n' + '\n'.join(
        '- `' + name + '.md`' for name in TEMPLATES) + '\n\nUse placeholders and reviewed findings only. Never send automatically.\n'
    files['sources/catalog.md'] = '''# Public reference sources

Links are research starting points, not evidence of current behavior. Verify the
exact product/provider version. If retrieval is unavailable, request a manual
check or supplied excerpt and state what remains unverified.

- Terraform: https://developer.hashicorp.com/terraform
- HCP Terraform: https://developer.hashicorp.com/terraform/cloud-docs
- Terraform Enterprise: https://developer.hashicorp.com/terraform/enterprise
- Providers: https://registry.terraform.io/browse/providers
- Core release notes: https://github.com/hashicorp/terraform/releases
- Service status: https://status.hashicorp.com

Do not use internal employee directories, ticket systems, or confidential process
documents in this public preview. Do not infer historical causes from current status.
'''
    return files


def audit(files):
    # Reviewable heuristic gate; this is not an exhaustive PII detector. The
    # intended public owner/repository URL is allowed, with no operator identity
    # elsewhere. Never scan or ingest vault/runtime data to build this release.
    issues = []
    for name, content in files.items():
        scanned = content.replace('imashishchawla/terraform-support-agent', 'PUBLIC_PROJECT')
        for label, pattern in {
            'operator identity': r'(?i)ashish|ashish_chawla',
            'personal path': r'/Users/|/home/[A-Za-z][^/\s]*',
            'email address': r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
            'internal endpoint': r'github\.ibm\.com|w3\.ibm\.com|atlassian\.net',
            'private key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
            'credential literal': r'\bAKIA[A-Z0-9]{16}\b|\bgh[pousr]_[A-Za-z0-9]{20,}',
        }.items():
            if re.search(pattern, scanned):
                issues.append(name + ': ' + label)
    if issues:
        raise ValueError('Release review required:\n' + '\n'.join(issues))


def build(destination):
    files = contents()
    audit(files)
    # Refuse accidental overwrites and any destination inside private sources.
    destination = destination.absolute()
    if destination.exists():
        raise ValueError('Destination must not exist; retain prior release for review')
    if AGENT == destination or destination in AGENT.parents:
        raise ValueError('Invalid release destination')
    if AGENT in destination.parents and AGENT / 'release-output' not in destination.parents:
        raise ValueError('Within this agent, use release-output/<new-directory>')
    destination.mkdir(parents=True, mode=0o700)
    manifest = {'version': VERSION, 'profile': 'bob-synthetic-preview', 'files': {}}
    for name, content in sorted(files.items()):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode('utf-8')
        target.write_bytes(data)
        manifest['files'][name] = hashlib.sha256(data).hexdigest()
    (destination / 'release-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    # A clean archive with no OS username, personal path, Git history, symlinks,
    # or non-allowlisted files. Fixed metadata makes repeat builds comparable.
    archive = destination.with_name(destination.name + '.tar.gz')
    if archive.exists() or archive.with_name(archive.name + '.sha256').exists():
        raise ValueError('Archive output already exists; choose a new release directory')
    with archive.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode='w') as stream:
                for name in sorted([*files, 'release-manifest.json']):
                    data = (destination / name).read_bytes()
                    info = tarfile.TarInfo('terraform-support-agent/' + name)
                    info.size = len(data)
                    info.mode = 0o644
                    stream.addfile(info, io.BytesIO(data))
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_name(archive.name + '.sha256').write_text(checksum + '  ' + archive.name + '\n')
    print('Built ' + str(len(files) + 1) + ' reviewed text files; no Git history or runtime data copied.')
    print('Destination: ' + str(destination))
    print('Archive SHA-256: ' + checksum)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        build(args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
