"""R04 shares owned-worker lifecycle while keeping its inventory/input contract."""
from .coincidence_service import CoincidenceService
from .relational_bank import Settings


class RelationalService(CoincidenceService):
    line='R04'
    module='harmonic_weaver.lab.research.relational_worker'
    artifacts=('request.json','input.json','result.json','manifest.json')

    def start(self,settings):
        return self._start({'request.json':Settings.model_validate(settings).model_dump()})

    def start_body(self,settings,selection,evaluation):
        from .relational_input import endpoint_snapshot
        settings=Settings.model_validate(settings)
        document=endpoint_snapshot(evaluation,selection)
        return self._start({'request.json':settings.model_dump(),'input.json':document})
