"""SI-unit plant; semi-implicit Euler and inelastic ground contact."""
from dataclasses import dataclass, asdict
import math

@dataclass(frozen=True)
class Scenario:
    mass: float = 1.0
    nominal_mass: float = 1.0
    drag: float = 0.5
    max_thrust: float = 25.0
    target: float = 2.0
    initial_z: float = 0.0
    initial_v: float = 0.0
    noise: float = 0.0
    force: float = 0.0
    force_start: float = 10.0
    force_end: float = 12.0
    dt: float = 0.01
    duration: float = 30.0

    def __post_init__(self):
        if not all(math.isfinite(x) for x in asdict(self).values()):
            raise ValueError('All parameters must be finite.')
        if self.mass <= 0 or self.nominal_mass <= 0 or self.max_thrust <= 0:
            raise ValueError('Masses and maximum thrust must be positive.')
        if min(self.drag, self.target, self.initial_z, self.noise) < 0:
            raise ValueError('Drag, heights and noise must be nonnegative.')
        if not 0 < self.dt <= 0.1 or not 2 <= self.duration <= 120:
            raise ValueError('Require 0 < dt ≤ 0.1 s and 2 ≤ duration ≤ 120 s.')
        if self.duration / self.dt > 100000:
            raise ValueError('Simulation exceeds 100,000 time steps.')
        if not 0 <= self.force_start <= self.force_end <= self.duration:
            raise ValueError('Disturbance times must lie within the simulation.')

    @property
    def feasible(self):
        return self.max_thrust >= self.mass * 9.81

    @property
    def disturbance_feasible(self):
        return 0 <= self.mass * 9.81 - self.force <= self.max_thrust

def acceleration(z, v, thrust, force, cfg):
    return (min(cfg.max_thrust, max(0, thrust)) + force - cfg.mass*9.81 - cfg.drag*v)/cfg.mass

def advance(z, v, thrust, force, cfg):
    v += acceleration(z, v, thrust, force, cfg)*cfg.dt
    z += v*cfg.dt
    if z <= 0:
        return 0.0, max(0.0, v)
    return z, v
