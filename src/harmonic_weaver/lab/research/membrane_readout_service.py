"""Bounded R07 figure readouts; portable settings separate from local cases."""

from pathlib import Path
import re
import threading
from uuid import uuid4

from .membrane_readout import Request, Dataset, snapshot
from .membrane_labels import Settings as LabelSettings
from .membrane_readout_run import run, verify


class ReadoutService:
    artifacts = ("dataset.json", "result.json", "manifest.json")

    def __init__(self, data_dir, projections, evaluation=None):
        self.root = Path(data_dir) / "research/r07-readout"
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.projections = projections
        self.evaluation = evaluation
        self.lock = threading.RLock()

    def folder(self, ident):
        if not isinstance(ident, str) or not re.fullmatch("[a-f0-9]{32}", ident):
            raise ValueError("Invalid readout id")
        folder = self.root / ident
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError("Readout unavailable")
        return folder

    def start(self, request):
        request = Request.model_validate(request)
        with self.lock:
            dataset = snapshot(request, self.projections, self.evaluation)
            ident = uuid4().hex
            stage = self.root / ("." + ident + ".staging")
            run(dataset, stage)
            verify(stage, recompute=True)
            stage.rename(self.root / ident)
            return self.verification(ident)

    def verification(self, ident, *, recompute=False):
        with self.lock:
            return {**verify(self.folder(ident), recompute=recompute), "id": ident}

    def replay_request(self, ident):
        """Recover local selections, not body identity or current live state."""
        with self.lock:
            dataset = Dataset.model_validate_json(self.artifact(ident, "dataset.json").read_text())
            if dataset.provider != "r07_snapshot" or any(c.projection_run_id is None for c in dataset.cases):
                raise ValueError("This archive has no recoverable local projection selection")
            cases, profiles = [], []
            for case in dataset.cases:
                value = {key:getattr(case,key) for key in
                         ("id","projection_run_id","role","recording_id","subject_group","targets")}
                profile = None
                if case.computed_label is not None:
                    profile = LabelSettings.model_validate({k:v for k,v in case.computed_label["request"].items()
                                                           if k != "projection_run_id"}).model_dump()
                    value["computed_label"] = profile
                profiles.append(profile)
                cases.append(value)
            common = profiles[0] if all(p == profiles[0] for p in profiles) else None
            return Request(reservation=dataset.reservation, attribute_ids=dataset.attribute_ids,
                           attribute_units=dataset.attribute_units, settings=dataset.settings,
                           label_settings=common, cases=cases).model_dump()

    def list(self):
        with self.lock:
            rows = []
            for folder in sorted(self.root.iterdir()):
                if (
                    not folder.is_symlink()
                    and folder.is_dir()
                    and re.fullmatch("[a-f0-9]{32}", folder.name)
                ):
                    try:
                        rows.append(self.verification(folder.name))
                    except (OSError, ValueError, KeyError):
                        continue
            return rows

    def artifact(self, ident, name):
        if name not in self.artifacts:
            raise ValueError("Unknown readout artifact")
        with self.lock:
            self.verification(ident)
            return self.folder(ident) / name
