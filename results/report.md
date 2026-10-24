# HoverLab computed benchmark report

Mode: **full**. Python 3.14.3. 130 controller runs. All values below come from saved computations, using evaluator-only true altitude. These are simulations, not flight validation.

## Method and frozen configuration

Fixed engineering choice before evaluation; no automated search, zero tuning candidates. P and PID share Kp. Not a best-tuned-P versus best-tuned-PID claim. Gains: {'kp': 4.0, 'ki': 0.8, 'kd': 3.5, 'tau': 0.1}. Both controllers get only measured altitude, identical nominal mass, thrust limits, sample time and pre-generated noise arrays. Deterministic scenarios use seed 0; full stochastic cases use 20 paired seeds (0–19). Noise is independent Gaussian altitude noise in meters at each sample. No tuning against these evaluations occurred. The baseline uses the same Kp, not an independently optimized baseline.

Step overshoot uses signed initial-to-target amplitude and clips negative overshoot to zero. Step metrics stop before a disturbance starts. Zero-amplitude steps are N/A. Settling tolerance is max(2% of step amplitude, 0.02 m), with at least 2 s in-band and no subsequent departure within the evaluation window. Recovery is measured from force removal, using the same band. Unmet conditions remain missing, never zero. Final mean error is signed target−altitude over the last 5 s. RMS covers the full run; IAE is trapezoidal integration over time. Saturation is percent of applied intervals at either limit. Effort is sum(thrust² × dt), a force-squared proxy, **not energy or battery consumption**.

## Computed summary

SD is sample SD (zero for deterministic single runs). Settling/recovery means include reached runs only; missing counts expose unsuccessful or inapplicable runs. Recovery is N/A outside disturbance scenarios.

| scenario | controller | runs | iae_mean | iae_sd | rms_mean | overshoot_pct | settling_s | recovery_s | final_error_m | saturation_pct | effort_n2_s | settling_missing | recovery_missing |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nominal | P | 1 | 5.166 | 0.000 | 0.376 | 67.282 | 14.640 | not reached / N/A | 0.000 | 0.000 | 2974.564 | 0 | 1 |
| nominal | PID | 1 | 3.203 | 0.000 | 0.283 | 12.911 | 12.100 | not reached / N/A | -0.001 | 0.000 | 2918.956 | 0 | 1 |
| disturbance | P | 1 | 8.993 | 0.000 | 0.477 | 67.282 | not reached / N/A | 12.840 | -0.004 | 0.000 | 3133.117 | 1 | 0 |
| disturbance | PID | 1 | 5.221 | 0.000 | 0.317 | 12.911 | not reached / N/A | 10.460 | -0.011 | 0.000 | 3056.277 | 1 | 0 |
| heavy | P | 1 | 22.370 | 0.000 | 0.788 | 7.899 | not reached / N/A | not reached / N/A | 0.737 | 0.000 | 4930.293 | 1 | 1 |
| heavy | PID | 1 | 3.668 | 0.000 | 0.349 | 0.000 | 9.150 | not reached / N/A | 0.000 | 0.000 | 4910.854 | 0 | 1 |
| light | P | 1 | 16.731 | 0.000 | 0.639 | 104.400 | not reached / N/A | not reached / N/A | -0.490 | 0.000 | 1952.635 | 1 | 1 |
| light | PID | 1 | 4.849 | 0.000 | 0.317 | 28.774 | 14.630 | not reached / N/A | -0.001 | 0.000 | 1879.490 | 0 | 1 |
| noise_low | P | 20 | 5.180 | 0.031 | 0.376 | 67.300 | 15.092 | not reached / N/A | 0.000 | 0.000 | 2974.708 | 0 | 20 |
| noise_low | PID | 20 | 3.219 | 0.031 | 0.283 | 12.990 | 12.192 | not reached / N/A | -0.001 | 0.000 | 2935.287 | 0 | 20 |
| noise_high | P | 20 | 5.330 | 0.144 | 0.376 | 67.375 | 18.640 | not reached / N/A | -0.000 | 0.000 | 2979.292 | 5 | 20 |
| noise_high | PID | 20 | 3.376 | 0.145 | 0.285 | 13.784 | 19.557 | not reached / N/A | -0.002 | 0.380 | 3324.695 | 2 | 20 |
| noisy_disturbance | P | 20 | 8.984 | 0.075 | 0.476 | 67.328 | not reached / N/A | 13.162 | -0.004 | 0.000 | 3134.008 | 20 | 1 |
| noisy_disturbance | PID | 20 | 5.232 | 0.073 | 0.317 | 13.208 | not reached / N/A | 11.134 | -0.011 | 0.003 | 3158.413 | 20 | 0 |
| infeasible | P | 1 | 60.000 | 0.000 | 2.000 | 0.000 | not reached / N/A | not reached / N/A | 2.000 | 100.000 | 1920.000 | 1 | 1 |
| infeasible | PID | 1 | 60.000 | 0.000 | 2.000 | 0.000 | not reached / N/A | not reached / N/A | 2.000 | 100.000 | 1920.000 | 1 | 1 |

## Paired IAE differences (PID minus P)

Negative favors PID. Positive favors P. SD is across paired differences, not an uncertainty claim about real hardware.

| scenario | mean | std | min | max |
|---|---|---|---|---|
| disturbance | -3.772 | 0.000 | -3.772 | -3.772 |
| heavy | -18.702 | 0.000 | -18.702 | -18.702 |
| infeasible | 0.000 | 0.000 | 0.000 | 0.000 |
| light | -11.882 | 0.000 | -11.882 | -11.882 |
| noise_high | -1.954 | 0.223 | -2.303 | -1.512 |
| noise_low | -1.961 | 0.051 | -2.037 | -1.864 |
| noisy_disturbance | -3.753 | 0.100 | -3.973 | -3.539 |
| nominal | -1.963 | 0.000 | -1.963 | -1.963 |

## Numerical sensitivity

Predeclared criterion: Before execution: max absolute altitude difference <= 0.05 m and IAE difference <= 5% for deterministic feasible scenarios. Stress case is reported separately. Fine dt = 0.005 s, compared at common sample times; noise cases excluded because independent sample noise has no fixed continuous-time bandwidth.

| scenario | controller | max_height_difference_m | iae_relative_difference | passed |
|---|---|---|---|---|
| nominal | P | 0.010 | 0.002 | True |
| nominal | PID | 0.007 | 0.003 | True |
| disturbance | P | 0.010 | 0.001 | True |
| disturbance | PID | 0.007 | 0.002 | True |
| heavy | P | 0.005 | 0.000 | True |
| heavy | PID | 0.005 | 0.001 | True |
| light | P | 0.014 | 0.000 | True |
| light | PID | 0.009 | 0.002 | True |
| infeasible | P | 0.000 | 0.000 | True |
| infeasible | PID | 0.000 | 0.000 | True |

## Interpretation and limitations

The infeasible case cannot hover: 8 N < 9.81 N weight. Both controllers remain grounded, so PID offers no tracking benefit. In the high-noise scenario PID uses more mean thrust-squared effort than P; the computed summary also shows that settling can worsen despite lower full-run tracking error. Read effort alongside error: stronger correction can increase actuator demand. The P controller retains offsets under mass mismatch or sustained force; PID may remove offset but amplifies sensor noise through its derivative. Gains are an illustrative fixed choice, not globally optimal. Noise samples and seed count quantify only this modeled randomness. Ground impacts are perfectly inelastic, thrust changes instantly, and there is no motor lag, tilt, wind dynamics, sensor delay, battery model or real aircraft. No safety or hardware claims follow from these results.

## Plots

![Nominal](../docs/images/nominal.png)
![Disturbance](../docs/images/disturbance.png)
![Thrust](../docs/images/thrust.png)
![Paired comparison](../docs/images/comparison.png)
