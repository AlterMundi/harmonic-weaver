"""Immutable local transport records; browser declarations, not human exposure."""
import hashlib
import json
import re
import threading
from pathlib import Path
from uuid import uuid4
from ..cache import atomic_json, sha256_file
from .experience_transport import Trace, bind_protocol, summarize

FILES = ('trace.json', 'binding.json', 'manifest.json')


class TransportService:
    def __init__(self, data_dir):
        self.root = Path(data_dir) / 'research/r10-transports'
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def folder(self, ident):
        if not isinstance(ident, str) or not re.fullmatch('[a-f0-9]{32}', ident):
            raise ValueError('Invalid transport record ID')
        folder = self.root / ident
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError('Transport record unavailable')
        return folder

    def read(self, ident):
        folder = self.folder(ident)
        for name in FILES:
            path = folder / name
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 16*1024*1024:
                raise ValueError('Regular bounded transport artifacts required')
        hashes = {n: sha256_file(folder/n) for n in FILES}
        manifest = json.loads((folder/'manifest.json').read_text())
        if manifest.get('schema_version') != 1 or manifest.get('kind') != 'declared_transport':
            raise ValueError('Invalid transport manifest')
        if manifest.get('hashes') != {n: hashes[n] for n in FILES[:-1]}:
            raise ValueError('Transport artifact hash mismatch')
        trace = Trace.model_validate_json((folder/'trace.json').read_text())
        digest = hashlib.sha256(json.dumps(trace.model_dump(), sort_keys=True,
                               separators=(',', ':')).encode()).hexdigest()
        if manifest.get('request_sha256') != digest or ident != digest[:32]:
            raise ValueError('Transport content identity mismatch')
        binding = json.loads((folder/'binding.json').read_text())
        trial = binding['trial']
        if (binding['protocol_manifest_sha256'] != trace.protocol_manifest_sha256 or
                trial['trial_id'] != trace.trial_id or
                trial['end_s']-trial['start_s'] != trace.duration_s or
                trial['video_enabled'] != trace.video_enabled or
                trial['audio_enabled'] != trace.audio_enabled):
            raise ValueError('Transport frozen binding mismatch')
        # Only summaries with matching implementation can be recomputed as current.
        current = manifest.get('code_hashes') == self.code_hashes()
        if current and binding['summary'] != summarize(trace):
            raise ValueError('Transport summary recomputation mismatch')
        for name, digest in hashes.items():
            if (folder/name).is_symlink() or sha256_file(folder/name) != digest:
                raise ValueError('Transport changed during verification')
        return {**manifest, 'id': ident,
                'read_verification': 'summary_recomputed' if current else 'historical_integrity_only'}

    @staticmethod
    def code_hashes():
        return {n: sha256_file(Path(__file__).parent/n) for n in
                ('experience_transport.py', 'experience_transport_service.py', '../contracts.py')}

    def start(self, protocols, request):
        trace = Trace.model_validate(request)
        # Content identity makes retries/restarts idempotent without a second receipt file.
        digest = hashlib.sha256(json.dumps(trace.model_dump(), sort_keys=True,
                               separators=(',', ':')).encode()).hexdigest()
        ident = digest[:32]
        with self.lock:
            if (self.root/ident).exists():
                saved = self.read(ident)
                if saved.get('request_sha256') != digest:
                    raise ValueError('Transport content ID collision')
                return saved
            binding = bind_protocol(protocols, trace)
            folder = self.root/ident
            folder.mkdir(mode=0o700, exist_ok=False)
            atomic_json(folder/'trace.json', trace.model_dump())
            atomic_json(folder/'binding.json', binding)
            atomic_json(folder/'manifest.json', {
                'schema_version': 1, 'line': 'R10', 'kind': 'declared_transport',
                'request_sha256': digest, 'code_hashes': self.code_hashes(),
                'hashes': {n: sha256_file(folder/n) for n in FILES[:-1]},
                'limits': ['Immutable browser-declared record, not verified human exposure',
                           'Frozen binding verified at save; reopening does not require original media',
                           'Summary recomputation does not reverify original protocol or identity',
                           'Hashes are not signed custody; incomplete publication is not retried']})
            return self.read(ident)

    def list(self):
        rows = []
        with self.lock:
            for folder in sorted(self.root.iterdir()):
                try:
                    rows.append(self.read(folder.name))
                except (OSError, ValueError, KeyError, TypeError):
                    continue
        return rows

    def artifact(self, ident, name):
        if name not in FILES:
            raise ValueError('Unknown transport artifact')
        self.read(ident)
        return self.folder(ident)/name
