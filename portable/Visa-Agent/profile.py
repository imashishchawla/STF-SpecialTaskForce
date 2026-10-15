"""Create and inspect private, case-scoped client profiles."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import unicodedata
import uuid

from runtime.contracts import ContractError
from runtime.coordinator import Coordinator

ROOT = Path(__file__).resolve().parent
PROFILES = ROOT / '.profile'


def slug_part(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    return re.sub(r'[^A-Za-z0-9]+', '_', value).strip('_')[:48] or 'Client'


def checked_root(root):
    root = Path(root).absolute()
    if root.is_symlink():
        raise ContractError('Profile root must not be a symlink')
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    root.chmod(0o700)
    return root


def checked_profile(root, folder):
    if not re.fullmatch(r'[A-Za-z0-9_]+(?:-[2-9][0-9]*)?', folder):
        raise ContractError('Invalid profile folder')
    path = root / folder
    if path.is_symlink() or not path.is_dir():
        raise ContractError('Profile folder not found')
    if (path / 'profile.json').is_symlink() or (path / 'state.sqlite3').is_symlink():
        raise ContractError('Profile metadata or database must not be a symlink')
    return path


def create(root, given_names, family_name, other_names=None, name_basis='candidate_reported', provenance='Client supplied name; identity document not checked'):
    root = checked_root(root)
    base = slug_part(given_names) + '_' + slug_part(family_name)
    for number in range(1, 1000):
        folder = base if number == 1 else f'{base}-{number}'
        path = root / folder
        try:
            path.mkdir(mode=0o700)
            break
        except FileExistsError:
            continue
    else:
        raise ContractError('No available profile folder for this name')
    case_id = 'case_' + uuid.uuid4().hex
    coordinator = None
    completed = False
    try:
        coordinator = Coordinator(path)
        coordinator.create(case_id)
        client = coordinator.run(case_id, 'client', {
            'given_names': given_names, 'family_name': family_name,
            'other_names': other_names or [], 'name_basis': name_basis,
            'provenance': provenance, 'expected_client_version': 0,
        }, 'client_initial', expected_revision=1)
        metadata = {'profile_version': 1, 'case_id': case_id,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'private_root': '.', 'client_version': client['client_version']}
        metadata_path = path / 'profile.json'
        with metadata_path.open('x') as output:
            os.chmod(metadata_path, 0o600)
            json.dump(metadata, output, indent=2)
            output.write('\n')
        completed = True
        return {'folder': folder, 'case_id': case_id, 'profile_path': str(path),
                'client': client, 'profile_is_local': True}
    finally:
        if coordinator is not None:
            coordinator.close()
        if not completed:
            shutil.rmtree(path)


def show(root, folder):
    path = checked_profile(checked_root(root), folder)
    metadata = json.loads((path / 'profile.json').read_text())
    if set(metadata) != {'profile_version', 'case_id', 'created_at', 'private_root', 'client_version'}:
        raise ContractError('Invalid profile metadata')
    coordinator = Coordinator(path)
    try:
        case = coordinator.case(metadata['case_id'])
        row = coordinator.db.execute('SELECT * FROM clients WHERE case_id=?',
                                     (metadata['case_id'],)).fetchone()
        if row is None:
            raise ContractError('Client name missing from local database')
        return {'folder': folder, 'profile_path': str(path), 'case_id': metadata['case_id'],
                'case_revision': case['revision'], 'status': case['status'],
                'given_names': row['given_names'], 'family_name': row['family_name'],
                'other_names': json.loads(row['other_names']), 'name_basis': row['name_basis'],
                'client_version': row['version'], 'name_for_application_requires_operator_check': True}
    finally:
        coordinator.close()


def list_profiles(root):
    root = checked_root(root)
    return [path.name for path in sorted(root.iterdir())
            if path.is_dir() and not path.is_symlink() and (path / 'profile.json').is_file()]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profiles-root', type=Path, default=PROFILES)
    commands = parser.add_subparsers(dest='command', required=True)
    create_cmd = commands.add_parser('create')
    create_cmd.add_argument('--given-names', required=True)
    create_cmd.add_argument('--family-name', required=True)
    create_cmd.add_argument('--other-name', action='append', default=[])
    create_cmd.add_argument('--name-basis', choices=('candidate_reported', 'passport_seen', 'other_document_seen'), default='candidate_reported')
    create_cmd.add_argument('--provenance', default='Client supplied name; identity document not checked')
    show_cmd = commands.add_parser('show')
    show_cmd.add_argument('folder')
    commands.add_parser('list')
    parser.add_argument('--reveal', action='store_true',
                        help='Show names and paths only in a direct interactive terminal')
    args = parser.parse_args(argv)
    try:
        if args.reveal and (not sys.stdin.isatty() or not sys.stdout.isatty()):
            raise ContractError('Private profile details require an interactive terminal')
        if args.command == 'create':
            result = create(args.profiles_root, args.given_names, args.family_name,
                            args.other_name, args.name_basis, args.provenance)
        elif args.command == 'show':
            result = show(args.profiles_root, args.folder)
        else:
            result = {'profiles': list_profiles(args.profiles_root)}
        if not args.reveal:
            if args.command == 'list':
                result = {'profile_count': len(result['profiles'])}
            elif args.command == 'show':
                result = {key: result[key] for key in ('case_id', 'case_revision', 'status', 'client_version')}
            else:
                result = {'case_id': result['case_id'], 'profile_is_local': True}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ContractError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
        print(json.dumps({'status': 'error', 'error_type': type(exc).__name__,
                          'message': str(exc) if isinstance(exc, ContractError) else 'Local profile operation failed'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
