"""Owned subprocesses for sound-only transient control banks."""

from .coincidence_service import CoincidenceService
from .membrane_controls import Request
from .membrane_controls_run import verification


class ControlService(CoincidenceService):
    line = "R07-CONTROLS"
    module = "harmonic_weaver.lab.research.membrane_controls_worker"
    artifacts = ("request.json", "result.json", "manifest.json")

    def start(self, request):
        request = Request.model_validate(request)
        return self._start({"request.json": request.model_dump()})

    def report(self, ident):
        with self.lock:
            value = super().report(ident)
            process = self.processes.get(ident)
            return {
                **value,
                "worker_active": process is not None and process.poll() is None,
            }

    def _verification(self, ident, *, recompute=False):
        from ..cache import sha256_file

        folder = self.folder(ident)
        status = verification(folder / "computed", recompute=recompute)
        outer = Request.model_validate_json(
            (folder / "request.json").read_text()
        ).model_dump()
        inner = Request.model_validate_json(
            (folder / "computed/request.json").read_text()
        ).model_dump()
        if outer != inner:
            raise ValueError("Control worker request differs from verified calculation")
        if sha256_file(folder / "result.json") != status["verified_result_sha256"]:
            raise ValueError("Control worker result differs from verified calculation")
        return status

    def verification(self, ident, *, recompute=False):
        super().artifact(ident, "result.json")
        return self._verification(ident, recompute=recompute)

    def artifact(self, ident, name):
        path = super().artifact(ident, name)
        if name != "manifest.json":
            # Historical integrity remains readable; rerendering is explicit.
            self._verification(ident, recompute=False)
        return path
