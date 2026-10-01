"""R06 owns its subprocess inventory; live synthesis remains independent."""
from .coincidence_service import CoincidenceService
from .activation_bank import Settings,schedules
from .activation_artifacts import verify


class ActivationService(CoincidenceService):
    line='R06'
    module='harmonic_weaver.lab.research.activation_worker'
    artifacts=('request.json','result.json','manifest.json')

    def start(self,settings):
        settings=Settings.model_validate(settings);schedules(settings)
        return self._start({'request.json':settings.model_dump()})

    def artifact(self,ident,name):
        path=super().artifact(ident,name)
        if name!='manifest.json':verify(self.folder(ident))
        return path
