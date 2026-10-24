import numpy as np
import pandas as pd
from .controllers import Controller, Gains
from .physics import advance

def paired_runs(cfg, gains=Gains(), seed=0):
    n = round(cfg.duration/cfg.dt)
    noise = np.random.default_rng(seed).normal(0, cfg.noise, n+1)
    return {kind: simulate(cfg, gains, kind, noise) for kind in ('P', 'PID')}

def simulate(cfg, gains, kind, noise):
    n = round(cfg.duration/cfg.dt)
    if len(noise) != n+1 or not np.isfinite(noise).all():
        raise ValueError('Noise must be a finite pre-generated sample per state.')
    controller = Controller(kind, gains, cfg)
    z, v = cfg.initial_z, cfg.initial_v
    rows = []
    for k in range(n+1):
        t = k*cfg.dt
        measured = z + noise[k]
        commanded, applied = controller.step(measured)
        force = cfg.force if cfg.force_start <= t < cfg.force_end else 0.0
        rows.append((t,z,v,measured,noise[k],cfg.target,cfg.target-z,commanded,applied,
                     float(applied <= 0 or applied >= cfg.max_thrust),force))
        if k < n:
            z,v = advance(z,v,applied,force,cfg)
    return pd.DataFrame(rows, columns=['time','altitude','velocity','measured','noise','target','error',
                                      'commanded','applied','saturated','force'])
