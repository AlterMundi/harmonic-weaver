"""Sound-only rectangular membrane proxy with fixed boundaries.

Modal displacement is dimensionless: PCM is a declared forcing proxy, not
measured pressure. This model does not simulate particles, sand or water.
"""
import numpy as np
from scipy.linalg import expm
from pydantic import Field, model_validator
from ..contracts import Contract, Number


class Settings(Contract):
    width_m: Number = Field(default=1., gt=0, le=10)
    height_m: Number = Field(default=1., gt=0, le=10)
    wave_speed_m_s: Number = Field(default=40., gt=0, le=1000)
    modes_x: int = Field(default=4, ge=1, le=16)
    modes_y: int = Field(default=4, ge=1, le=16)
    damping_per_s: Number = Field(default=2., ge=0, le=100)
    sample_rate: int = Field(default=48000, ge=8000, le=96000)
    excitation_x: Number = Field(default=.37, ge=0, le=1)
    excitation_y: Number = Field(default=.41, ge=0, le=1)
    forcing_gain: Number = Field(default=1., ge=0, le=100)

    @model_validator(mode='after')
    def valid(self):
        maximum = self.wave_speed_m_s / 2 * np.hypot(
            self.modes_x / self.width_m, self.modes_y / self.height_m)
        if maximum >= self.sample_rate / 2:
            raise ValueError('All retained modes must lie below Nyquist')
        return self


class Membrane:
    """q'' + 2γq' + ω²q = gain * shape(excitation) * PCM.

    Exact zero-order-hold integration; each PCM sample forces its interval.
    Outputs describe the right edge of that interval. State survives blocks.
    Shapes use unnormalized sine products; gain absorbs modal mass/pressure
    calibration. Geometry and wave speed determine frequencies independently
    of the harmonic ratios of the source instrument.
    """
    def __init__(self, settings):
        self.settings = Settings.model_validate(settings)
        s = self.settings
        self.indices = np.array([(m, n) for m in range(1, s.modes_x + 1)
                                 for n in range(1, s.modes_y + 1)])
        self.omega = np.pi * s.wave_speed_m_s * np.hypot(
            self.indices[:, 0] / s.width_m, self.indices[:, 1] / s.height_m)
        self.state = np.zeros((len(self.indices), 2))
        self.sample_index = 0
        forcing = self.shapes([s.excitation_x], [s.excitation_y])[0]
        self.transition = []
        self.input_step = []
        for omega, shape in zip(self.omega, forcing):
            generator = np.array([[0., 1., 0.],
                                  [-omega**2, -2*s.damping_per_s, s.forcing_gain*shape],
                                  [0., 0., 0.]])
            step = expm(generator / s.sample_rate)
            self.transition.append(step[:2, :2])
            self.input_step.append(step[:2, 2])
        self.transition = np.array(self.transition)
        self.input_step = np.array(self.input_step)

    def shapes(self, x, y):
        """Normalized coordinates; paired points × retained modes."""
        x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
        if x.ndim != 1 or x.shape != y.shape or not np.isfinite(x).all() or not np.isfinite(y).all() or (x < 0).any() or (x > 1).any() or (y < 0).any() or (y > 1).any():
            raise ValueError('Finite paired coordinates in [0,1] required')
        result = np.sin(np.pi*x[:, None]*self.indices[:, 0]) * np.sin(np.pi*y[:, None]*self.indices[:, 1])
        result[(x == 0) | (x == 1) | (y == 0) | (y == 1)] = 0.
        return result

    def reset(self):
        self.state.fill(0)
        self.sample_index = 0

    def field(self, modal_displacement, x, y):
        """Frames × paired points; no scaling, clipping or normalization."""
        q = np.asarray(modal_displacement, dtype=float)
        if q.ndim != 2 or q.shape[1] != len(self.indices) or not np.isfinite(q).all():
            raise ValueError('Finite frames × retained modes required')
        shapes = self.shapes(x, y)
        if q.size + shapes.size + len(q)*len(shapes) > 8_000_000:
            raise ValueError('Field projection exceeds bounded element budget')
        return q @ shapes.T

    def field_rms(self, modal_displacement, x, y):
        """RMS over exactly these contiguous, equally spaced sample frames.

        Includes cross-mode covariance; summing per-mode RMS loses
        interference. Empty support is invalid, never a silent zero field.
        Caller must retain sample-clock/window provenance.
        """
        field = self.field(modal_displacement, x, y)
        if not len(field):
            raise ValueError('RMS requires nonempty temporal support')
        return np.sqrt(np.mean(field**2, axis=0))

    def render(self, pcm):
        pcm = np.asarray(pcm, dtype=float)
        if pcm.ndim != 1 or not np.isfinite(pcm).all() or len(pcm) > self.settings.sample_rate*120:
            raise ValueError('Finite mono PCM, at most 120 seconds per call')
        if len(pcm)*(len(self.indices)+1) > 8_000_000:
            raise ValueError('Render exceeds bounded element budget; use smaller blocks')
        displacement = np.empty((len(pcm), len(self.indices)))
        energy = np.empty(len(pcm))
        for i, force in enumerate(pcm):
            self.state = np.einsum('nij,nj->ni', self.transition, self.state) + self.input_step*force
            displacement[i] = self.state[:, 0]
            energy[i] = .5*np.sum(self.state[:, 1]**2 + self.omega**2*self.state[:, 0]**2)
        self.sample_index += len(pcm)
        return {'modal_displacement': displacement, 'modal_energy_proxy': energy,
                'sample_index': self.sample_index}
