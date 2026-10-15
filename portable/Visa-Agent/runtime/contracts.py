"""Canonical local record validation; no network or model dependency."""
from datetime import datetime, timezone
from urllib.parse import urlsplit
import re

VERSION = '1.0.0'
ENUMS = {
    'verification': ('candidate_reported', 'document_supported', 'disputed', 'unknown'),
    'fit': ('potential_fit', 'conditional', 'excluded', 'unresolved', 'not_assessed'),
    'source_status': ('current', 'unavailable', 'conflicting', 'stale'),
    'open_status': ('open', 'closed', 'transition_only', 'unknown'),
    'mode': ('general_information', 'professional_review'),
}
OFFICIAL_HOSTS = ('immi.homeaffairs.gov.au', 'www.mara.gov.au', 'www.acs.org.au')
STATE_HOSTS = ('www.migration.sa.gov.au', 'migration.wa.gov.au',
               'liveinmelbourne.vic.gov.au', 'www.nsw.gov.au',
               'www.migration.tas.gov.au', 'migration.qld.gov.au',
               'www.act.gov.au', 'theterritory.com.au')

class ContractError(ValueError):
    pass

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value):
        raise ContractError('Invalid local identifier')
    return value

def official_url(url):
    if not isinstance(url, str):
        raise ContractError('URL must be a string')
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname not in OFFICIAL_HOSTS + STATE_HOSTS
            or parsed.username or parsed.password or parsed.port not in (None, 443)
            or parsed.query or parsed.fragment):
        raise ContractError('Only registered HTTPS official pages without query/fragment are accepted')
    return url

def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError()
    except (ValueError, TypeError):
        raise ContractError('Timestamp must include a timezone') from None
    return parsed

def validate(record, kind, case_id, revision):
    if not isinstance(record, dict):
        raise ContractError('Record must be an object')
    common = {'id', 'case_id', 'revision', 'schema_version', 'provenance', 'created_at'}
    fields = {
        'fact': {'name', 'value', 'verification'},
        'source': {'url', 'title', 'rule', 'content_hash', 'accessed_at', 'source_status', 'scope', 'open_status', 'open_rule'},
        'screen': {'subclass', 'stream', 'fit', 'source_status', 'open_status',
                   'source_ids', 'fact_ids', 'reason', 'gaps', 'gates'},
    }
    if kind not in fields or set(record) != common | fields[kind]:
        raise ContractError('Record fields differ from canonical schema')
    identifier(record['id'])
    if record['case_id'] != case_id or record['revision'] != revision:
        raise ContractError('Cross-case or stale revision record')
    if record['schema_version'] != VERSION or not isinstance(record['revision'], int) or isinstance(record['revision'], bool):
        raise ContractError('Unsupported schema/revision')
    timestamp(record['created_at'])
    if not isinstance(record['provenance'], str) or not record['provenance'].strip():
        raise ContractError('Provenance is required')
    for field, values in ENUMS.items():
        if field in record and record[field] not in values:
            raise ContractError('Invalid ' + field)
    if kind == 'fact':
        identifier(record['name'])
        if not isinstance(record['value'], (str, int, float, bool, type(None))):
            raise ContractError('Fact must be a scalar')
        if isinstance(record['value'], str) and len(record['value']) > 4000:
            raise ContractError('Fact is too large')
    if kind == 'source':
        official_url(record['url'])
        accessed = timestamp(record['accessed_at'])
        if accessed > datetime.now(timezone.utc):
            raise ContractError('Future source access time')
        if not re.fullmatch(r'[a-f0-9]{64}', record['content_hash']):
            raise ContractError('Content SHA256 required')
        if not isinstance(record['open_rule'], str):
            raise ContractError('Open-rule evidence must be a string')
        for field in ('title', 'rule', 'scope'):
            if not isinstance(record[field], str) or not record[field].strip():
                raise ContractError('Source field required: ' + field)
    if kind == 'screen':
        if not isinstance(record['subclass'], str) or not re.fullmatch(r'\d{3}', record['subclass']):
            raise ContractError('Subclass must contain three digits')
        for field in ('stream', 'reason'):
            if not isinstance(record[field], str) or not record[field].strip():
                raise ContractError('Screen field required: ' + field)
        for field in ('source_ids', 'fact_ids', 'gaps', 'gates'):
            if not isinstance(record[field], list):
                raise ContractError('Screen field must be a list: ' + field)
        for field in ('source_ids', 'fact_ids'):
            for ref in record[field]:
                identifier(ref)
        for gap in record['gaps']:
            if not isinstance(gap, str):
                raise ContractError('Gaps must contain strings')
    return record
