"""Known-component synthetic R11 control; never estimates EEG signal from a mixture."""
import math
from typing import Literal
from pydantic import Field, model_validator
from ..contracts import Contract


class Tone(Contract):
    amplitude: float = Field(ge=0, le=1e6)
    frequency_hz: float = Field(gt=0, le=50000)
    phase_rad: float = Field(ge=-1000, le=1000)
    dc_offset: float = Field(ge=-1e6, le=1e6)


class Config(Contract):
    schema_version: Literal[1] = 1
    line: Literal['R11'] = 'R11'
    kind: Literal['synthetic_known_components'] = 'synthetic_known_components'
    sample_rate_hz: float = Field(gt=0, le=100000)
    sample_count: int = Field(ge=2, le=20000)
    signal: Tone
    noise: Tone
    start_index: int = Field(ge=0)
    stop_index: int = Field(gt=0)
    remove_mean: bool
    missing_indices: list[int] = Field(default_factory=list, max_length=20000)
    excluded_indices: list[int] = Field(default_factory=list, max_length=20000)

    @model_validator(mode='after')
    def support(self):
        if not self.start_index < self.stop_index <= self.sample_count:
            raise ValueError('Require 0 <= start < stop <= sample_count; stop is exclusive')
        for tone in (self.signal, self.noise):
            if tone.frequency_hz >= self.sample_rate_hz / 2:
                raise ValueError('Synthetic frequencies must be strictly below Nyquist')
        for indices in (self.missing_indices, self.excluded_indices):
            if len(set(indices)) != len(indices) or any(i < 0 or i >= self.sample_count for i in indices):
                raise ValueError('Indices must be unique and within the generated record')
        return self


def calculate(config):
    config = Config.model_validate(config)
    missing, excluded = set(config.missing_indices), set(config.excluded_indices)
    samples, support = [], []
    for index in range(config.sample_count):
        time = index / config.sample_rate_hz
        values = [tone.dc_offset + tone.amplitude * math.sin(2 * math.pi * tone.frequency_hz * time + tone.phase_rad)
                  for tone in (config.signal, config.noise)]
        observed = index not in missing
        included = observed and index not in excluded and config.start_index <= index < config.stop_index
        samples.append({'index': index, 'source_time_s': time,
            'signal': values[0] if observed else None, 'noise': values[1] if observed else None,
            'mixture': sum(values) if observed else None,
            'missing_cause': 'synthetic_dropout' if not observed else None,
            'explicitly_excluded': index in excluded, 'used_for_power': included})
        if included:
            support.append(values)
    powers, means = [None, None], [None, None]
    status, db = 'insufficient_support', None
    if len(support) >= 2:
        for channel in range(2):
            values = [row[channel] for row in support]
            means[channel] = math.fsum(values) / len(values)
            center = means[channel] if config.remove_mean else 0.0
            powers[channel] = math.fsum((v - center) ** 2 for v in values) / len(values)
        ps, pn = powers
        if ps == 0 and pn == 0:
            status = 'both_zero'
        elif pn == 0:
            status = 'noise_zero'
        elif ps == 0:
            status = 'signal_zero'
        else:
            status = 'finite'
            db = 10 * (math.log10(ps) - math.log10(pn))
    return {'schema_version': 1, 'line': 'R11', 'kind': 'synthetic_known_components',
        'metric_version': 'known_component_mean_square_v1', 'config': config.model_dump(),
        'samples': samples, 'used_indices': [s['index'] for s in samples if s['used_for_power']],
        'metrics': {'support_count': len(support), 'signal_mean': means[0], 'noise_mean': means[1],
            'signal_power': powers[0], 'noise_power': powers[1], 'power_units': 'dimensionless_squared',
            'snr_db': db, 'status': status},
        'limits': ['Synthetic dimensionless tones; designated noise is a known control, not physiological noise',
            'Equal-weight mean-square power on identical retained sample indices; no interpolation or time weighting',
            'Optional mean removal is computed independently on the same retained support for each component',
            'Signal/noise separation is provided by construction, never inferred from the mixture',
            'Zero powers and insufficient support produce explicit statuses and null dB, never Infinity',
            'No hardware, EEG inference, filtering, mental-state interpretation or physical SNR validation']}
