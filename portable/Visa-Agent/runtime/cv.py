"""Local DOCX preservation and structural checks; no renderer or external upload."""
from pathlib import Path
import hashlib
import io
import shutil
import uuid
import zipfile
import xml.etree.ElementTree as ET
from .contracts import ContractError, identifier

MAX_DOCX = 20 * 1024 * 1024
MAX_EXPANDED = 50 * 1024 * 1024
MC = '{http://schemas.openxmlformats.org/markup-compatibility/2006}Ignorable'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def inspect_docx(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_DOCX:
        raise ContractError('Expected bounded local regular DOCX')
    raw = path.read_bytes()
    texts, links = [], []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        if len(infos) > 2000 or sum(i.file_size for i in infos) > MAX_EXPANDED:
            raise ContractError('DOCX exceeds expansion bound')
        if len({i.filename for i in infos}) != len(infos):
            raise ContractError('Duplicate ZIP members')
        if archive.testzip() is not None:
            raise ContractError('Invalid ZIP integrity')
        if not {'[Content_Types].xml', 'word/document.xml'} <= set(archive.namelist()):
            raise ContractError('Missing required OOXML members')
        for info in infos:
            if not info.filename.endswith(('.xml', '.rels')):
                continue
            content = archive.read(info.filename)
            if b'<!DOCTYPE' in content.upper() or b'<!ENTITY' in content.upper():
                raise ContractError('DTD/entity declarations forbidden')
            # Track namespace scope on each element; undeclared mc:Ignorable prefixes
            # can break Word even when generic XML parsing succeeds.
            scope, pending, stack = {}, [], []
            for event, node in ET.iterparse(io.BytesIO(content), events=('start-ns', 'start', 'end')):
                if event == 'start-ns':
                    pending.append(node)
                elif event == 'start':
                    stack.append(scope)
                    scope = dict(scope)
                    scope.update(pending)
                    pending = []
                    if any(prefix not in scope for prefix in node.attrib.get(MC, '').split()):
                        raise ContractError('Undeclared mc:Ignorable namespace prefix')
                else:
                    scope = stack.pop()
            tree = ET.fromstring(content)
            if info.filename == 'word/document.xml':
                texts = [''.join(p.itertext()) for p in tree.iter(W + 't')]
            if info.filename.endswith('.rels'):
                links += [node.attrib['Target'] for node in tree
                          if node.attrib.get('Type', '').endswith('/hyperlink') and 'Target' in node.attrib]
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'text': '\n'.join(texts), 'links': links,
            'zip_integrity': True, 'xml_integrity': True, 'mc_ignorable': True,
            'rendered': False, 'page_count': None,
            'limits': ['Word/LibreOffice rendering and visual layout have not been verified.']}

def preserve_docx(path, private_root, case_id):
    identifier(case_id)
    original = Path(path)
    resolved = original.resolve()
    root_resolved = Path(private_root).resolve()
    if resolved.is_relative_to(root_resolved) and not resolved.is_relative_to(root_resolved / 'cv' / case_id):
        raise ContractError('CV path references private artifacts outside this case')
    result = inspect_docx(original)
    root = Path(private_root)
    directory = root / 'cv' / case_id
    for parent in (root, root / 'cv', directory):
        if parent.is_symlink():
            raise ContractError('Private artifact directory must not be a symlink')
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        parent.chmod(0o700)
    copy = directory / ('original-' + uuid.uuid4().hex + '.docx')
    # Preserve exactly the bytes inspected, detecting mutation while copying.
    shutil.copyfile(original, copy)
    copy.chmod(0o600)
    if hashlib.sha256(copy.read_bytes()).hexdigest() != result['sha256']:
        copy.unlink()
        raise ContractError('CV changed during preservation')
    result['preserved_path'] = str(copy.resolve())
    return result
