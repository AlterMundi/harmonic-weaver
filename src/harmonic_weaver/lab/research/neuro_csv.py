"""Explicit UTF-8 tabular import; no hardware, reference, scale or clock inferred."""

from typing import Literal

from pydantic import Field
from ..contracts import Contract
from .neuro_observations import Channel, Stream, inspect
from .spatial_observations import Clock
from .csv_table import MappingConfig, decode


class Metadata(Contract):
    source_id: str = Field(min_length=1, max_length=80)
    subject_slot: str = Field(min_length=1, max_length=80)
    provider: Literal["declared_import", "synthetic", "openbci_export"]
    hardware_description: str = Field(min_length=1, max_length=240)
    nominal_sample_rate_hz: float = Field(gt=0, le=100000)
    clock: Clock
    channels: list[Channel] = Field(min_length=1, max_length=64)




class Request(Contract):
    schema_version: Literal[1] = 1
    csv_text: str = Field(min_length=1, max_length=16 * 1024 * 1024)
    metadata: Metadata
    mapping: MappingConfig


def convert(request):
    request = Request.model_validate(request)
    metadata, mapping = request.metadata, request.mapping
    ids = {c.id for c in metadata.channels}
    if len(ids) != len(metadata.channels) or set(mapping.channel_columns) != ids:
        raise ValueError("CSV mapping must bind every declared channel exactly once")
    samples, provenance = decode(request.csv_text, mapping)
    converted = Stream.model_validate(
        {
            **metadata.model_dump(),
            "samples": samples,
            "raw_source_sha256": provenance['raw_utf8_sha256'],
        }
    )
    return {
        **inspect(converted),
        "import_provenance": {
            "adapter": "explicit_utf8_csv_v1",
            **provenance,
            "limits": [
                "UTF-8 source digest; keep original CSV and mapping locally",
                "No device-format autodetection, packet-counter unwrapping, filtering or value-unit conversion",
                "Time unit conversion is declared; it does not measure physical synchronization",
            ],
        },
    }
