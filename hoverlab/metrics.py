"""Evaluator-only true-state metrics. None is intentionally retained."""
import numpy as np

def settling_time(time, error, tolerance, start=0.0, dwell=2.0):
    # First entry followed by at least dwell seconds AND no later departure.
    eligible = np.flatnonzero(time >= start-1e-9)
    if not len(eligible):
        return None
    bad = np.flatnonzero((np.abs(error)>tolerance) & (time >= start-1e-9))
    first = max(eligible[0], bad[-1]+1 if len(bad) else eligible[0])
    if first >= len(time) or time[-1]-time[first] < dwell-1e-9:
        return None
    return float(time[first]-start)

def evaluate(df, cfg):
    t, e = df.time.to_numpy(), df.error.to_numpy()
    amplitude = cfg.target-cfg.initial_z
    tolerance = max(0.02*abs(amplitude),0.02)
    step_end = cfg.force_start if cfg.force != 0 else t[-1]
    step = t < step_end if cfg.force != 0 else np.ones(len(t), dtype=bool)
    final = t >= t[-1]-5
    overshoot = None
    if abs(amplitude)>1e-12 and np.any(step):
        progress = (df.altitude.to_numpy()[step]-cfg.initial_z)/amplitude
        overshoot = float(max(0, progress.max()-1)*100)
    return dict(overshoot_pct=overshoot,
        settling_s=settling_time(t[step], e[step], tolerance) if amplitude else None,
        recovery_s=settling_time(t,e,tolerance,cfg.force_end) if cfg.force else None,
        final_mean_error_m=float(e[final].mean()), rms_error_m=float(np.sqrt(np.mean(e**2))),
        iae_m_s=float(np.trapezoid(np.abs(e),t)),
        saturation_pct=float(df.saturated.iloc[:-1].mean()*100),
        effort_n2_s=float(np.sum(df.applied.to_numpy()[:-1]**2)*cfg.dt))
