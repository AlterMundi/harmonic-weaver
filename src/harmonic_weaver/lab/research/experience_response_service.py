"""Content-addressed immutable declared responses; no inferred acceptance."""
import hashlib
import json
import threading
from pathlib import Path
from ..cache import atomic_json, sha256_file
from ..contracts import Contract
from .experience_protocol import Request as Protocol, validate_response
from .experience_response import Request, resolve
from .experience_transport_service import TransportService

FILES=('request.json','result.json','manifest.json')


def identity(request):
    return hashlib.sha256(json.dumps(request,sort_keys=True,separators=(',',':')).encode()).hexdigest()


class ResponseService(TransportService):
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research/r10-responses'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.lock=threading.RLock()

    @staticmethod
    def code_hashes():
        return {n:sha256_file(Path(__file__).parent/n) for n in
            ('experience_response.py','experience_response_service.py','experience_protocol.py','../contracts.py')}

    def read(self,ident):
        folder=self.folder(ident)
        for n in FILES:
            p=folder/n
            if p.is_symlink() or not p.is_file() or p.stat().st_size>16*1024*1024:
                raise ValueError('Regular bounded response artifacts required')
        hashes={n:sha256_file(folder/n) for n in FILES}
        manifest=json.loads((folder/'manifest.json').read_text())
        if manifest.get('schema_version')!=1 or manifest.get('kind')!='declared_response':
            raise ValueError('Invalid response manifest')
        if manifest.get('hashes')!={n:hashes[n] for n in FILES[:-1]}:
            raise ValueError('Response artifact hash mismatch')
        request=Request.model_validate_json((folder/'request.json').read_text())
        digest=identity(request.model_dump())
        if ident!=digest[:32] or manifest.get('request_sha256')!=digest:
            raise ValueError('Response content identity mismatch')
        result=json.loads((folder/'result.json').read_text());Contract.finite_tree(result)
        if result.get('request')!=request.model_dump() or result.get('schema_version')!=1 or result.get('line')!='R10':
            raise ValueError('Response input binding mismatch')
        protocol=Protocol.model_validate(result['protocol'])
        if result['trial']['trial_id']!=request.response.trial_id:
            raise ValueError('Response trial binding mismatch')
        transport=result.get('transport')
        if (transport is None)!=(request.transport_id is None) or transport is not None and transport['id']!=request.transport_id:
            raise ValueError('Response transport binding mismatch')
        validated=result['validated']
        if (validated.get('response')!=request.response.model_dump() or
                validated.get('participant_slot')!=protocol.participant_slot or
                validated.get('role')!=protocol.role):
            raise ValueError('Response declared ratings/role binding mismatch')
        current=manifest.get('code_hashes')==self.code_hashes()
        if current and result['validated']!=validate_response(protocol,request.response):
            raise ValueError('Response recomputation mismatch')
        for n,d in hashes.items():
            if (folder/n).is_symlink() or sha256_file(folder/n)!=d:
                raise ValueError('Response changed during verification')
        return {**manifest,'id':ident,'read_verification':'ratings_recomputed' if current else 'historical_integrity_only'}

    def start(self,protocols,transports,request):
        request=Request.model_validate(request);digest=identity(request.model_dump());ident=digest[:32]
        with self.lock:
            if (self.root/ident).exists():return self.read(ident)
            result=resolve(protocols,transports,request)
            folder=self.root/ident;folder.mkdir(mode=0o700,exist_ok=False)
            atomic_json(folder/'request.json',request.model_dump())
            atomic_json(folder/'result.json',result)
            atomic_json(folder/'manifest.json',{'schema_version':1,'line':'R10','kind':'declared_response',
                'request_sha256':digest,'code_hashes':self.code_hashes(),
                'hashes':{n:sha256_file(folder/n) for n in FILES[:-1]},
                'limits':result['limits']+['Sources verified at publication, not reverified on read',
                    'Hashes are not signed custody; identical responses are one content record',
                    'Corrections create new records; no implicit replacement or participant deduplication']})
            return self.read(ident)

    def artifact(self,ident,name):
        if name not in FILES:raise ValueError('Unknown response artifact')
        self.read(ident);return self.folder(ident)/name
