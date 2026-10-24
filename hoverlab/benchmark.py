"""Run with python -m hoverlab.benchmark [--smoke] [--output PATH]."""
import argparse
from dataclasses import asdict, replace
from pathlib import Path
import json, platform, importlib.metadata
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .physics import Scenario
from .controllers import Gains
from .simulation import paired_runs
from .metrics import evaluate
from .visuals import animation

COLORS={'P':'#bb6500','PID':'#007c91'}

def charts(traces, metrics, images):
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    for scenario,filename in [('nominal','nominal.png'),('disturbance','disturbance.png')]:
        if scenario not in traces: continue
        fig,ax=plt.subplots(figsize=(9,4.5),layout='constrained')
        for kind,df in traces[scenario].items():
            ax.plot(df.time,df.altitude,label=kind,color=COLORS[kind])
        ax.plot(df.time,df.target,'--',color='#555555',label='Target')
        if scenario=='disturbance': ax.axvspan(10,12,color='gray',alpha=.15,label='−3 N force')
        ax.set(xlabel='Time (s)',ylabel='True altitude (m)',title=f'{scenario.title()} · simulation, seed 0')
        ax.legend(ncol=4); ax.grid(alpha=.2); fig.savefig(images/filename,dpi=150); plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(9,6),sharex=True,layout='constrained')
    for kind,df in traces['infeasible'].items():
        axes[0].plot(df.time,df.commanded,'--',color=COLORS[kind],alpha=.6,label=f'{kind} commanded')
        axes[0].plot(df.time,df.applied,color=COLORS[kind],label=f'{kind} applied')
        axes[1].step(df.time,df.saturated,where='post',color=COLORS[kind],label=kind)
    axes[0].set(ylabel='Thrust (N)',title='Infeasible thrust: demanded force exceeds available force'); axes[0].legend(ncol=2)
    axes[1].set(xlabel='Time (s)',ylabel='Saturated (0/1)',ylim=(-.1,1.1)); axes[1].legend()
    fig.savefig(images/'thrust.png',dpi=150); plt.close(fig)
    names=list(metrics.scenario.unique()); fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    for ax,metric,label in zip(axes,['iae_m_s','effort_n2_s'],['Integral absolute error (m·s)','Thrust-squared integral (N²·s)']):
        for kind,offset in [('P',-.12),('PID',.12)]:
            means=[]; deviations=[]
            for name in names:
                values=metrics.loc[(metrics.scenario==name)&(metrics.controller==kind),metric]
                means.append(values.mean()); deviations.append(values.std(ddof=0))
            ax.errorbar(np.arange(len(names))+offset,means,yerr=deviations,fmt='o',capsize=4,label=kind,color=COLORS[kind])
        ax.set(xticks=np.arange(len(names)),xticklabels=names,ylabel=label)
        ax.tick_params(axis='x',rotation=40); ax.legend(); ax.grid(axis='y',alpha=.2)
    fig.suptitle('Paired benchmark · mean ± population SD across seeds'); fig.savefig(images/'comparison.png',dpi=150); plt.close(fig)

def table(frame):
    def fmt(v):
        if pd.isna(v): return 'not reached / N/A'
        return f'{v:.3f}' if isinstance(v,(float,np.floating)) else str(v)
    return '| '+' | '.join(frame.columns)+' |\n|'+'|'.join(['---']*len(frame.columns))+'|\n'+'\n'.join('| '+' | '.join(fmt(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None))

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--smoke',action='store_true'); parser.add_argument('--output',type=Path)
    args=parser.parse_args(); root=Path(__file__).resolve().parents[1]
    out=args.output or (root/'work/smoke' if args.smoke else root/'results')
    images=out/'images' if args.output or args.smoke else root/'docs/images'
    out.mkdir(parents=True,exist_ok=True); images.mkdir(parents=True,exist_ok=True)
    spec=json.loads((root/'configs/benchmark.json').read_text()); gains=Gains(**spec['gains'])
    rows=[]; traces={}; configs={}
    for name,overrides in spec['scenarios'].items():
        cfg=Scenario(**overrides); configs[name]=asdict(cfg)
        seeds=spec['seeds'][:2] if args.smoke else (spec['seeds'] if cfg.noise else [0])
        for seed in seeds:
            runs=paired_runs(cfg,gains,seed)
            for kind,df in runs.items():
                rows.append(dict(scenario=name,seed=seed,controller=kind,**evaluate(df,cfg)))
                if seed==0:
                    df.to_csv(out/f'{name}_{kind}.csv',index=False,float_format='%.8g')
            if seed==0: traces[name]=runs
    metrics=pd.DataFrame(rows); metrics.to_csv(out/'metrics.csv',index=False)
    sensitivity=[]
    for name,overrides in spec['scenarios'].items():
        cfg=Scenario(**overrides)
        if cfg.noise: continue
        fine=paired_runs(replace(cfg,dt=cfg.dt/2),gains)
        for kind,df in traces[name].items():
            delta=float(np.max(np.abs(df.altitude.to_numpy()-fine[kind].altitude.to_numpy()[::2])))
            coarse_iae=evaluate(df,cfg)['iae_m_s']; fine_iae=evaluate(fine[kind],replace(cfg,dt=cfg.dt/2))['iae_m_s']
            relative=abs(coarse_iae-fine_iae)/max(abs(fine_iae),1e-12)
            sensitivity.append(dict(scenario=name,controller=kind,max_height_difference_m=delta,iae_relative_difference=relative,passed=delta<=.05 and relative<=.05))
    sensitivity=pd.DataFrame(sensitivity); sensitivity.to_csv(out/'sensitivity.csv',index=False)
    metadata=dict(python=platform.python_version(),platform=platform.platform(),mode='smoke' if args.smoke else 'full',
                  packages={p:importlib.metadata.version(p) for p in ['numpy','pandas','streamlit','plotly','matplotlib','pillow','pytest']})
    (out/'environment.json').write_text(json.dumps(metadata,indent=2)+'\n')
    (out/'configuration.json').write_text(json.dumps(dict(**spec,resolved_scenarios=configs),indent=2)+'\n')
    charts(traces,metrics,images); (images/'simulation.gif').write_bytes(animation(traces['nominal']))
    summary=metrics.groupby(['scenario','controller'],sort=False).agg(runs=('seed','count'),iae_mean=('iae_m_s','mean'),iae_sd=('iae_m_s','std'),rms_mean=('rms_error_m','mean'),overshoot_pct=('overshoot_pct','mean'),settling_s=('settling_s','mean'),recovery_s=('recovery_s','mean'),final_error_m=('final_mean_error_m','mean'),saturation_pct=('saturation_pct','mean'),effort_n2_s=('effort_n2_s','mean')).reset_index()
    summary['iae_sd']=summary.iae_sd.fillna(0)
    # Missing counts keep partial settling/recovery failures visible beside means.
    summary['settling_missing']=metrics.groupby(['scenario','controller'],sort=False).settling_s.apply(lambda x:x.isna().sum()).to_numpy()
    summary['recovery_missing']=metrics.groupby(['scenario','controller'],sort=False).recovery_s.apply(lambda x:x.isna().sum()).to_numpy()
    summary.to_csv(out/'summary.csv',index=False)
    paired=metrics.pivot(index=['scenario','seed'],columns='controller',values='iae_m_s')
    paired['PID_minus_P']=paired.PID-paired.P
    paired_summary=paired.groupby('scenario').PID_minus_P.agg(['mean','std','min','max']).fillna(0).reset_index()
    paired_summary.to_csv(out/'paired_differences.csv',index=False)
    image_prefix='images' if args.output or args.smoke else '../docs/images'
    report=f'''# HoverLab computed benchmark report

Mode: **{metadata['mode']}**. Python {metadata['python']}. {len(metrics)} controller runs. All values below come from saved computations, using evaluator-only true altitude. These are simulations, not flight validation.

## Method and frozen configuration

{spec['selection']} Gains: {spec['gains']}. Both controllers get only measured altitude, identical nominal mass, thrust limits, sample time and pre-generated noise arrays. Deterministic scenarios use seed 0; full stochastic cases use 20 paired seeds (0–19). Noise is independent Gaussian altitude noise in meters at each sample. No tuning against these evaluations occurred. The baseline uses the same Kp, not an independently optimized baseline.

Step overshoot uses signed initial-to-target amplitude and clips negative overshoot to zero. Step metrics stop before a disturbance starts. Zero-amplitude steps are N/A. Settling tolerance is max(2% of step amplitude, 0.02 m), with at least 2 s in-band and no subsequent departure within the evaluation window. Recovery is measured from force removal, using the same band. Unmet conditions remain missing, never zero. Final mean error is signed target−altitude over the last 5 s. RMS covers the full run; IAE is trapezoidal integration over time. Saturation is percent of applied intervals at either limit. Effort is sum(thrust² × dt), a force-squared proxy, **not energy or battery consumption**.

## Computed summary

SD is sample SD (zero for deterministic single runs). Settling/recovery means include reached runs only; missing counts expose unsuccessful or inapplicable runs. Recovery is N/A outside disturbance scenarios.

{table(summary)}

## Paired IAE differences (PID minus P)

Negative favors PID. Positive favors P. SD is across paired differences, not an uncertainty claim about real hardware.

{table(paired_summary)}

## Numerical sensitivity

Predeclared criterion: {spec['sensitivity_tolerance']} Fine dt = 0.005 s, compared at common sample times; noise cases excluded because independent sample noise has no fixed continuous-time bandwidth.

{table(sensitivity)}

## Interpretation and limitations

The infeasible case cannot hover: 8 N < 9.81 N weight. Both controllers remain grounded, so PID offers no tracking benefit. In the high-noise scenario PID uses more mean thrust-squared effort than P; the computed summary also shows that settling can worsen despite lower full-run tracking error. Read effort alongside error: stronger correction can increase actuator demand. The P controller retains offsets under mass mismatch or sustained force; PID may remove offset but amplifies sensor noise through its derivative. Gains are an illustrative fixed choice, not globally optimal. Noise samples and seed count quantify only this modeled randomness. Ground impacts are perfectly inelastic, thrust changes instantly, and there is no motor lag, tilt, wind dynamics, sensor delay, battery model or real aircraft. No safety or hardware claims follow from these results.

## Plots

![Nominal]({image_prefix}/nominal.png)
![Disturbance]({image_prefix}/disturbance.png)
![Thrust]({image_prefix}/thrust.png)
![Paired comparison]({image_prefix}/comparison.png)
'''
    (out/'report.md').write_text(report)
    # Refresh only the explicitly generated README section.
    readme=root/'README.md'
    if not args.smoke and not args.output and readme.exists():
        text=readme.read_text(); start='<!-- RESULTS_START -->'; end='<!-- RESULTS_END -->'
        if start in text:
            selected=summary[summary.scenario.isin(['nominal','infeasible'])][['scenario','controller','iae_mean','rms_mean','settling_s']]
            text=text.split(start)[0]+start+'\n\n'+table(selected)+'\n\n'+end+text.split(end)[1]
            readme.write_text(text)
    print(table(summary[['scenario','controller','iae_mean','rms_mean','settling_s','effort_n2_s']]))
    print(f'Sensitivity: {sensitivity.passed.sum()}/{len(sensitivity)} passed. Outputs: {out}')
    if not sensitivity.passed.all(): raise SystemExit('Numerical sensitivity criterion failed; investigate.')

if __name__=='__main__': main()
