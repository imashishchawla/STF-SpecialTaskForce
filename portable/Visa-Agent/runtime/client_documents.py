"""Private client names, source-dated document lists, and local upload-copy inventory.

All requirement interpretations and name evidence are operator assertions. This
module neither fetches current law nor uploads anything to ImmiAccount.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import json
import os
import re
import unicodedata
import uuid

from .contracts import ContractError, identifier, official_url, timestamp, utcnow

MAX_FILE = 5 * 1024 * 1024
FORMATS = {'.bmp', '.dcm', '.doc', '.docx', '.dot', '.gif', '.jpg', '.png',
           '.pdf', '.ppt', '.pptx', '.rft', '.txt', '.xls', '.xlsx'}
UPLOAD_GUIDANCE = {
    'url': 'https://immi.homeaffairs.gov.au/help-support/applying-online-or-on-paper/online/attach-documents-to-your-application',
    'published_at': None,
    'accessed_at': '2026-10-14',
    'saved_at': '2026-10-14',
    'note': 'General ImmiAccount format/size guidance; recheck the live page and actual application before upload.',
}


def setup(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS clients (
      case_id TEXT PRIMARY KEY REFERENCES cases(id), version INTEGER NOT NULL,
      given_names TEXT NOT NULL, family_name TEXT NOT NULL,
      other_names TEXT NOT NULL, name_basis TEXT NOT NULL,
      provenance TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS document_lists (
      case_id TEXT NOT NULL REFERENCES cases(id), route TEXT NOT NULL,
      version INTEGER NOT NULL, coverage_note TEXT NOT NULL, saved_at TEXT NOT NULL,
      PRIMARY KEY(case_id,route));
    CREATE TABLE IF NOT EXISTS document_sources (
      case_id TEXT NOT NULL, route TEXT NOT NULL, version INTEGER NOT NULL,
      id TEXT NOT NULL, url TEXT NOT NULL, title TEXT NOT NULL,
      accessed_at TEXT NOT NULL, published_at TEXT,
      saved_at TEXT NOT NULL, content_hash TEXT NOT NULL, content TEXT NOT NULL,
      PRIMARY KEY(case_id,route,version,id));
    CREATE TABLE IF NOT EXISTS document_requirements (
      case_id TEXT NOT NULL, route TEXT NOT NULL, version INTEGER NOT NULL,
      id TEXT NOT NULL, title TEXT NOT NULL, source_id TEXT NOT NULL,
      source_excerpt TEXT NOT NULL, necessity TEXT NOT NULL,
      preparation_note TEXT NOT NULL, alternatives TEXT NOT NULL,
      PRIMARY KEY(case_id,route,version,id));
    CREATE TABLE IF NOT EXISTS client_documents (
      case_id TEXT NOT NULL REFERENCES cases(id), id TEXT NOT NULL,
      route TEXT NOT NULL, requirement_id TEXT NOT NULL,
      list_version INTEGER NOT NULL, client_version INTEGER NOT NULL,
      path TEXT NOT NULL, suggested_filename TEXT NOT NULL,
      sha256 TEXT NOT NULL, size_bytes INTEGER NOT NULL, saved_at TEXT NOT NULL,
      operator_reported_uploaded_at TEXT, upload_note TEXT,
      PRIMARY KEY(case_id,id));
    ''')


def _name(value):
    if not isinstance(value, str):
        raise ContractError('Name must be text')
    value = unicodedata.normalize('NFC', value.strip())
    if not value or len(value) > 120 or any(ord(char) < 32 or char in '/\\' for char in value):
        raise ContractError('Invalid client name')
    return value


def _note(value, label, limit=2000):
    if not isinstance(value, str) or len(value) > limit:
        raise ContractError('Invalid ' + label)
    return value


def _route(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{3}:[A-Za-z0-9_-]{1,48}', value):
        raise ContractError('Route must be subclass:stream')
    return value


def _client(db, case_id):
    row = db.execute('SELECT * FROM clients WHERE case_id=?', (case_id,)).fetchone()
    if not row:
        raise ContractError('Client name has not been recorded for this case')
    result = dict(row)
    result['other_names'] = json.loads(result['other_names'])
    return result


def save_client(db, case_id, payload):
    required = {'given_names', 'family_name', 'other_names', 'name_basis',
                'provenance', 'expected_client_version'}
    if set(payload) != required:
        raise ContractError('Client input fields differ from contract')
    prior = db.execute('SELECT version FROM clients WHERE case_id=?', (case_id,)).fetchone()
    current = prior['version'] if prior else 0
    if type(payload['expected_client_version']) is not int or payload['expected_client_version'] != current:
        raise ContractError('Stale client version; refresh the name record')
    given = _name(payload['given_names'])
    family = _name(payload['family_name'])
    others = payload['other_names']
    if not isinstance(others, list) or len(others) > 12:
        raise ContractError('Other names must be a bounded list')
    others = [_name(value) for value in others]
    if payload['name_basis'] not in ('candidate_reported', 'passport_seen', 'other_document_seen'):
        raise ContractError('Invalid name basis')
    provenance = _note(payload['provenance'], 'name provenance')
    if not provenance.strip():
        raise ContractError('Name provenance is required')
    now = utcnow()
    db.execute('''INSERT INTO clients VALUES (?,?,?,?,?,?,?,?)
      ON CONFLICT(case_id) DO UPDATE SET version=excluded.version,
      given_names=excluded.given_names,family_name=excluded.family_name,
      other_names=excluded.other_names,name_basis=excluded.name_basis,
      provenance=excluded.provenance,updated_at=excluded.updated_at''',
      (case_id, current + 1, given, family, json.dumps(others),
       payload['name_basis'], provenance, now))
    return {'case_id': case_id, 'client_version': current + 1, 'given_names': given,
            'family_name': family, 'other_names': others, 'name_basis': payload['name_basis'],
            'updated_at': now, 'name_for_application_requires_operator_check': True}


def import_requirements(db, case_id, payload):
    if set(payload) != {'route', 'expected_list_version', 'sources', 'items', 'coverage_note'}:
        raise ContractError('Requirement input fields differ from contract')
    route = _route(payload['route'])
    prior = db.execute('SELECT version FROM document_lists WHERE case_id=? AND route=?',
                       (case_id, route)).fetchone()
    current = prior['version'] if prior else 0
    if type(payload['expected_list_version']) is not int or payload['expected_list_version'] != current:
        raise ContractError('Stale document-list version')
    sources = payload['sources']
    items = payload['items']
    if not isinstance(sources, list) or not sources or len(sources) > 30 or not isinstance(items, list) or len(items) > 200:
        raise ContractError('Requirements need bounded official sources and items')
    coverage_note = _note(payload['coverage_note'], 'coverage note')
    if not coverage_note.strip():
        raise ContractError('State which application/stream checklist was reviewed and what remains unchecked')
    source_map = {}
    saved = utcnow()
    for source in sources:
        if not isinstance(source, dict) or set(source) != {'id','url','title','accessed_at','published_at','content'}:
            raise ContractError('Invalid document source')
        source_id = identifier(source['id'])
        if source_id in source_map:
            raise ContractError('Duplicate document source ID')
        official_url(source['url'])
        accessed = timestamp(source['accessed_at'])
        if accessed > datetime.now(timezone.utc):
            raise ContractError('Future source access time')
        published = source['published_at']
        if published is not None and timestamp(published) > accessed:
            raise ContractError('Published date after access time')
        content = source['content']
        if not isinstance(content, str) or not content or len(content.encode()) > 2 * 1024 * 1024:
            raise ContractError('Document source text required within bound')
        title = _note(source['title'], 'source title', 300)
        if not title.strip():
            raise ContractError('Source title required')
        source_map[source_id] = dict(source, hash=hashlib.sha256(content.encode()).hexdigest())
    item_map = {}
    for item in items:
        required = {'id','title','source_id','source_excerpt','necessity','preparation_note','alternatives'}
        if not isinstance(item, dict) or set(item) != required:
            raise ContractError('Invalid document requirement')
        item_id = identifier(item['id'])
        if item_id in item_map:
            raise ContractError('Duplicate document requirement ID')
        if item['source_id'] not in source_map:
            raise ContractError('Requirement source missing from this import')
        excerpt = _note(item['source_excerpt'], 'source excerpt', 2000)
        if not excerpt or excerpt not in source_map[item['source_id']]['content']:
            raise ContractError('Requirement excerpt absent from saved source')
        if item['necessity'] not in ('required', 'conditional', 'unknown'):
            raise ContractError('Invalid requirement necessity')
        title = _note(item['title'], 'requirement title', 150)
        if not title.strip():
            raise ContractError('Requirement title required')
        _note(item['preparation_note'], 'preparation note')
        alternatives = item['alternatives']
        if not isinstance(alternatives, list) or len(alternatives) > 10:
            raise ContractError('Alternatives must be a bounded list')
        for alternative in alternatives:
            if not isinstance(alternative, dict) or set(alternative) != {'text','source_id','source_excerpt'}:
                raise ContractError('Alternative needs official evidence')
            if alternative['source_id'] not in source_map:
                raise ContractError('Alternative source missing')
            quote = _note(alternative['source_excerpt'], 'alternative excerpt')
            if not quote or quote not in source_map[alternative['source_id']]['content']:
                raise ContractError('Alternative not supported by saved source')
            if not _note(alternative['text'], 'alternative note').strip():
                raise ContractError('Alternative text required')
        item_map[item_id] = item
    version = current + 1
    db.execute('''INSERT INTO document_lists VALUES (?,?,?,?,?)
      ON CONFLICT(case_id,route) DO UPDATE SET version=excluded.version,
      coverage_note=excluded.coverage_note,saved_at=excluded.saved_at''',
      (case_id, route, version, coverage_note, saved))
    for source_id, source in source_map.items():
        db.execute('INSERT INTO document_sources VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                   (case_id, route, version, source_id, source['url'], source['title'],
                    source['accessed_at'], source['published_at'], saved, source['hash'], source['content']))
    for item_id, item in item_map.items():
        db.execute('INSERT INTO document_requirements VALUES (?,?,?,?,?,?,?,?,?,?)',
                   (case_id, route, version, item_id, item['title'], item['source_id'],
                    item['source_excerpt'], item['necessity'], item['preparation_note'],
                    json.dumps(item['alternatives'], ensure_ascii=False)))
    return {'case_id': case_id, 'route': route, 'list_version': version,
            'source_count': len(source_map), 'item_count': len(item_map),
            'saved_at': saved, 'live_verified': False, 'complete': False}


def _slug(value, fallback):
    ascii_text = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    slug = re.sub(r'[^A-Za-z0-9]+', '_', ascii_text).strip('_')[:45]
    return slug or fallback


def register_document(db, private_root, case_id, payload):
    if set(payload) != {'route', 'requirement_id', 'path'} or not isinstance(payload['path'], str):
        raise ContractError('Document input fields differ from contract')
    route = _route(payload['route'])
    requirement_id = identifier(payload['requirement_id'])
    listing = db.execute('SELECT version FROM document_lists WHERE case_id=? AND route=?',
                         (case_id, route)).fetchone()
    if not listing:
        raise ContractError('No document list for this route')
    requirement = db.execute('''SELECT title FROM document_requirements
       WHERE case_id=? AND route=? AND version=? AND id=?''',
       (case_id, route, listing['version'], requirement_id)).fetchone()
    if not requirement:
        raise ContractError('Requirement absent from current route list')
    client = _client(db, case_id)
    path = Path(payload['path']).absolute()
    if any(parent.is_symlink() for parent in (path, *path.parents)) or not path.is_file():
        raise ContractError('Document must be a regular non-symlink file')
    private = Path(private_root).resolve()
    resolved = path.resolve()
    if resolved.is_relative_to(private) and not resolved.is_relative_to(private / 'documents' / case_id):
        raise ContractError('Document path references another private artifact')
    suffix = path.suffix.lower()
    if suffix not in FORMATS:
        raise ContractError('Document format outside reviewed general ImmiAccount list')
    if path.stat().st_size > MAX_FILE:
        raise ContractError('Document exceeds reviewed general 5 MB bound')
    data = path.read_bytes()
    if not data or len(data) > MAX_FILE:
        raise ContractError('Document exceeds reviewed general 5 MB bound or is empty')
    directory = private / 'documents' / case_id
    for parent in (private, private / 'documents', directory):
        if parent.is_symlink():
            raise ContractError('Private document directory must not be a symlink')
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        parent.chmod(0o700)
    date = datetime.now(timezone.utc).strftime('%Y%m%d')
    suggested = '_'.join((_slug(client['family_name'], 'Family'),
                          _slug(client['given_names'], 'Given'),
                          _slug(requirement['title'], requirement_id), date)) + suffix
    document_id = uuid.uuid4().hex
    destination = directory / (document_id + '-' + suggested)
    try:
        with destination.open('xb') as output:
            os.chmod(destination, 0o600)
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        digest = hashlib.sha256(data).hexdigest()
        if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
            raise ContractError('Document copy changed during preservation')
        saved = utcnow()
        db.execute('''INSERT INTO client_documents
           (case_id,id,route,requirement_id,list_version,client_version,path,
            suggested_filename,sha256,size_bytes,saved_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                   (case_id, document_id, route, requirement_id, listing['version'],
                    client['version'], str(destination), suggested, digest, len(data), saved))
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return {'case_id': case_id, 'document_id': document_id, 'route': route,
            'requirement_id': requirement_id, 'saved_path': str(destination),
            'suggested_filename': suggested, 'filename_is_official_requirement': False,
            'sha256': digest, 'size_bytes': len(data), 'saved_at': saved,
            'status': 'collected_local', 'upload_ready': False,
            'verification_needed': ['Confirm live ImmiAccount request, file type, size, clarity, translation, and document category before upload.']}


def record_upload(db, case_id, payload):
    if set(payload) != {'route', 'document_id', 'uploaded_at', 'evidence_note'}:
        raise ContractError('Upload record fields differ from contract')
    route = _route(payload['route'])
    document_id = identifier(payload['document_id'])
    row = db.execute('''SELECT saved_at,operator_reported_uploaded_at FROM client_documents
        WHERE case_id=? AND route=? AND id=?''', (case_id, route, document_id)).fetchone()
    if not row:
        raise ContractError('Document not found in this case and route')
    if row['operator_reported_uploaded_at']:
        raise ContractError('Upload already recorded for this document')
    uploaded = timestamp(payload['uploaded_at'])
    if uploaded < timestamp(row['saved_at']) or uploaded > datetime.now(timezone.utc):
        raise ContractError('Upload record time is outside local document interval')
    note = _note(payload['evidence_note'], 'upload evidence note')
    if not note.strip():
        raise ContractError('Operator upload evidence note is required')
    db.execute('''UPDATE client_documents SET operator_reported_uploaded_at=?,upload_note=?
        WHERE case_id=? AND route=? AND id=?''',
        (payload['uploaded_at'], note, case_id, route, document_id))
    return {'case_id': case_id, 'route': route, 'document_id': document_id,
            'operator_reported_uploaded_at': payload['uploaded_at'],
            'actual_upload_performed_by_tool': False,
            'evidence_is_operator_assertion': True}


def checklist(db, case_id, payload):
    if set(payload) != {'route'}:
        raise ContractError('Checklist needs only a route')
    route = _route(payload['route'])
    client = _client(db, case_id)
    listing = db.execute('SELECT * FROM document_lists WHERE case_id=? AND route=?',
                         (case_id, route)).fetchone()
    if not listing:
        raise ContractError('No document list for this route')
    version = listing['version']
    sources = []
    for row in db.execute('''SELECT id,url,title,accessed_at,published_at,saved_at,content_hash
       FROM document_sources WHERE case_id=? AND route=? AND version=? ORDER BY id''',
       (case_id, route, version)):
        source = dict(row)
        source['freshness'] = ('stale' if timestamp(source['accessed_at']) < datetime.now(timezone.utc)-timedelta(days=7)
                               else 'recent_local_snapshot_unverified')
        sources.append(source)
    by_source = {source['id']: source for source in sources}
    entries = []
    for row in db.execute('''SELECT * FROM document_requirements
       WHERE case_id=? AND route=? AND version=? ORDER BY id''',
       (case_id, route, version)):
        item = dict(row)
        item['alternatives'] = json.loads(item['alternatives'])
        docs = [dict(doc) for doc in db.execute('''SELECT id,path AS saved_path,suggested_filename,sha256,size_bytes,saved_at,list_version,client_version,operator_reported_uploaded_at,upload_note
          FROM client_documents WHERE case_id=? AND route=? AND requirement_id=? ORDER BY saved_at''',
          (case_id, route, item['id']))]
        source = by_source[item['source_id']]
        item['needs_recheck'] = (source['freshness'] == 'stale' or
                                  any(doc['list_version'] != version or doc['client_version'] != client['version'] for doc in docs))
        item['status'] = ('operator_reported_uploaded' if any(doc['operator_reported_uploaded_at'] for doc in docs) else
                          'needs_recheck' if docs and item['needs_recheck'] else
                          'collected_local' if docs else 'missing_local')
        item['documents'] = docs
        del item['case_id'], item['route'], item['version']
        entries.append(item)
    return {'case_id': case_id, 'route': route, 'client': {
                'given_names': client['given_names'], 'family_name': client['family_name'],
                'other_names': client['other_names'], 'name_basis': client['name_basis'],
                'client_version': client['version'], 'updated_at': client['updated_at']},
            'list_version': version, 'saved_at': listing['saved_at'],
            'coverage_note': listing['coverage_note'], 'sources': sources, 'items': entries,
            'complete': False, 'live_verified': False, 'upload_ready': False,
            'application_checklist_required': True,
            'general_upload_guidance': dict(UPLOAD_GUIDANCE, recheck_required=True),
            'limits': ['Public checklists can be incomplete for a specific applicant.',
                       'Use the actual ImmiAccount application list and current stream page before upload.',
                       'A suggested filename is not an official naming requirement.',
                       'No file has been uploaded by this tool.']}
