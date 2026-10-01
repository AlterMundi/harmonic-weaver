"""R05 inventory shares owned-worker lifecycle; download verifies full PCM."""
from .coincidence_service import CoincidenceService
from .resonator_render import Render
from .resonator_artifacts import verify


class ResonatorService(CoincidenceService):
    line = 'R05'
    module = 'harmonic_weaver.lab.research.resonator_worker'
    artifacts = ('request.json','input.json','sum.wav','voices.wav','manifest.json')

    def start(self, request, document):
        if set(request) - {'resonators','excitation','render'}:
            raise ValueError('Unknown R05 request field')
        prepared = Render(document, request.get('resonators',{}),
                          request.get('excitation',{}), request.get('render',{}))
        frozen = {'resonators':prepared.resonators.model_dump(),
                  'excitation':prepared.excitation['settings'], 'render':prepared.settings.model_dump()}
        return self._start({'request.json':frozen, 'input.json':document})

    def artifact(self, ident, name):
        if name not in self.artifacts:
            raise ValueError('Unknown R05 artifact')
        folder = self.folder(ident); report = self.report(ident); path = folder/name
        if path.is_symlink() or not path.is_file():
            raise ValueError('R05 artifact unavailable')
        if name == 'manifest.json': return path
        if report['status'] != 'complete':
            raise ValueError('R05 result is not complete')
        verify(folder)
        return path
