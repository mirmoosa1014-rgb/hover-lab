# 60-second demonstration

- 0–10 s: Open the dashboard. Point out “SIMULATION ONLY,” the two controllers, and the default altitude response.
- 10–25 s: Compare RMS error and settling. Explain gravity feedforward and the derivative term's braking effect.
- 25–40 s: Choose Disturbance. Show the height error, recovery and commanded/applied thrust. Open the full metrics.
- 40–50 s: Choose Insufficient thrust. Explain why 8 N cannot lift a 1 kg mass against 9.81 N weight.
- 50–60 s: Show the optional animation and frozen benchmark. Mention paired seeds, tests, the AI-assisted implementation and the absence of real-flight validation.

## Reviewer questions

**Why does P have an offset with the wrong mass?** Its fixed gravity feedforward is wrong, so nonzero proportional error supplies the extra force needed at equilibrium.

**Does PID see the real velocity?** No. It estimates motion using filtered differences of measured altitude. True state is reserved for the evaluator.

**How is the comparison fair?** The plant, initial state, limits, time step, nominal mass, Kp and exact noise arrays are shared. Gains are frozen before evaluation. This is not a comparison of independently optimal controllers.

**What does anti-windup do here?** It rejects integral increments that would worsen command saturation. It allows correction in the opposite direction and does not remove the physical limit.

**Why should someone trust the numbers?** They can reproduce saved metrics from committed scenarios and seeds, inspect the equations and tests, and compare half-step results. That supports reproducibility of a simplified simulation, not real-world performance.
