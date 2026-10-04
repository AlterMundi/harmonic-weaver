"""Local immutable CSV imports, including original UTF-8 bytes and explicit map."""
import json
import platform
import threading
from pathlib import Path
from uuid import uuid4

from ..cache import atomic_json, sha256_file
from ..contracts import Contract
from .experience_response_service import identity
from .experience_transport_service import TransportService
from .neuro_csv import Request, convert
from .neuro_observations import Stream

FILES = ('source.csv', 'request.json', 'result.json', 'manifest.json')


def code_hashes():
    return {name: sha256_file(Path(__file__).parent / name) for name in
            ('neuro_csv.py', 'neuro_csv_archive.py', 'neuro_observations.py', 'csv_table.py',
             'spatial_observations.py', '../contracts.py')}


def verify(folder, *, recompute=False):
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('Regular CSV import directory required')
    for name in FILES:
        path = folder / name
        budget = 16 if name == 'source.csv' else 128
        if path.is_symlink() or not path.is_file() or path.stat().st_size > budget*1024*1024:
            raise ValueError('Regular bounded CSV import artifacts required')
    hashes = {name: sha256_file(folder / name) for name in FILES}
    manifest = json.loads((folder / 'manifest.json').read_text())
    Contract.finite_tree(manifest)
    if (not isinstance(manifest, dict) or manifest.get('schema_version') != 1 or manifest.get('line') != 'R11' or
            manifest.get('kind') != 'csv_import' or manifest.get('status') != 'complete'):
        raise ValueError('Invalid CSV import manifest')
    if manifest.get('hashes') != {name: hashes[name] for name in FILES[:-1]}:
        raise ValueError('CSV import artifact hash mismatch')
    frozen = Request.model_validate_json((folder / 'request.json').read_text())
    if manifest.get('request_sha256') != identity(frozen.model_dump()):
        raise ValueError('CSV import request identity mismatch')
    # read_bytes is deliberate: universal-newline text reads would lose CRLF.
    if (folder / 'source.csv').read_bytes() != frozen.csv_text.encode('utf-8'):
        raise ValueError('CSV original bytes differ from frozen request')
    result = json.loads((folder / 'result.json').read_text())
    Contract.finite_tree(result)
    if not isinstance(result, dict) or result.get('schema_version') != 1 or result.get('line') != 'R11':
        raise ValueError('Invalid CSV conversion result')
    stream = result.get('stream', {})
    provenance = result.get('import_provenance', {})
    Stream.model_validate(stream)
    if not isinstance(provenance, dict):
        raise ValueError('Invalid CSV conversion provenance')
    if (stream.get('raw_source_sha256') != hashes['source.csv'] or
            provenance.get('raw_utf8_sha256') != hashes['source.csv'] or
            provenance.get('mapping') != frozen.mapping.model_dump() or
            any(stream.get(k) != v for k, v in frozen.metadata.model_dump().items())):
        raise ValueError('CSV conversion binding differs from frozen input')
    if recompute and result != convert(frozen):
        raise ValueError('CSV import recomputation differs')
    for name, digest in hashes.items():
        if (folder / name).is_symlink() or sha256_file(folder / name) != digest:
            raise ValueError('CSV import changed during verification')
    return {**manifest, 'read_verification': 'recomputed' if recompute else 'integrity_only',
            'current_code_matches': manifest.get('code_hashes') == code_hashes()}


class CSVService(TransportService):
    def __init__(self, data_dir):
        self.root = Path(data_dir) / 'research/r11-csv-imports'
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def read(self, ident, *, recompute=False):
        verified = verify(self.folder(ident), recompute=recompute)
        if verified['request_sha256'][:32] != ident:
            raise ValueError('CSV content identity differs from directory')
        return {**verified, 'id': ident}

    def start(self, request):
        frozen = Request.model_validate(request)
        digest = identity(frozen.model_dump())
        ident = digest[:32]
        with self.lock:
            if (self.root / ident).exists():
                saved = self.read(ident)
                if saved['request_sha256'] != digest:
                    raise ValueError('CSV content identity collision')
                return saved
            result = convert(frozen)
            staging = self.root / f'.{ident}-{uuid4().hex}'
            staging.mkdir(mode=0o700)
            (staging / 'source.csv').write_bytes(frozen.csv_text.encode('utf-8'))
            atomic_json(staging / 'request.json', frozen.model_dump())
            atomic_json(staging / 'result.json', result)
            atomic_json(staging / 'manifest.json', {
                'schema_version': 1, 'line': 'R11', 'kind': 'csv_import',
                'status': 'complete', 'request_sha256': digest,
                'hashes': {name: sha256_file(staging / name) for name in FILES[:-1]},
                'code_hashes': code_hashes(), 'environment': {'python': platform.python_version()},
                'samples': len(result['stream']['samples']),
                'source_id': frozen.metadata.source_id,
                'limits': ['Original UTF-8 bytes and declared map retained locally',
                           'Hardware, units, clock and subject slot remain declarations',
                           'Integrity is not signed custody; recomputation is explicit']})
            verify(staging, recompute=True)
            staging.rename(self.root / ident)
            return self.read(ident)

    def artifact(self, ident, name):
        if name not in FILES:
            raise ValueError('Unknown CSV import artifact')
        self.read(ident)
        return self.folder(ident) / name
