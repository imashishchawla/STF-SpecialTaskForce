"""Run with python3 -m runtime.cli from the Visa-Agent workspace."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys
import xml.etree.ElementTree as ET
import zipfile
from .contracts import ContractError
from .coordinator import Coordinator, MAX_INPUT
from .cv import preserve_docx


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-root', type=Path, default=Path('.info/agent-runtime'))
    parser.add_argument('--reveal', action='store_true',
                        help='Show full local results only in a direct interactive terminal')
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('create')
    create.add_argument('case_id')
    create.add_argument('--mode', choices=('general_information', 'professional_review'), default='general_information')
    create.add_argument('--budget', type=int, default=30)
    for name in ('ingest', 'research', 'screen', 'report', 'resume', 'cancel',
                 'client', 'requirements', 'document', 'checklist', 'record_upload'):
        command = commands.add_parser(name)
        command.add_argument('case_id')
        command.add_argument('--token', required=True)
        command.add_argument('--revision', required=True, type=int)
        if name in ('ingest', 'research', 'screen', 'client', 'requirements', 'document', 'checklist', 'record_upload'):
            command.add_argument('--input', type=Path, required=True)
    cv = commands.add_parser('cv')
    cv.add_argument('case_id')
    cv.add_argument('--input', type=Path, required=True)
    cv.add_argument('--token', required=True)
    cv.add_argument('--revision', required=True, type=int)
    args = parser.parse_args(argv)
    coordinator = None
    try:
        if args.reveal and (not sys.stdin.isatty() or not sys.stdout.isatty()):
            raise ContractError('Private results require an interactive terminal')
        coordinator = Coordinator(args.private_root)
        if args.command == 'create':
            result = coordinator.create(args.case_id, args.mode, args.budget)
        elif args.command == 'cv':
            result = coordinator.run(args.case_id, 'cv', {'path': str(args.input.absolute())}, args.token, expected_revision=args.revision)
        else:
            payload = {}
            if hasattr(args, 'input'):
                if args.input.is_symlink() or args.input.stat().st_size > MAX_INPUT:
                    raise ContractError('Expected bounded local JSON input')
                payload = json.loads(args.input.read_text(), parse_constant=lambda _: (_ for _ in ()).throw(ContractError('Non-finite JSON value')))
            result = coordinator.run(args.case_id, args.command, payload, args.token, expected_revision=args.revision)
        if not args.reveal:
            result = {'status': 'ok', 'action': args.command,
                      'revision': result.get('revision', result.get('case_revision')),
                      'legal_eligibility_assessed': result.get('legal_eligibility_assessed', False)}
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ContractError, OSError, sqlite3.Error, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        # Input values/documents are intentionally excluded from error output.
        print(json.dumps({'status': 'error', 'error_type': type(exc).__name__,
                          'message': 'Local operation failed; inspect input privately'}), file=sys.stderr)
        return 1
    finally:
        if coordinator:
            coordinator.close()

if __name__ == '__main__':
    raise SystemExit(main())
