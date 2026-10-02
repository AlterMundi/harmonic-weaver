"""Resolve verified local inputs before publishing a frozen endpoint benchmark."""
import json
import shutil
import threading
from pathlib import Path
from typing import Literal
from uuid import uuid4
from pydantic import Field
from ..contracts import Contract
from ..cache import sha256_file
from .rope_flow_benchmark_run import Identifier, Input, run
from .rope_compare_service import RopeCompareService
from .rope_flow_benchmark_run import read_verified


class Selection(Contract):
    reference_id: Identifier
    flow_id: Identifier
    endpoint_seeds: dict[Literal['a','b'], int] = Field(min_length=1, max_length=2)


class RopeFlowBenchmarkService(RopeCompareService):
    def __init__(self, data_dir, references, flows):
        self.root = Path(data_dir) / 'research/r08-flow-benchmarks'
        self.lock = threading.RLock()
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.references = references
        self.flows = flows

    def start(self, selection):
        selection = Selection.model_validate(selection)
        with self.lock:
            # Resolve via owners, not client-supplied snapshots, paths or hashes.
            ref_manifest = self.references.artifact(selection.reference_id, 'manifest.json')
            flow_manifest = self.flows.artifact(selection.flow_id, 'manifest.json')
            hashes = [sha256_file(ref_manifest), sha256_file(flow_manifest)]
            reference = json.loads(self.references.artifact(selection.reference_id, 'annotation.json').read_text())
            flow = json.loads(self.flows.artifact(selection.flow_id, 'result.json').read_text())
            frozen = Input.model_validate({'benchmark': {'reference': reference, 'flow': flow,
                'endpoint_seeds': selection.endpoint_seeds},
                'reference_revision': {'id': selection.reference_id, 'manifest_sha256': hashes[0]},
                'flow_run': {'id': selection.flow_id, 'manifest_sha256': hashes[1]}})

            def unchanged():
                paths = [self.references.artifact(selection.reference_id, 'manifest.json'),
                         self.flows.artifact(selection.flow_id, 'manifest.json')]
                if [sha256_file(path) for path in paths] != hashes:
                    raise ValueError('Benchmark source artifacts changed during publication')

            unchanged()
            ident = uuid4().hex
            folder = self.root / ident
            try:
                manifest = run(frozen, folder)
                unchanged()
            except Exception:
                if folder.is_dir() and not folder.is_symlink():
                    shutil.rmtree(folder)
                raise
            return {**manifest, 'id': ident,
                    'source_resolution': 'verified_local_artifacts_at_creation'}

    def list(self):
        with self.lock:
            rows = []
            for folder in sorted(self.root.iterdir()):
                try:
                    self.folder(folder.name)
                    rows.append({**read_verified(folder), 'id': folder.name})
                except (OSError, ValueError, KeyError):
                    continue
            return rows

    def artifact(self, ident, name):
        if name not in ('request.json', 'result.json', 'manifest.json'):
            raise ValueError('Unknown benchmark artifact')
        folder = self.folder(ident)
        read_verified(folder)
        return folder / name
