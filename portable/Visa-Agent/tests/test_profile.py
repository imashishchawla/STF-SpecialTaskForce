from pathlib import Path
import contextlib
import io
import json
import tempfile
import unittest

from profile import create, list_profiles, main, show
from runtime.contracts import ContractError
from runtime.coordinator import Coordinator


class ProfileTests(unittest.TestCase):
    def test_named_folders_are_private_and_case_isolated(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as temp:
            root = Path(temp) / '.profile'
            first = create(root, 'Asha', 'Example')
            second = create(root, 'Asha', 'Example')
            self.assertEqual(list_profiles(root), ['Asha_Example', 'Asha_Example-2'])
            self.assertNotEqual(first['case_id'], second['case_id'])
            self.assertEqual(show(root, first['folder'])['given_names'], 'Asha')
            self.assertEqual((root / first['folder'] / 'state.sqlite3').stat().st_mode & 0o777, 0o600)
            self.assertEqual((root / first['folder']).stat().st_mode & 0o777, 0o700)
            coordinator = Coordinator(root / second['folder'])
            try:
                with self.assertRaises(ContractError):
                    coordinator.case(first['case_id'])
            finally:
                coordinator.close()

    def test_invalid_client_does_not_leave_profile(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as temp:
            root = Path(temp) / '.profile'
            with self.assertRaises(ContractError):
                create(root, 'Bad/Name', 'Example')
            self.assertEqual(list_profiles(root), [])

    def test_cli_default_output_omits_names_and_paths(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as temp:
            root = Path(temp) / '.profile'
            created = create(root, 'Asha', 'Example')
            for command in (['list'], ['show', created['folder']]):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(main(['--profiles-root', str(root), *command]), 0)
                self.assertNotIn('Asha', output.getvalue())
                self.assertNotIn(str(root), output.getvalue())
                self.assertIsInstance(json.loads(output.getvalue()), dict)
            error = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(error):
                self.assertEqual(main(['--profiles-root', str(root), '--reveal', 'show', created['folder']]), 1)
            self.assertNotIn('Asha', error.getvalue())


if __name__ == '__main__':
    unittest.main()
