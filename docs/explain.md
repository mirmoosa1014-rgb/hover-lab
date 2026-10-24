# Understanding HoverLab

Gravity pulls down with force m×9.81. Thrust pushes up. A disturbance is an extra signed force, and drag resists vertical velocity. Dividing the net force by mass gives acceleration. At steady hover with no disturbance or velocity, thrust must equal weight. If maximum thrust is smaller than weight, clever control cannot make the vehicle hover.

The simulation moves forward in small time steps. It updates velocity from acceleration, then height using the new velocity. This is semi-implicit Euler integration. It is an approximation: halving the step should change representative results only slightly. The saved sensitivity table compares full trajectories at shared times and IAE; the criterion (0.05 m and 5%) was written before running it. It is an engineering consistency check, not a proof of continuous-time accuracy.

P means proportional: a larger altitude error commands a larger correction. Gravity feedforward supplies nominal hover thrust before feedback adds its correction. If actual mass differs from the assumed mass, P often needs a persistent altitude error to produce the missing thrust.

I means integral: persistent error accumulates into an extra force contribution. D means derivative: measured upward movement reduces thrust so the controller can brake before reaching the target. The derivative uses changes in measured altitude, never hidden true velocity. Noise makes raw differences jumpy; the first-order filter smooths them. Higher smoothing also delays the feedback. Initial derivative is zero, and the first measurement seeds the previous-sample state.

Anti-windup matters when the motor is already at a limit. Adding more integral correction in the same direction cannot increase actual thrust, but it can delay later recovery. This implementation freezes an integral increment that would push the candidate command farther beyond the relevant limit. Integration in the opposite direction remains allowed. Commanded thrust may still exceed the limit; applied thrust never does.

The nominal plot shows how quickly and smoothly height approaches the target. Overshoot is the amount above the requested signed step, as a percentage of its amplitude. The disturbance plot marks the force window. Recovery time starts at force removal, not at the original ascent. The thrust chart distinguishes controller demand from available force and marks saturation. The paired comparison shows mean performance with seed-to-seed standard deviation; a single deterministic run has zero variability, not evidence of universal certainty.

IAE adds the magnitude of altitude error over time. RMS weights larger errors more strongly. Final mean error is signed, so a value near zero can hide oscillation; read it alongside RMS and the trace. Settling requires staying within max(2% of step size, 0.02 m) through the evaluation window with at least 2 seconds remaining. A late entry with less than 2 seconds left is not reached. A zero-size step makes step metrics inapplicable. Effort sums squared thrust over time; it is not battery energy.

The controller sees noisy altitude, but evaluation sees true simulated height. This separates sensor noise from real tracking error. The paired experiment uses exactly the same noise array for both algorithms, reducing avoidable comparison noise. Frozen gains and saved seeds keep evaluation reproducible; neither controller is claimed to be optimally tuned.

Start reading physics.py, then controllers.py, simulation.py and metrics.py. The benchmark combines those modules without importing the UI. The dashboard only runs short current simulations and reads the frozen summary; slider changes never silently rerun or replace the full benchmark.

This is one-dimensional software. A real drone tilts, has delayed motors and imperfect sensors, and can fail in many unmodeled ways. These results do not validate any aircraft.
