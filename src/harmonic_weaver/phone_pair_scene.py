"""Phone scenes target declared native controls; no synthetic pose channels."""
from __future__ import annotations
from harmonic_weaver.contract_codec import contract_id_from_manifest


def build_scene(target, manifest, baseline=None):
    if target != 'beacon':
        raise ValueError('Shaper uses the current laboratory; this scene is for Beacon Spatializer only')
    baseline = baseline or {}
    instrument = 'beacon-spatial'
    routes, defaults, silence = [], [], []

    def route(name, channels, transforms, capability, bindings, argument, reset):
        dest = {'instrument_id': instrument, 'capability': capability, 'bindings': bindings, 'argument': argument}
        routes.append({'route_id': name, 'route_version': 1, 'enabled': True,
                       'inputs': [{'channel': channel} for channel in channels],
                       'transforms': transforms, 'destination': dest,
                       'validity': {'held': 'reject', 'min_confidence': .5, 'invalid': 'release'}})
        defaults.append({'capability': capability, 'bindings': bindings, 'argument': argument, 'value': reset})

    def scale(lo, hi, a, b, rate):
        return [{'type': 'scale_range', 'in': [lo, hi], 'out': [a, b], 'clamp': True},
                {'type': 'slew_limiter', 'max_rate': rate, 'max_dt_ms': 100.0}]

    values = baseline.get('values', baseline)
    for n in range(1, 14):
        role = 'a' if n <= 6 else 'b' if n <= 12 else 'pair'
        gain = float(values.get(f'/beacon/gain/{n}', .8))
        if role == 'pair':
            inputs, transforms = ['phone-pair.synchrony'], scale(0, 1, gain, min(3, gain+.5), 3)
        else:
            inputs = [f'phone-{role}.sway_mps2', f'phone-{role}.pitch']
            transforms = [{'type': 'combine', 'operator': 'weighted_sum', 'weights': [1/6, 1/450]},
                          *scale(-.2, .7, gain*.8, min(3, gain*1.25), 3)]
        route(f'{role}-band-{n}', inputs, transforms, 'band_gain', {'N': n}, 'gain', gain)
        if role != 'pair':
            az = float(values.get(f'/beacon/az/{n}', 0))
            route(f'{role}-azimuth-{n}', [f'phone-{role}.yaw'], scale(-180, 180, max(-180, az-90), min(180, az+90), 180), 'band_azimuth', {'N': n}, 'azimuth_degrees', az)

    scene = {'scene_id': 'phone-pair-'+target, 'scene_version': 1,
             'name': 'Phone Pair · '+target, 'description': 'Source-domain phone IMU through Weaver into the selected native instrument. No physiology or browser synthesis.',
             'tags': ['experimental', 'phone', 'pair'], 'created_at_us': 0, 'updated_at_us': 0,
             'aggregators': [], 'routes': routes,
             'transition': {'policy': 'crossfade', 'duration_ms': 120, 'await_valid_ms': 300}}
    profile = {'instrument_id': instrument, 'instrument_contract_id': contract_id_from_manifest(manifest),
               'instrument_class': 'control_only',
               'silence_actions': silence, 'reset_defaults': defaults, 'rearm_fade_ms': 300}
    return scene, profile
