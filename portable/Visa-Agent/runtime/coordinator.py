"""Single-coordinator SQLite state machine. External candidate tools do not exist."""
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json
import os
import sqlite3

from .contracts import ContractError, VERSION, ENUMS, identifier, official_url, utcnow, validate, timestamp
from . import client_documents

MAX_INPUT = 2 * 1024 * 1024
REQUIRED_INDEXES = ('finder', 'permanent_work', 'temporary_work', 'short_stay_work', 'visa_listing')
SOURCE_REGISTRY = {
    'finder': 'https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-finder',
    'permanent_work': 'https://immi.homeaffairs.gov.au/visas/working-in-australia/permanent-work-visas',
    'temporary_work': 'https://immi.homeaffairs.gov.au/visas/working-in-australia/temporary-work-visas',
    'short_stay_work': 'https://immi.homeaffairs.gov.au/visas/working-in-australia/short-stay-work-visas',
    'visa_listing': 'https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing',
}

def stable(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)

class Coordinator:
    def __init__(self, root):
        raw_root = Path(root).absolute()
        if any(p.is_symlink() for p in (raw_root, *raw_root.parents)):
            raise ContractError('Private root ancestry must not contain symlinks')
        self.root = raw_root.resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.is_symlink():
            raise ContractError('Private root must not be a symlink')
        os.chmod(self.root, 0o700)
        db = self.root / 'state.sqlite3'
        if db.is_symlink():
            raise ContractError('Database must not be a symlink')
        self.db = sqlite3.connect(db, isolation_level=None, timeout=10)
        self.db.row_factory = sqlite3.Row
        os.chmod(db, 0o600)
        self.db.executescript('''
        PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS cases (
          id TEXT PRIMARY KEY, revision INTEGER NOT NULL, mode TEXT NOT NULL,
          status TEXT NOT NULL, budget INTEGER NOT NULL, used INTEGER NOT NULL,
          created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS records (
          case_id TEXT NOT NULL REFERENCES cases(id), kind TEXT NOT NULL,
          id TEXT NOT NULL, revision INTEGER NOT NULL, payload TEXT NOT NULL,
          PRIMARY KEY(case_id,kind,id,revision));
        CREATE TABLE IF NOT EXISTS snapshots (
          case_id TEXT NOT NULL REFERENCES cases(id), source_id TEXT NOT NULL,
          revision INTEGER NOT NULL, content TEXT NOT NULL,
          PRIMARY KEY(case_id,source_id,revision));
        CREATE TABLE IF NOT EXISTS receipts (
          case_id TEXT NOT NULL REFERENCES cases(id), token TEXT NOT NULL,
          action TEXT NOT NULL, input_hash TEXT NOT NULL, result TEXT NOT NULL,
          PRIMARY KEY(case_id,token));
        CREATE TABLE IF NOT EXISTS events (
          sequence INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL,
          action TEXT NOT NULL, revision INTEGER NOT NULL, timestamp TEXT NOT NULL);
        ''')
        client_documents.setup(self.db)

    def close(self):
        self.db.close()

    def case(self, case_id):
        identifier(case_id)
        row = self.db.execute('SELECT * FROM cases WHERE id=?', (case_id,)).fetchone()
        if row is None:
            raise ContractError('Unknown case')
        return dict(row)

    def create(self, case_id, mode='general_information', budget=30):
        identifier(case_id)
        if mode not in ENUMS['mode'] or type(budget) is not int or not 1 <= budget <= 500:
            raise ContractError('Invalid mode or step budget')
        with self.transaction():
            self.db.execute('INSERT INTO cases VALUES (?,1,?,\'active\',?,0,?)',
                            (case_id, mode, budget, utcnow()))
            self.event(case_id, 'create', 1)
        return self.case(case_id)

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def event(self, case_id, action, revision):
        # No facts, documents, URLs, or model reasoning in the event journal.
        self.db.execute('INSERT INTO events(case_id,action,revision,timestamp) VALUES (?,?,?,?)',
                        (case_id, action, revision, utcnow()))

    def records(self, case_id, kind, revision=None):
        revision = revision or self.case(case_id)['revision']
        rows = [json.loads(row[0]) for row in self.db.execute(
            'SELECT payload FROM records WHERE case_id=? AND kind=? AND revision=? ORDER BY id',
            (case_id, kind, revision))]
        if kind == 'source':
            for record in rows:
                if record['source_status'] == 'current' and timestamp(record['accessed_at']) < datetime.now(timezone.utc) - timedelta(days=7):
                    record['source_status'] = 'stale'
        return rows

    def store(self, case, kind, record):
        validate(record, kind, case['id'], case['revision'])
        self.db.execute('INSERT INTO records VALUES (?,?,?,?,?)',
                        (case['id'], kind, record['id'], case['revision'], stable(record)))

    def envelope(self, case, id, provenance):
        return dict(id=identifier(id), case_id=case['id'], revision=case['revision'],
                    schema_version=VERSION, provenance=provenance, created_at=utcnow())

    def run(self, case_id, action, payload, token, *, expected_revision):
        identifier(token)
        if type(expected_revision) is not int or expected_revision < 1 or not isinstance(payload, dict):
            raise ContractError('Expected revision and object payload required')
        if len(stable(payload).encode()) > MAX_INPUT:
            raise ContractError('Local action input exceeds size bound')
        if action not in ('ingest', 'research', 'screen', 'report', 'resume', 'cancel', 'cv',
                          'client', 'requirements', 'document', 'checklist', 'record_upload'):
            raise ContractError('Tool denied: no such local action')
        fingerprint = hashlib.sha256(stable({'payload': payload, 'expected_revision': expected_revision}).encode()).hexdigest()
        with self.transaction():
            case = self.case(case_id)
            receipt = self.db.execute('SELECT * FROM receipts WHERE case_id=? AND token=?',
                                      (case_id, token)).fetchone()
            if receipt:
                if receipt['input_hash'] != fingerprint or receipt['action'] != action:
                    raise ContractError('Idempotency token reused with different input')
                return json.loads(receipt['result'])
            if expected_revision != case['revision']:
                raise ContractError('Stale expected revision; refresh the case before writing')
            if action == 'resume':
                if case['status'] != 'cancelled':
                    raise ContractError('Only a cancelled case can resume')
                self.db.execute("UPDATE cases SET status='active' WHERE id=?", (case_id,))
                result = {'status': 'active', 'revision': case['revision']}
            elif action == 'cancel':
                self.db.execute("UPDATE cases SET status='cancelled' WHERE id=?", (case_id,))
                result = {'status': 'cancelled', 'revision': case['revision']}
            else:
                if case['status'] != 'active':
                    raise ContractError('Case is cancelled')
                if case['used'] >= case['budget']:
                    raise ContractError('Step budget exhausted; create a new reviewed run')
                result = getattr(self, '_' + action)(case, payload)
                self.db.execute('UPDATE cases SET used=used+1 WHERE id=?', (case_id,))
            self.event(case_id, action, self.case(case_id)['revision'])
            self.db.execute('INSERT INTO receipts VALUES (?,?,?,?,?)',
                            (case_id, token, action, fingerprint, stable(result)))
            return result

    def _ingest(self, case, payload):
        if set(payload) != {'facts'} or not isinstance(payload['facts'], list) or not payload['facts']:
            raise ContractError('Ingest requires a nonempty facts list')
        # Replacement snapshot: all prior sources and screens remain historical only.
        if self.records(case['id'], 'fact') or self.records(case['id'], 'source'):
            case = dict(case, revision=case['revision'] + 1)
            self.db.execute('UPDATE cases SET revision=? WHERE id=?', (case['revision'], case['id']))
        names = set()
        for item in payload['facts']:
            if not isinstance(item, dict) or set(item) != {'id', 'name', 'value', 'verification', 'provenance'}:
                raise ContractError('Invalid fact input')
            if item['name'] in names:
                raise ContractError('Duplicate fact name')
            names.add(item['name'])
            record = self.envelope(case, item['id'], item['provenance'])
            record.update({k: item[k] for k in ('name', 'value', 'verification')})
            self.store(case, 'fact', record)
        return {'revision': case['revision'], 'facts': len(payload['facts']), 'prior_screens_invalidated': True}

    def _research(self, case, payload):
        if set(payload) != {'sources'} or not isinstance(payload['sources'], list) or not payload['sources']:
            raise ContractError('Research requires local source snapshots')
        if self.records(case['id'], 'source') or self.records(case['id'], 'screen'):
            old_facts = self.records(case['id'], 'fact')
            case = dict(case, revision=case['revision'] + 1)
            self.db.execute('UPDATE cases SET revision=? WHERE id=?', (case['revision'], case['id']))
            for fact in old_facts:
                fact['revision'] = case['revision']
                self.store(case, 'fact', fact)
        for item in payload['sources']:
            required = {'id', 'url', 'title', 'rule', 'content', 'accessed_at', 'source_status', 'scope', 'provenance', 'open_status', 'open_rule'}
            if not isinstance(item, dict) or set(item) != required:
                raise ContractError('Invalid source snapshot')
            content = item['content']
            if not isinstance(content, str) or len(content.encode()) > MAX_INPUT:
                raise ContractError('Source content exceeds local input bound')
            if item['source_status'] == 'current' and (not content or item['rule'] not in content):
                raise ContractError('Current rule must appear verbatim in provided snapshot')
            if item['open_status'] != 'unknown' and (not isinstance(item['open_rule'], str) or not item['open_rule'] or item['open_rule'] not in content):
                raise ContractError('Open status needs literal snapshot evidence')
            record = self.envelope(case, item['id'], item['provenance'])
            record.update({k: item[k] for k in ('url', 'title', 'rule', 'accessed_at', 'source_status', 'scope', 'open_status', 'open_rule')})
            record['content_hash'] = hashlib.sha256(content.encode()).hexdigest()
            # Even a recent local snapshot is only candidate-supplied research evidence,
            # not proof of current website contents. Seven days is a conservative local TTL.
            if timestamp(item['accessed_at']) < datetime.now(timezone.utc) - timedelta(days=7):
                record['source_status'] = 'stale'
            self.store(case, 'source', record)
            self.db.execute('INSERT INTO snapshots VALUES (?,?,?,?)',
                            (case['id'], record['id'], case['revision'], content))
        return {'revision': case['revision'], 'sources': len(payload['sources']),
                'adapter': 'local_snapshot', 'live_verified': False}

    def _screen(self, case, payload):
        expected = {'id', 'subclass', 'stream', 'source_ids', 'open_status', 'gates', 'provenance'}
        if not isinstance(payload, dict) or set(payload) != expected:
            raise ContractError('Invalid screen input')
        sources = {s['id']: s for s in self.records(case['id'], 'source')}
        facts = {f['id']: f for f in self.records(case['id'], 'fact')}
        if not isinstance(payload['source_ids'], list) or not payload['source_ids']:
            raise ContractError('Screen requires official stream evidence')
        if any(ref not in sources for ref in payload['source_ids']):
            raise ContractError('Missing, stale, or cross-case source reference')
        if not isinstance(payload['gates'], list):
            raise ContractError('Gates must be a list')
        selected = [sources[ref] for ref in payload['source_ids']]
        scope = payload['subclass'] + ':' + payload['stream']
        if any(s['scope'] != scope for s in selected):
            raise ContractError('Index or unrelated stream cannot establish a screen')
        if any(s['open_status'] != payload['open_status'] for s in selected):
            raise ContractError('Screen open status differs from its source evidence')
        statuses = {s['source_status'] for s in selected}
        source_status = next((s for s in ('conflicting', 'unavailable', 'stale') if s in statuses), 'current')
        gaps, failed, conditional, refs = [], [], False, []
        if source_status != 'current' or payload['open_status'] == 'unknown':
            gaps.append('Verify current official stream source and open status')
        for gate in payload['gates']:
            if not isinstance(gate, dict) or set(gate) != {'fact_id', 'source_id', 'operator', 'value', 'rule', 'review_status', 'reviewer'}:
                raise ContractError('Invalid gate')
            if gate['source_id'] not in payload['source_ids']:
                raise ContractError('Gate source outside screened stream')
            if gate['rule'] != sources[gate['source_id']]['rule']:
                raise ContractError('Gate rule is not supported by referenced source')
            if gate['review_status'] not in ('unreviewed', 'qualified_human_confirmed') or not isinstance(gate['reviewer'], str):
                raise ContractError('Invalid local semantic review annotation')
            if gate['review_status'] == 'qualified_human_confirmed' and not gate['reviewer'].strip():
                raise ContractError('Local semantic review provenance required')
            if not isinstance(gate['value'], (str, int, float, bool, type(None))):
                raise ContractError('Gate comparison value must be a scalar')
            fact = facts.get(gate['fact_id'])
            if gate['operator'] not in ('eq', 'min', 'max'):
                raise ContractError('Unsupported comparison operator')
            if fact is None:
                raise ContractError('Missing, stale, or cross-case fact reference')
            refs.append(fact['id'])
            if fact['verification'] in ('unknown', 'disputed') or fact['value'] is None:
                gaps.append('Clarify ' + fact['name'])
                continue
            conditional |= fact['verification'] != 'document_supported'
            if gate['operator'] == 'eq':
                passed = type(fact['value']) is type(gate['value']) and fact['value'] == gate['value']
            else:
                if type(fact['value']) not in (int, float) or type(gate['value']) not in (int, float):
                    raise ContractError('Numeric gate requires numeric facts and limits')
                passed = fact['value'] >= gate['value'] if gate['operator'] == 'min' else fact['value'] <= gate['value']
            if not passed:
                if fact['verification'] == 'document_supported' and gate['review_status'] == 'qualified_human_confirmed':
                    failed.append(fact['name'])
                else:
                    gaps.append('Confirm fact and structured rule semantics with qualified human: ' + fact['name'])
        # This comparator never determines legal eligibility or recommends a visa.
        if gaps:
            fit, reason = 'unresolved', '; '.join(gaps)
        elif payload['open_status'] in ('closed', 'transition_only'):
            fit, reason = 'unresolved', 'Closure/transition applicability requires qualified human review'
        elif failed:
            fit, reason = 'excluded', 'Recorded gate mismatch: ' + ', '.join(failed)
        elif not payload['gates']:
            fit, reason = 'not_assessed', 'No candidate gates assessed'
        else:
            fit, reason = ('conditional' if conditional else 'potential_fit'), 'Only recorded gates compared; additional rules may apply'
        record = self.envelope(case, payload['id'], payload['provenance'])
        record.update(subclass=payload['subclass'], stream=payload['stream'], fit=fit,
                      source_status=source_status, open_status=payload['open_status'],
                      source_ids=payload['source_ids'], fact_ids=sorted(set(refs)), reason=reason,
                      gaps=gaps, gates=payload['gates'])
        self.store(case, 'screen', record)
        return record

    def _cv(self, case, payload):
        from .cv import preserve_docx
        if set(payload) != {'path'} or not isinstance(payload['path'], str):
            raise ContractError('CV input requires a local path')
        return preserve_docx(payload['path'], self.root, case['id'])

    def _client(self, case, payload):
        return client_documents.save_client(self.db, case['id'], payload)

    def _requirements(self, case, payload):
        return client_documents.import_requirements(self.db, case['id'], payload)

    def _document(self, case, payload):
        return client_documents.register_document(self.db, self.root, case['id'], payload)

    def _checklist(self, case, payload):
        return client_documents.checklist(self.db, case['id'], payload)

    def _record_upload(self, case, payload):
        return client_documents.record_upload(self.db, case['id'], payload)

    def _report(self, case, payload):
        if payload != {}:
            raise ContractError('Report takes no private query parameters')
        sources = self.records(case['id'], 'source')
        covered = {s['scope'] for s in sources if s['source_status'] == 'current'
                   and SOURCE_REGISTRY.get(s['scope']) == s['url']}
        by_id = {s['id']: s for s in sources}
        screens = self.records(case['id'], 'screen')
        for screen in screens:
            current_statuses = {by_id[ref]['source_status'] for ref in screen['source_ids']}
            current_status = next((v for v in ('conflicting','unavailable','stale') if v in current_statuses), 'current')
            if current_status != 'current':
                screen.update(fit='unresolved', source_status=current_status, reason='Source status changed since recorded comparison; recheck official page')
        return {'case_id': case['id'], 'revision': case['revision'], 'schema_version': VERSION,
                'mode': case['mode'], 'screens': screens, 'assessment_kind': 'recorded_comparator_triage',
                'legal_eligibility_assessed': False, 'source_currentness': 'local_annotation_only',
                'coverage': {'reviewed_indexes': sorted(covered),
                             'missing_indexes': sorted(set(REQUIRED_INDEXES) - covered),
                             'exhaustive': False, 'live_verified': False},
                'limits': ['Local snapshots have not been checked against live pages.',
                           'Recorded gate comparison is research triage, not eligibility or migration advice.',
                           'Qualified human review is required before relying on a personalized legal conclusion.']}
