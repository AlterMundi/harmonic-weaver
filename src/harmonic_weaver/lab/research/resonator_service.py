"""R05 inventory shares owned-worker lifecycle; download verifies full PCM."""
from .coincidence_service import CoincidenceService
from .resonator_render import Render
from .resonator_artifacts import verify
from .projection_reader import ProjectionReader


class ResonatorService(CoincidenceService):
    line = 'R05'
    module = 'harmonic_weaver.lab.research.resonator_worker'
    artifacts = ('request.json','input.json','sum.wav','voices.wav','quadrature.wav','manifest.json',
                 'result.json','excited-sum.wav','excited-voices.wav','excited-quadrature.wav',
                 'mapped-sum.wav','mapped-voices.wav','mapped-quadrature.wav')

    def __init__(self,data_dir):
        super().__init__(data_dir);self.projection_reader=ProjectionReader()

    def projection(self,ident,request):
        with self.lock:
            if self.closed:raise ValueError('R05 service is closed')
            if self.report(ident)['status']!='complete':raise ValueError('Completed R05 run required')
            from .model_projection import project
            return project(self.folder(ident),request,reader=self.projection_reader)

    def close(self):
        super().close();self.projection_reader.close()

    def start(self, request, document):
        if set(request) - {'resonators','excitation','render','mapping'}:
            raise ValueError('Unknown R05 request field')
        prepared = Render(document, request.get('resonators',{}),
                          request.get('excitation',{}), request.get('render',{}))
        frozen = {'resonators':prepared.resonators.model_dump(),
                  'excitation':prepared.excitation['settings'], 'render':prepared.settings.model_dump()}
        if 'mapping' in request:
            from .parameter_render import Render as ParameterRender
            carriers={**frozen['resonators'],'coupling_per_s':0.,'topology':'isolated','adjacency':None}
            mapped=ParameterRender(document,carriers,request['mapping'],frozen['render'])
            frozen['mapping']=mapped.mapping.model_dump(exclude_none=True)
        return self._start({'request.json':frozen, 'input.json':document})

    def artifact(self, ident, name):
        if name not in self.artifacts:
            raise ValueError('Unknown R05 artifact')
        folder = self.folder(ident); report = self.report(ident)
        paired=report.get('kind')=='mechanism_comparison'
        if name.startswith(('excited-','mapped-')):
            arm,file=name.split('-',1);path=folder/arm/file
        else:path=folder/name
        if path.is_symlink() or not path.is_file():
            raise ValueError('R05 artifact unavailable')
        if name == 'manifest.json': return path
        if report['status'] != 'complete':
            raise ValueError('R05 result is not complete')
        if paired:
            from .mechanism_run import verify as verify_pair
            verify_pair(folder)
            if name.startswith(('excited-','mapped-')):
                verified_arm=verify(folder/arm)
                if file not in verified_arm['output_hashes']:
                    raise ValueError('R05 arm artifact is not in verified inventory')
        else:
            verified=verify(folder)
            if name not in {*verified['input_hashes'],*verified['output_hashes']}:
                raise ValueError('R05 artifact is not in verified inventory')
        return path
