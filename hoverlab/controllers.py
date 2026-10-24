"""Hand-written P / PID with measurement derivative and conditional integration."""
from dataclasses import dataclass, asdict
import math

@dataclass(frozen=True)
class Gains:
    kp: float = 4.0
    ki: float = 0.8
    kd: float = 3.5
    tau: float = 0.1
    def __post_init__(self):
        if not all(math.isfinite(x) and x >= 0 for x in asdict(self).values()) or self.tau <= 0:
            raise ValueError('Gains must be finite and nonnegative; tau must be positive.')

class Controller:
    def __init__(self, kind, gains, cfg):
        if kind not in ('P', 'PID'):
            raise ValueError('Unknown controller')
        self.kind, self.g, self.cfg = kind, gains, cfg
        self.integral = self.derivative = 0.0
        self.previous = None

    def step(self, measured):
        g, c = self.g, self.cfg
        error = c.target-measured
        raw_d = 0.0 if self.previous is None else (measured-self.previous)/c.dt
        alpha = g.tau/(g.tau+c.dt)
        self.derivative = alpha*self.derivative + (1-alpha)*raw_d
        self.previous = measured
        base = c.nominal_mass*9.81 + g.kp*error
        if self.kind == 'PID':
            base -= g.kd*self.derivative
            candidate = self.integral + g.ki*error*c.dt
            proposed = base + candidate
            # Freeze integration only if the increment drives farther into saturation.
            if not ((proposed > c.max_thrust and error > 0) or (proposed < 0 and error < 0)):
                self.integral = candidate
            base += self.integral
        return base, min(c.max_thrust, max(0.0, base))
