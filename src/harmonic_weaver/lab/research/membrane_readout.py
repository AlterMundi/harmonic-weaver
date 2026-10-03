"""R07 train-only attribute readout from frozen sound-derived RMS figures.

Targets enter this decoder, never the sound/membrane renderer. A successful
readout measures this configured channel, not a natural HIT mechanism.
"""

import json
from typing import Literal

import numpy as np
from pydantic import Field, model_validator, model_serializer

from ..cache import sha256_file
from ..contracts import Contract, Number
from ..evaluation.runner import digest


class Settings(Contract):
    ridge: Number = Field(default=0.1, gt=0, le=100)
    normalization: Literal["center_train", "standardize_train"] = "standardize_train"
    embargo_s: Number = Field(default=0.5, ge=0, le=120)
    shuffle_seed: int = Field(default=17, ge=0, le=2**31 - 1)


class Case(Contract):
    id: str = Field(min_length=1, max_length=80)
    role: Literal["train", "test"]
    recording_id: str = Field(min_length=1, max_length=160)
    subject_group: str = Field(min_length=1, max_length=80)
    targets: list[Number] = Field(min_length=1, max_length=8)
    projection_run_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")
    source_origin_s: Number | None = Field(default=None, ge=0)
    pcm_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    projection_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    start_sample: int = Field(ge=0)
    stop_sample_exclusive: int = Field(gt=0)
    sample_rate: int = Field(ge=8000, le=96000)
    rms: list[Number] = Field(min_length=4, max_length=1024)

    @model_serializer(mode="wrap")
    def serialize(self, handler):
        value = handler(self)
        if self.source_origin_s is None:
            value.pop("source_origin_s", None)
        return value

    @model_validator(mode="after")
    def support(self):
        if self.start_sample >= self.stop_sample_exclusive or any(
            v < 0 for v in self.rms
        ):
            raise ValueError("Nonempty sample window and nonnegative RMS required")
        return self


class Dataset(Contract):
    schema_version: Literal[1] = 1
    provider: Literal["synthetic", "r07_snapshot"]
    reservation: Literal["within_take", "take", "subject"]
    attribute_ids: list[str] = Field(min_length=1, max_length=8)
    attribute_units: list[str] = Field(min_length=1, max_length=8)
    grid_x: int = Field(ge=2, le=32)
    grid_y: int = Field(ge=2, le=32)
    medium_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    settings: Settings = Field(default_factory=Settings)
    cases: list[Case] = Field(min_length=5, max_length=64)

    @model_validator(mode="after")
    def split(self):
        dims = len(self.attribute_ids)
        if len(set(self.attribute_ids)) != dims or len(self.attribute_units) != dims:
            raise ValueError(
                "Unique attributes and one explicit unit per attribute required"
            )
        if any(
            not v.strip() or len(v) > 80
            for v in self.attribute_ids + self.attribute_units
        ):
            raise ValueError("Nonempty bounded attribute IDs and units required")
        if len({c.id for c in self.cases}) != len(self.cases):
            raise ValueError("Unique case IDs required")
        windows = [
            (c.pcm_sha256, c.start_sample, c.stop_sample_exclusive, c.sample_rate)
            for c in self.cases
        ]
        if len(set(windows)) != len(windows):
            raise ValueError("The same PCM window cannot count as multiple cases")
        if any(
            len(c.targets) != dims or len(c.rms) != self.grid_x * self.grid_y
            for c in self.cases
        ):
            raise ValueError(
                "Targets and RMS must match ordered attribute/grid inventories"
            )
        train = [c for c in self.cases if c.role == "train"]
        test = [c for c in self.cases if c.role == "test"]
        if len(train) < 3 or len(test) < 2:
            raise ValueError("At least three training and two reserved cases required")
        for a in train:
            for b in test:
                if a.projection_sha256 == b.projection_sha256:
                    raise ValueError(
                        "The same frozen projection cannot be both train and test"
                    )
                same_pcm = a.pcm_sha256 == b.pcm_sha256
                same_recording = a.recording_id == b.recording_id
                if self.reservation != "within_take" and (same_pcm or same_recording):
                    raise ValueError("Reserved recording or PCM appears in training")
                if self.reservation == "subject" and a.subject_group == b.subject_group:
                    raise ValueError("Subject group reservation violated")
                if same_pcm and a.sample_rate != b.sample_rate:
                    raise ValueError(
                        "Identical PCM cannot declare different sample clocks"
                    )
                if same_pcm or same_recording:
                    if not same_pcm and (
                        a.source_origin_s is None or b.source_origin_s is None
                    ):
                        raise ValueError(
                            "Different PCM from one recording requires verified source-clock origins"
                        )
                    if same_pcm and a.source_origin_s != b.source_origin_s:
                        raise ValueError(
                            "Identical PCM cannot declare different source-clock origins"
                        )
                    if (
                        (a.source_origin_s or 0.0)
                        + a.stop_sample_exclusive / a.sample_rate
                        + self.settings.embargo_s
                        > (b.source_origin_s or 0.0) + b.start_sample / b.sample_rate
                    ):
                        raise ValueError(
                            "Within-take training must precede test with explicit embargo"
                        )
        return self


class Selection(Contract):
    id: str = Field(min_length=1, max_length=80)
    projection_run_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    role: Literal["train", "test"]
    recording_id: str = Field(min_length=1, max_length=160)
    subject_group: str = Field(min_length=1, max_length=80)
    targets: list[Number] = Field(min_length=1, max_length=8)


class Config(Contract):
    schema_version: Literal[1] = 1
    reservation: Literal["within_take", "take", "subject"] = "take"
    attribute_ids: list[str] = Field(
        default_factory=lambda: ["declared_attribute"], min_length=1, max_length=8
    )
    attribute_units: list[str] = Field(
        default_factory=lambda: ["dimensionless"], min_length=1, max_length=8
    )
    settings: Settings = Field(default_factory=Settings)

    @model_validator(mode="after")
    def attributes(self):
        if len(set(self.attribute_ids)) != len(self.attribute_ids) or len(
            self.attribute_units
        ) != len(self.attribute_ids):
            raise ValueError("Unique attributes and one unit per attribute required")
        if any(
            not v.strip() or len(v) > 80
            for v in self.attribute_ids + self.attribute_units
        ):
            raise ValueError("Nonempty bounded attribute IDs and units required")
        return self


class Request(Config):
    cases: list[Selection] = Field(min_length=5, max_length=64)


def snapshot(request, service):
    """Read verified local R07 artifacts; labels never influence figure creation.

    The service resolves IDs, checks complete jobs and verifies their artifacts.
    Snapshot freezes the RMS, not source PCM, media or any pose observations.
    """
    request = Request.model_validate(request)
    cases = []
    inventory = None
    captured = []
    for selection in request.cases:
        path = service.artifact(selection.projection_run_id, "result.json")
        before = sha256_file(path)
        report = json.loads(path.read_text())
        if sha256_file(path) != before:
            raise ValueError("Projection changed during readout snapshot")
        source = report["request"]
        current = (source["grid_x"], source["grid_y"], digest(source["membrane"]))
        if inventory is not None and current != inventory:
            raise ValueError(
                "Readout requires the same declared medium and spatial grid"
            )
        inventory = current
        field = report["window"]
        origin = None
        if hasattr(service, "audio_source"):
            try:
                audio = service.audio_source(selection.projection_run_id)
                manifest_path = audio.with_name("manifest.json")
                manifest = json.loads(manifest_path.read_text())
                if sha256_file(manifest_path) != report["source_manifest_sha256"]:
                    raise ValueError("Source-clock metadata differs from frozen projection")
                preparation = manifest["preparation"]
                clock = preparation.get(
                    "selection", preparation.get("excitation", {}).get("selection", {})
                )
                origin = clock.get("start_s")
            except (OSError, ValueError):
                # Historical figures remain usable without their source PCM;
                # cross-PCM reservations cannot then assert a source offset.
                origin = None
        cases.append(
            Case(
                **selection.model_dump(exclude={"projection_run_id"}),
                projection_run_id=selection.projection_run_id,
                source_origin_s=origin,
                pcm_sha256=report["source_component_sha256"],
                projection_sha256=before,
                start_sample=field["start_sample"],
                stop_sample_exclusive=field["stop_sample_exclusive"],
                sample_rate=field["sample_rate"],
                rms=np.asarray(field["rms"]).ravel().tolist(),
            )
        )
        captured.append((selection.projection_run_id, before))
    for ident, expected in captured:
        if sha256_file(service.artifact(ident, "result.json")) != expected:
            raise ValueError("Projection changed during readout snapshot")
    return Dataset(
        provider="r07_snapshot",
        reservation=request.reservation,
        attribute_ids=request.attribute_ids,
        attribute_units=request.attribute_units,
        settings=request.settings,
        grid_x=inventory[0],
        grid_y=inventory[1],
        medium_sha256=inventory[2],
        cases=cases,
    )


def features(dataset):
    raw = np.asarray([case.rms for case in dataset.cases])
    magnitude = np.linalg.norm(raw, axis=1, keepdims=True)
    shape = np.divide(raw, magnitude, out=np.zeros_like(raw), where=magnitude > 0)
    return {"rms_full": raw, "rms_shape": shape, "rms_magnitude": magnitude}


def fit(x, targets, settings):
    mean = x.mean(axis=0)
    scale = (
        x.std(axis=0)
        if settings.normalization == "standardize_train"
        else np.ones(x.shape[1])
    )
    # Do not turn roundoff in a constant normalized shape into unit variance.
    # Relative threshold still permits small raw membrane displacements.
    resolution = (
        64
        * np.finfo(float).eps
        * np.maximum(np.max(np.abs(x), axis=0), np.finfo(float).tiny)
    )
    scale = np.where(scale > resolution, scale, 1.0)
    centered = (x - mean) / scale
    target_mean = targets.mean(axis=0)
    # Dual solve bounds work by <=64 cases rather than a 1024-point grid.
    coefficients = centered.T @ np.linalg.solve(
        centered @ centered.T + settings.ridge * np.eye(len(x)),
        targets - target_mean,
    )
    model = {
        "input_mean": mean.tolist(),
        "input_scale": scale.tolist(),
        "target_mean": target_mean.tolist(),
        "coefficients": coefficients.tolist(),
    }
    Contract.finite_tree(model)
    return model


def predict(model, x):
    values = (x - model["input_mean"]) / model["input_scale"]
    return np.asarray(model["target_mean"]) + values @ np.asarray(model["coefficients"])


def calculate(dataset):
    dataset = Dataset.model_validate(dataset)
    train = np.asarray([i for i, c in enumerate(dataset.cases) if c.role == "train"])
    test = np.asarray([i for i, c in enumerate(dataset.cases) if c.role == "test"])
    targets = np.asarray([c.targets for c in dataset.cases])
    training_targets = targets[train]
    permutation = np.random.default_rng(dataset.settings.shuffle_seed).permutation(
        len(train)
    )
    models = {}
    predictions = {
        "training_mean": np.tile(training_targets.mean(axis=0), (len(test), 1))
    }
    for name, values in features(dataset).items():
        for control, y in (
            (name, training_targets),
            (name + "_training_shuffle", training_targets[permutation]),
        ):
            model = fit(values[train], y, dataset.settings)
            models[control] = model
            predictions[control] = predict(model, values[test])
    rows = []
    for index, original in enumerate(test):
        actual = targets[original]
        rows.append(
            {
                "case_id": dataset.cases[original].id,
                "actual": actual.tolist(),
                "predictions": {k: v[index].tolist() for k, v in predictions.items()},
                "squared_error": {
                    k: ((v[index] - actual) ** 2).tolist()
                    for k, v in predictions.items()
                },
            }
        )
    result = {
        "schema_version": 1,
        "line": "R07",
        "kind": "reserved_attribute_readout",
        "dataset_sha256": digest(dataset.model_dump()),
        "attribute_ids": dataset.attribute_ids,
        "attribute_units": dataset.attribute_units,
        "training_case_ids": [dataset.cases[i].id for i in train],
        "reserved_case_ids": [dataset.cases[i].id for i in test],
        "training_shuffle_case_ids": [dataset.cases[train[i]].id for i in permutation],
        "models": models,
        "rows": rows,
        "common_count": len(test),
        "mean_squared_error": {
            k: np.mean((v - targets[test]) ** 2, axis=0).tolist()
            for k, v in predictions.items()
        },
        "limits": [
            "All readouts score the same reserved cases; each window has equal weight, not independent subject evidence",
            "Targets/recording/subject IDs are human declarations; hashes detect some aliases, not biometric identity",
            "RMS is sound-derived displacement proxy; no pose or targets enter the membrane renderer",
            "Shape uses rowwise L2 normalization; zero fields map to a zero shape, not missing data",
            "Magnitude is a spatial grid L2 norm, not calibrated loudness or physical energy",
            "Normalization, intercept and ridge fit training only; shuffled labels use the same features and capacity",
            "Shuffle does not preserve temporal autocorrelation; no significance or causal claim follows",
            "Successful decoding of an explicitly encoded attribute measures a configured channel, not HIT",
            "Settings selected after test exposure are exploratory; no prospective blindness is certified",
        ],
    }
    Contract.finite_tree(result)
    return result
