"""R12 explicit CSV import into the existing measurement contract."""
from typing import Literal
from pydantic import Field
from ..contracts import Contract
from .csv_table import Mapping, decode
from .physiology import Request as Measurements, Channel, Trial, EvaluationBinding, calculate
from .spatial_observations import Clock


class Metadata(Contract):
    provider: Literal['synthetic', 'declared_import']
    source_id: str = Field(min_length=1, max_length=80)
    subject_slot: str = Field(min_length=1, max_length=80)
    task: str = Field(min_length=1, max_length=240)
    constraints: str = Field(min_length=1, max_length=400)
    clock: Clock
    channels: list[Channel] = Field(min_length=1, max_length=16)
    trials: list[Trial] = Field(min_length=1, max_length=32)
    max_gap_s: float = Field(default=2, gt=0, le=60)
    common_channel_ids: list[str] = Field(min_length=1, max_length=16)
    evaluation_binding: EvaluationBinding | None = None


class Request(Contract):
    schema_version: Literal[1] = 1
    csv_text: str = Field(min_length=1, max_length=16 * 1024 * 1024)
    metadata: Metadata
    mapping: Mapping


def convert(request):
    frozen = Request.model_validate(request)
    ids = {channel.id for channel in frozen.metadata.channels}
    if len(ids) != len(frozen.metadata.channels) or set(frozen.mapping.channel_columns) != ids:
        raise ValueError('CSV mapping must bind every declared measurement channel exactly once')
    samples, provenance = decode(frozen.csv_text, frozen.mapping, max_samples=20000)
    converted = Measurements.model_validate({**frozen.metadata.model_dump(),
        'samples': samples, 'raw_source_sha256': provenance['raw_utf8_sha256']})
    return {**calculate(converted), 'import_provenance': {
        'adapter': 'r12_explicit_utf8_csv_v1', **provenance,
        'limits': ['Original UTF-8 text and map must remain local',
                   'Values are already in declared channel units; no value conversion or scale inference',
                   'No sensor-format autodetection, filtering, packet unwrapping or calibration transfer',
                   'Time-unit conversion does not demonstrate physical synchronization']}}
