"""Responses bound to frozen R10 questions/trials, not inferred from transport."""
import json
from typing import Annotated
from pydantic import Field
from ..contracts import Contract
from ..cache import sha256_file
from .experience_protocol import Response, validate_response

Id = Annotated[str, Field(pattern=r'^[a-f0-9]{32}$')]
Digest = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]


class Request(Contract):
    protocol_id: Id
    protocol_manifest_sha256: Digest
    response: Response
    transport_id: Id | None = None


def resolve(protocols, transports, request):
    request = Request.model_validate(request)
    manifest = protocols.artifact(request.protocol_id, 'manifest.json')
    digest = sha256_file(manifest)
    if digest != request.protocol_manifest_sha256:
        raise ValueError('Response references a different protocol manifest')
    protocol = json.loads(protocols.artifact(request.protocol_id, 'request.json').read_text())['protocol']
    result = json.loads(protocols.artifact(request.protocol_id, 'result.json').read_text())
    trial = next((t for t in result['trials'] if t['trial_id'] == request.response.trial_id), None)
    if trial is None:
        raise ValueError('Response references unknown frozen trial')
    validated = validate_response(protocol, request.response)
    transport = None
    if request.transport_id is not None:
        path = transports.artifact(request.transport_id, 'manifest.json')
        transport_digest = sha256_file(path)
        trace = json.loads(transports.artifact(request.transport_id, 'trace.json').read_text())
        if (trace['protocol_id'] != request.protocol_id or
                trace['protocol_manifest_sha256'] != digest or
                trace['trial_id'] != request.response.trial_id):
            raise ValueError('Response transport belongs to a different protocol or trial')
        binding = json.loads(transports.artifact(request.transport_id, 'binding.json').read_text())
        if binding['trial'] != trial:
            raise ValueError('Response transport frozen trial differs')
        transport = {'id': request.transport_id, 'manifest_sha256': transport_digest,
                     'summary': binding['summary']}
        if sha256_file(transports.artifact(request.transport_id, 'manifest.json')) != transport_digest:
            raise ValueError('Transport changed during response binding')
    if sha256_file(protocols.artifact(request.protocol_id, 'manifest.json')) != digest:
        raise ValueError('Protocol changed during response binding')
    return {'schema_version': 1, 'line': 'R10', 'request': request.model_dump(),
            'protocol': protocol, 'trial': trial, 'validated': validated,
            'transport': transport,
            'limits': ['Answers are declared, not verified participant identity or exposure',
                       'Optional transport reference does not establish listening or complete exposure',
                       'Null means unanswered, never zero or imputed physiology',
                       'Configured questions are not validated scientific scales']}
