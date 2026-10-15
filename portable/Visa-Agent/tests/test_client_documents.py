from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import tempfile
import unittest

from runtime.contracts import ContractError
from runtime.coordinator import Coordinator


def act(coordinator, case_id, action, payload, token):
    return coordinator.run(case_id, action, payload, token,
                           expected_revision=coordinator.case(case_id)['revision'])


class ClientDocumentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/private/tmp')
        self.base = Path(self.temp.name)
        self.coordinator = Coordinator(self.base / 'private')
        self.coordinator.create('case_a')
        self.coordinator.create('case_b')

    def tearDown(self):
        self.coordinator.close()
        self.temp.cleanup()

    def client(self, version=0, family='Example'):
        return {'given_names': 'Asha', 'family_name': family,
                'other_names': ['Prior Name'], 'name_basis': 'passport_seen',
                'provenance': 'synthetic local passport inspection',
                'expected_client_version': version}

    def requirements(self, version=0, age_days=0):
        return {
            'route': '500:student', 'expected_list_version': version,
            'coverage_note': 'Synthetic public stream excerpt only; actual ImmiAccount list not reviewed',
            'sources': [{
                'id': 'stream',
                'url': 'https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing/student-500',
                'title': 'Synthetic fixture; not a current legal rule',
                'accessed_at': (datetime.now(timezone.utc)-timedelta(days=age_days)).isoformat(),
                'published_at': None,
                'content': 'Provide a passport. A replacement travel document may be accepted in this synthetic test.'}],
            'items': [{
                'id': 'passport', 'title': 'Passport', 'source_id': 'stream',
                'source_excerpt': 'Provide a passport.', 'necessity': 'required',
                'preparation_note': 'Operator note: request a clear copy from the client.',
                'alternatives': [{'text': 'Synthetic travel document possibility; confirm the actual rule.',
                                  'source_id': 'stream',
                                  'source_excerpt': 'A replacement travel document may be accepted in this synthetic test.'}]}]}

    def prepare(self):
        act(self.coordinator, 'case_a', 'client', self.client(), 'client_1')
        act(self.coordinator, 'case_a', 'requirements', self.requirements(), 'requirements_1')

    def test_client_name_and_versions_stay_local(self):
        first = act(self.coordinator, 'case_a', 'client', self.client(), 'client_1')
        self.assertEqual(first['family_name'], 'Example')
        self.assertTrue(first['name_for_application_requires_operator_check'])
        with self.assertRaises(ContractError):
            act(self.coordinator, 'case_a', 'client', self.client(family='Stale'), 'stale_client')
        second = act(self.coordinator, 'case_a', 'client', self.client(version=1, family='Corrected'), 'client_2')
        self.assertEqual(second['client_version'], 2)
        with self.assertRaises(ContractError):
            act(self.coordinator, 'case_b', 'checklist', {'route': '500:student'}, 'cross_case')
        self.assertNotIn('Corrected',
                         ''.join(row['action'] for row in self.coordinator.db.execute('SELECT action FROM events')))

    def test_source_dated_list_and_supported_alternative(self):
        self.prepare()
        report = act(self.coordinator, 'case_a', 'checklist', {'route': '500:student'}, 'checklist_1')
        self.assertEqual(report['items'][0]['status'], 'missing_local')
        self.assertFalse(report['complete'])
        self.assertFalse(report['upload_ready'])
        self.assertIsNone(report['sources'][0]['published_at'])
        self.assertTrue(report['sources'][0]['saved_at'])
        self.assertEqual(report['sources'][0]['content_hash'], hashlib.sha256(self.requirements()['sources'][0]['content'].encode()).hexdigest())
        invalid = self.requirements(version=1)
        invalid['items'][0]['alternatives'][0]['source_excerpt'] = 'An alternative that is not in the source'
        with self.assertRaises(ContractError):
            act(self.coordinator, 'case_a', 'requirements', invalid, 'bad_alternative')
        self.assertEqual(self.coordinator.db.execute('SELECT version FROM document_lists').fetchone()[0], 1)

    def test_document_copy_name_and_revision_recheck(self):
        self.prepare()
        original = self.base / 'original.PDF'
        original.write_bytes(b'%PDF-1.4\nSynthetic local file')
        result = act(self.coordinator, 'case_a', 'document',
                     {'route': '500:student', 'requirement_id': 'passport', 'path': str(original)}, 'document_1')
        saved = Path(result['saved_path'])
        self.assertEqual(saved.read_bytes(), original.read_bytes())
        self.assertEqual(saved.stat().st_mode & 0o777, 0o600)
        self.assertTrue(result['suggested_filename'].startswith('Example_Asha_Passport_'))
        self.assertFalse(result['filename_is_official_requirement'])
        self.assertFalse(result['upload_ready'])
        current = act(self.coordinator, 'case_a', 'checklist', {'route': '500:student'}, 'checklist_2')
        self.assertEqual(current['items'][0]['status'], 'collected_local')
        self.assertEqual(current['items'][0]['documents'][0]['saved_path'], str(saved))
        act(self.coordinator, 'case_b', 'client', self.client(), 'client_b')
        act(self.coordinator, 'case_b', 'requirements', self.requirements(), 'requirements_b')
        with self.assertRaises(ContractError):
            act(self.coordinator, 'case_b', 'document',
                {'route': '500:student', 'requirement_id': 'passport', 'path': str(saved)}, 'cross_case_doc')
        act(self.coordinator, 'case_a', 'client', self.client(version=1, family='Newname'), 'client_2')
        changed = act(self.coordinator, 'case_a', 'checklist', {'route': '500:student'}, 'checklist_3')
        self.assertTrue(changed['items'][0]['needs_recheck'])
        act(self.coordinator, 'case_a', 'requirements', self.requirements(version=1), 'requirements_2')
        changed = act(self.coordinator, 'case_a', 'checklist', {'route': '500:student'}, 'checklist_4')
        self.assertTrue(changed['items'][0]['needs_recheck'])

    def test_stale_source_and_unapproved_url(self):
        act(self.coordinator, 'case_a', 'client', self.client(), 'client_1')
        act(self.coordinator, 'case_a', 'requirements', self.requirements(age_days=8), 'old_requirements')
        report = act(self.coordinator, 'case_a', 'checklist', {'route': '500:student'}, 'old_checklist')
        self.assertEqual(report['sources'][0]['freshness'], 'stale')
        self.assertTrue(report['items'][0]['needs_recheck'])
        bad = self.requirements(version=1)
        bad['sources'][0]['url'] = 'https://github.com/example/visa-rules'
        with self.assertRaises(ContractError):
            act(self.coordinator, 'case_a', 'requirements', bad, 'bad_source')

    def test_upload_tracking_is_only_an_operator_record(self):
        self.prepare()
        original = self.base / 'record.pdf'
        original.write_bytes(b'%PDF-1.4\nSynthetic')
        document = act(self.coordinator, 'case_a', 'document',
                       {'route': '500:student', 'requirement_id': 'passport', 'path': str(original)}, 'document_1')
        with self.assertRaises(ContractError):
            act(self.coordinator, 'case_b', 'record_upload',
                {'route': '500:student', 'document_id': document['document_id'],
                 'uploaded_at': datetime.now(timezone.utc).isoformat(),
                 'evidence_note': 'synthetic ImmiAccount receipt'}, 'cross_upload')
        result = act(self.coordinator, 'case_a', 'record_upload',
                     {'route': '500:student', 'document_id': document['document_id'],
                      'uploaded_at': datetime.now(timezone.utc).isoformat(),
                      'evidence_note': 'operator saw synthetic Received status'}, 'upload_note')
        self.assertFalse(result['actual_upload_performed_by_tool'])
        report = act(self.coordinator, 'case_a', 'checklist', {'route': '500:student'}, 'checklist_1')
        self.assertEqual(report['items'][0]['status'], 'operator_reported_uploaded')
        self.assertFalse(report['upload_ready'])


if __name__ == '__main__':
    unittest.main()
