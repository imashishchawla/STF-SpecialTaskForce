import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from decrypt_vault import main
from runtime.redactor import encrypt_vault_mapping, get_or_create_vault_key


class VaultCliTests(unittest.TestCase):
    def test_default_output_contains_counts_only(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as temp:
            profile = Path(temp) / 'Synthetic_Client'
            profile.mkdir()
            key = get_or_create_vault_key(profile / '.vault.key')
            encrypt_vault_mapping({'XCVBH-TEST-0001': 'Asha Example'}, key, profile / 'vault.enc')
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main([str(profile)]), 0)
            self.assertIn('"token_count": 1', output.getvalue())
            self.assertNotIn('Asha Example', output.getvalue())
            self.assertNotIn(str(profile), output.getvalue())
            error = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(error):
                self.assertEqual(main([str(profile), '--reveal']), 1)
            self.assertNotIn('Asha Example', error.getvalue())


if __name__ == '__main__':
    unittest.main()
