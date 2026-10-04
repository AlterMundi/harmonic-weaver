"""Periodic per-port shifts preserve input powers, not finite output responses."""
import math

import numpy as np

from .resonators import Resonators


def inputs(indices, span, vector, shifts):
    calendars = [sorted((index + shift) % span for index in indices) for shift in shifts]
    original = np.zeros((span, len(vector)))
    shifted = np.zeros_like(original)
    for voice, (weight, calendar) in enumerate(zip(vector, calendars)):
        original[indices, voice] = weight
        shifted[calendar, voice] = weight
    a, b = np.fft.rfft(original, axis=0), np.fft.rfft(shifted, axis=0)
    scale = max(float(np.max(abs(a)**2)), 1e-30)
    power_error = float(np.max(abs(abs(a)**2-abs(b)**2)) / scale)
    cross_error = 0.
    for i in range(len(vector)):
        for j in range(len(vector)):
            cross_error = max(cross_error, float(np.max(abs(a[:, i]*a[:, j].conj()-b[:, i]*b[:, j].conj())) / scale))
    return calendars, {
        'power_max_relative_error': power_error,
        'cross_spectrum_max_relative_change': cross_error,
        'shared_shift': len(set(shifts)) == 1,
        'changed_input_samples': int(np.count_nonzero(original != shifted)),
    }


def render(settings, calendars, phases):
    sr = settings.medium.sample_rate
    span = math.ceil(settings.excitation_span_s*sr)
    total = span + math.ceil(settings.tail_s*sr)
    voices = len(calendars)
    vector = np.full(voices, settings.impulse_strength/math.sqrt(voices))
    kernel = Resonators(settings.medium)
    event_set = set().union(*map(set, calendars))
    squares = peak = integral = tail_squares = 0.
    trace = []
    for start in range(0, total, settings.block_size):
        end = min(total, start+settings.block_size)
        impulses = np.zeros((end-start, voices))
        for voice, calendar in enumerate(calendars):
            for index in calendar:
                if start <= index < end:
                    impulses[index-start, voice] = vector[voice]
        block = kernel.render(impulses, excitation_phases_rad=phases)
        summed, norm = block['sum'], block['state_norm_squared']
        squares += float(np.dot(summed, summed)); peak = max(peak, float(np.abs(summed).max()))
        integral += float(norm.sum())/sr
        tail = summed[max(0, span-start):]; tail_squares += float(np.dot(tail, tail))
        for i in range(end-start):
            index = start+i
            if index % settings.trace_stride == 0 or index in event_set or index == total-1:
                trace.append({'sample_index': index, 'time_s': (index+1)/sr, 'sum': float(summed[i]),
                              'state_norm_squared': float(norm[i]), 'instrument_tail': index >= span})
    return {'voice_event_samples': calendars,
            'input_squared_norm': float(np.dot(vector, vector))*settings.event_count,
            'metrics': {'rms': math.sqrt(squares/total), 'peak_abs': peak,
                        'state_norm_time_integral': integral,
                        'final_state_norm_squared': float(np.vdot(kernel.state, kernel.state).real),
                        'tail_rms': math.sqrt(tail_squares/(total-span)) if total > span else None},
            'trace': trace}


def probe(settings, events, reference, phases=None):
    span = math.ceil(settings.excitation_span_s*settings.medium.sample_rate)
    vector = np.full(len(settings.medium.ratios), settings.impulse_strength/math.sqrt(len(settings.medium.ratios)))
    controls = []
    for index, shifts in enumerate(settings.circular_shift_controls):
        conditions = {}
        for name, indices in events.items():
            calendars, checks = inputs(indices, span, vector, shifts)
            condition = render(settings, calendars, phases)
            condition['spectral_preservation'] = checks
            condition['metric_difference_vs_base'] = {
                key: value-reference[name]['metrics'][key] if value is not None else None
                for key, value in condition['metrics'].items()}
            conditions[name] = condition
        controls.append({'index': index, 'shifts_samples': shifts, 'conditions': conditions})
    return controls


def validate(outputs, settings, events, reference):
    span = math.ceil(settings.excitation_span_s*settings.medium.sample_rate)
    total = span+math.ceil(settings.tail_s*settings.medium.sample_rate)
    vector = np.full(len(settings.medium.ratios), settings.impulse_strength/math.sqrt(len(settings.medium.ratios)))
    if len(outputs) != len(settings.circular_shift_controls):
        raise ValueError('Circular shift inventory mismatch')
    for index, (output, shifts) in enumerate(zip(outputs, settings.circular_shift_controls)):
        if output['index'] != index or output['shifts_samples'] != shifts or set(output['conditions']) != set(events):
            raise ValueError('Circular shifts differ from frozen configuration')
        for name, indices in events.items():
            calendars, checks = inputs(indices, span, vector, shifts)
            condition = output['conditions'][name]
            actual=condition['spectral_preservation']
            matching=set(actual)==set(checks) and all(
                math.isclose(actual[key],value,rel_tol=1e-12,abs_tol=1e-12) if type(value) is float else actual[key]==value
                for key,value in checks.items())
            if condition['voice_event_samples'] != calendars or not matching:
                raise ValueError('Circular shift input spectrum/calendar differs')
            if condition['input_squared_norm'] != reference[name]['input_squared_norm']:
                raise ValueError('Circular shift input dose differs')
            metrics = condition['metrics']
            if set(metrics) != set(reference[name]['metrics']):
                raise ValueError('Circular shift metric inventory differs')
            for key, value in metrics.items():
                if key == 'tail_rms' and span == total:
                    if value is not None: raise ValueError('Empty shifted tail must be null')
                elif type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                    raise ValueError('Invalid circular shift metric')
            expected = {key: value-reference[name]['metrics'][key] if value is not None else None for key, value in metrics.items()}
            if condition['metric_difference_vs_base'] != expected:
                raise ValueError('Circular shift metric differences differ')
            expected_indices = sorted(set(range(0, total, settings.trace_stride)) | set().union(*map(set, calendars)) | {total-1})
            if [row['sample_index'] for row in condition['trace']] != expected_indices:
                raise ValueError('Circular shift trace support differs')
            for row in condition['trace']:
                if row['time_s'] != (row['sample_index']+1)/settings.medium.sample_rate or row['instrument_tail'] != (row['sample_index'] >= span):
                    raise ValueError('Circular shift trace clock differs')
                if any(type(row[key]) not in (int, float) or not math.isfinite(row[key]) for key in ('sum', 'state_norm_squared')) or row['state_norm_squared'] < 0:
                    raise ValueError('Invalid circular shift trace')
