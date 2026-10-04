"""Bounded explicit UTF-8 table decoding shared by declared sensor imports."""
import csv
import hashlib
import io
import json
import math
import re
from datetime import datetime
from typing import Literal
from pydantic import Field, model_validator
from ..contracts import Contract

class Mapping(Contract):
    delimiter: Literal[",", ";", "\t"] = ","
    skip_rows: int = Field(default=0, ge=0, le=1000)
    index_column: str = Field(min_length=1, max_length=160)
    time_column: str = Field(min_length=1, max_length=160)
    time_units: Literal["seconds", "milliseconds", "microseconds"]
    channel_columns: dict[str, str] = Field(min_length=1, max_length=64)
    missing_tokens: list[str] = Field(default_factory=lambda: [""], max_length=32)
    missing_cause: str = Field(
        default="declared_csv_missing", min_length=1, max_length=160
    )

    @model_validator(mode="after")
    def columns(self):
        names = [name for name in [self.index_column, self.time_column, *self.channel_columns.values()] if name is not None]
        if len(set(names)) != len(names) or any(not 1 <= len(n) <= 160 for n in names):
            raise ValueError(
                "Mapped CSV columns must be nonempty, bounded and distinct"
            )
        if len(set(self.missing_tokens)) != len(self.missing_tokens) or any(
            len(t) > 160 for t in self.missing_tokens
        ):
            raise ValueError("Missing tokens must be unique bounded literal strings")
        return self


def iso_timestamp(text):
    # Explicit timezone and bounded fractional precision: never truncate ns silently.
    if not isinstance(text,str) or not re.fullmatch(
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})',text):
        raise ValueError('ISO time requires YYYY-MM-DDTHH:MM:SS, explicit Z/offset and at most 6 fractional digits')
    result=datetime.fromisoformat(text)
    if result.tzinfo is None:raise ValueError('ISO timezone must be explicit')
    return result


class ISOTimeMapping(Mapping):
    schema_version: Literal[2]
    time_units: Literal['iso8601']
    time_origin: str = Field(min_length=1,max_length=64)

    @model_validator(mode='after')
    def origin(self):
        iso_timestamp(self.time_origin)
        return self


class RowIndexMapping(Mapping):
    schema_version: Literal[3]
    index_mode: Literal['row_ordinal']
    index_column: None = None
    time_units: Literal['seconds', 'milliseconds', 'microseconds', 'iso8601']
    time_origin: str | None = Field(default=None, min_length=1, max_length=64)

    @model_validator(mode='after')
    def temporal_origin(self):
        if self.time_units == 'iso8601':
            iso_timestamp(self.time_origin)
        elif self.time_origin is not None:
            raise ValueError('Numeric row mapping cannot declare an ISO origin')
        return self


MappingConfig = Mapping | ISOTimeMapping | RowIndexMapping


def _rows(reader):
    try:
        yield from reader
    except csv.Error as exc:
        raise ValueError(f"Malformed CSV near line {reader.line_num}: {exc}") from exc


def decode(csv_text, mapping, *, max_samples=120000):
    if not isinstance(mapping, Mapping):
        mapping={2: ISOTimeMapping, 3: RowIndexMapping}.get(mapping.get('schema_version'), Mapping).model_validate(mapping)
    raw = csv_text.encode("utf-8")
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError("CSV exceeds 16 MiB UTF-8 budget")
    stream = io.StringIO(csv_text.lstrip("\ufeff"), newline="")
    for _ in range(mapping.skip_rows):
        if stream.readline() == "":
            raise ValueError("CSV header unavailable after skipped preamble")
    reader = csv.reader(stream, delimiter=mapping.delimiter, strict=True)
    try:
        rows = _rows(reader)
        header = next(rows)
    except StopIteration as exc:
        raise ValueError("CSV header required") from exc
    if (
        not header
        or len(set(header)) != len(header)
        or any(not name for name in header)
    ):
        raise ValueError("CSV header names must be nonempty and unique")
    required = [name for name in [
        mapping.index_column,
        mapping.time_column,
        *mapping.channel_columns.values(),
    ] if name is not None]
    if not set(required) <= set(header):
        raise ValueError("CSV mapped column missing from header")
    positions = {name: header.index(name) for name in required}
    origin=iso_timestamp(mapping.time_origin) if mapping.time_units == 'iso8601' else None
    scale = None if origin is not None else {"seconds": 1.0, "milliseconds": 0.001, "microseconds": 0.000001}[mapping.time_units]
    samples = []
    decoded_bytes = 0
    for row in rows:
        if len(row) != len(header):
            raise ValueError(f"CSV row {reader.line_num} has wrong column count")
        index_text = str(len(samples)) if isinstance(mapping, RowIndexMapping) else row[positions[mapping.index_column]]
        if not index_text.isascii() or not index_text.isdecimal():
            raise ValueError(
                f"CSV row {reader.line_num}: nonnegative integer index required"
            )
        try:
            cell_time=row[positions[mapping.time_column]]
            time=(iso_timestamp(cell_time)-origin).total_seconds() if origin is not None else float(cell_time)*scale
            if not math.isfinite(time) or time < 0:
                raise ValueError("nonfinite or negative source time")
            values, causes = {}, {}
            for channel, name in mapping.channel_columns.items():
                cell = row[positions[name]]
                if cell in mapping.missing_tokens:
                    values[channel] = None
                    causes[channel] = mapping.missing_cause
                else:
                    number = float(cell)
                    if not math.isfinite(number):
                        raise ValueError(f"Nonfinite value in {name}")
                    values[channel] = number
        except ValueError as exc:
            raise ValueError(f"CSV row {reader.line_num}: {exc}") from exc
        sample = {
            "index": int(index_text), "source_time_s": time,
            "values": values, "missing_causes": causes,
        }
        decoded_bytes += len(json.dumps(sample, ensure_ascii=True).encode("utf-8"))
        if decoded_bytes > 16 * 1024 * 1024:
            raise ValueError("Decoded CSV samples exceed 16 MiB budget")
        samples.append(sample)
        if len(samples) > max_samples:
            raise ValueError(f"CSV exceeds {max_samples} sample budget")
    provenance = {
        "raw_utf8_sha256": hashlib.sha256(raw).hexdigest(),
        "mapping": mapping.model_dump(), "header": header,
        "ignored_columns": [name for name in header if name not in required],
        "time_conversion_to_seconds": scale,
    }
    if origin is not None:
        provenance['time_conversion']={
            'kind':'iso8601_relative_seconds','origin':mapping.time_origin,
            'maximum_fractional_digits':6,
            'clock_order':'subtract declared ISO origin, then apply metadata Clock'}
    if isinstance(mapping, RowIndexMapping):
        provenance['index_generation'] = {
            'kind': 'row_ordinal', 'start': 0, 'step': 1,
            'basis': 'parsed data records after declared header; no rows discarded',
            'device_counter_observed': False,
            'limit': 'Contiguous generated indices cannot detect missing device samples; timestamps remain supplied'}
    return samples, provenance
