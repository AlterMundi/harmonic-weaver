"""Owned subprocesses for sound-only transient control banks."""
from .coincidence_service import CoincidenceService
from .membrane_controls import Request
from .membrane_controls_run import verify
import json


class ControlService(CoincidenceService):
    line='R07-CONTROLS'
    module='harmonic_weaver.lab.research.membrane_controls_worker'
    artifacts=('request.json','result.json','manifest.json')

    def start(self,request):
        request=Request.model_validate(request)
        return self._start({'request.json':request.model_dump()})

    def report(self,ident):
        with self.lock:
            value=super().report(ident);process=self.processes.get(ident)
            return {**value,'worker_active':process is not None and process.poll() is None}

    def artifact(self,ident,name):
        path=super().artifact(ident,name)
        if name!='manifest.json':
            # Worker manifest wraps the computed contract. Verify its exact
            # completed internal calculation as well as published result hash.
            manifest=verify(self.folder(ident)/'computed')
            from ..cache import sha256_file
            outer=Request.model_validate_json((self.folder(ident)/'request.json').read_text()).model_dump()
            inner=Request.model_validate_json((self.folder(ident)/'computed/request.json').read_text()).model_dump()
            if outer!=inner:
                raise ValueError('Control worker request differs from verified calculation')
            if sha256_file(self.folder(ident)/'result.json')!=manifest['output']['sha256']:
                raise ValueError('Control worker result differs from verified calculation')
        return path
