"""Offline Streamlit interface; benchmark work is deliberately outside UI reruns."""
from dataclasses import asdict
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from hoverlab.physics import Scenario
from hoverlab.controllers import Gains
from hoverlab.simulation import paired_runs
from hoverlab.metrics import evaluate
from hoverlab.visuals import animation

st.set_page_config(page_title='HoverLab | Altitude control',page_icon='↕',layout='wide')
st.markdown('<div style="position:fixed;top:0.7rem;left:50%;transform:translateX(-50%);z-index:999999;background:#123447;color:white;padding:0.3rem 0.8rem;border-radius:6px;font-size:0.75rem">SIMULATION ONLY · NO AIRCRAFT CONNECTION</div>', unsafe_allow_html=True)
st.title('HoverLab')
st.markdown('### One axis. Two controllers. Measurable tradeoffs.')
st.write('Explore how proportional and PID feedback control altitude in a simple vertical-motion model. Every curve is computed locally.')
PRESETS={'Calm ascent':{},'Disturbance':{'force':-3.0},'Mass mismatch':{'mass':1.3},'Noisy sensor':{'noise':0.1},'Insufficient thrust':{'max_thrust':8.0}}
def reset():
    for key in list(st.session_state):
        if key!='preset': del st.session_state[key]

def preset_changed(): reset()
with st.sidebar:
    st.header('Experiment controls')
    choice=st.selectbox('Preset',list(PRESETS),key='preset',on_change=preset_changed)
    defaults=Scenario(**PRESETS[choice])
    with st.form('controls'):
        st.subheader('Plant & sensor')
        mass=st.slider('Actual mass (kg)',0.5,2.0,defaults.mass,0.1,key='mass',help='Physical plant mass; the controller does not observe this.')
        nominal=st.slider('Assumed mass (kg)',0.5,2.0,1.0,0.1,key='nominal',help='Both controllers use this for gravity feedforward.')
        drag=st.slider('Linear drag (N·s/m)',0.0,3.0,defaults.drag,0.1,key='drag')
        noise=st.slider('Sensor noise SD (m)',0.0,0.2,defaults.noise,0.01,key='noise')
        thrust=st.slider('Maximum thrust (N)',1.0,35.0,defaults.max_thrust,0.5,key='thrust')
        target=st.slider('Target altitude (m)',0.0,5.0,2.0,0.1,key='target')
        st.subheader('Shared gains / PID terms')
        kp=st.slider('Kp (N/m)',0.0,12.0,4.0,0.1,key='kp')
        ki=st.slider('Ki (N/(m·s))',0.0,4.0,0.8,0.1,key='ki')
        kd=st.slider('Kd (N·s/m)',0.0,10.0,3.5,0.1,key='kd')
        tau=st.slider('Derivative filter τ (s)',0.02,0.5,0.1,0.01,key='tau',help='Larger values smooth the measurement derivative more strongly.')
        st.subheader('External vertical force')
        force=st.slider('Force (N)',-8.0,8.0,defaults.force,0.5,key='force',help='Positive is upward; neither controller observes the disturbance.')
        window=st.slider('Force window (s)',0.0,30.0,(10.0,12.0),0.5,key='window')
        seed=st.number_input('Noise seed',min_value=0,max_value=99999,value=0,key='seed')
        run=st.form_submit_button('Run simulation',type='primary',use_container_width=True)
    st.button('Reset controls',on_click=reset,use_container_width=True)
    st.caption('30 s simulation · 0.01 s time step. Form edits apply when Run is pressed. Presets and Reset load a fresh demo.')

if run or 'runs' not in st.session_state:
    try:
        cfg=Scenario(mass=mass,nominal_mass=nominal,drag=drag,noise=noise,max_thrust=thrust,target=target,force=force,force_start=window[0],force_end=window[1])
        gains=Gains(kp,ki,kd,tau)
        st.session_state.runs=paired_runs(cfg,gains,int(seed))
        st.session_state.config=cfg; st.session_state.gains=gains; st.session_state.run_seed=int(seed)
    except ValueError as exc:
        st.error(str(exc)); st.stop()
cfg=st.session_state.config; runs=st.session_state.runs
st.caption(f'CURRENT RUN · {cfg.mass:g} kg actual / {cfg.nominal_mass:g} kg assumed · target {cfg.target:g} m · seed {st.session_state.run_seed}')
if not cfg.feasible: st.error(f'Hover is physically infeasible: {cfg.max_thrust:.2f} N maximum thrust is below {cfg.mass*9.81:.2f} N weight.')
elif cfg.force and not cfg.disturbance_feasible: st.warning('Hover is infeasible during the force pulse at these actuator limits.')
metrics={kind:evaluate(df,cfg) for kind,df in runs.items()}
for col,(kind,m) in zip(st.columns(2),metrics.items()):
    with col:
        st.subheader('P controller' if kind=='P' else 'PID controller')
        a,b=st.columns(2); a.metric('RMS error',f'{m["rms_error_m"]:.3f} m'); b.metric('Integral absolute error',f'{m["iae_m_s"]:.3f} m·s')
        st.caption('Settling: '+(f'{m["settling_s"]:.2f} s' if m['settling_s'] is not None else ('not applicable' if cfg.target==cfg.initial_z else 'not reached')))
        if m['settling_s'] is None and cfg.target!=cfg.initial_z and cfg.feasible:
            st.warning(f'{kind} did not settle in the evaluation window. This may indicate persistent oscillation or tracking offset.')
st.info('P reacts to present error. PID adds accumulated error correction and filtered motion feedback; sensor noise can increase thrust variation. Lower tracking error can cost more actuator effort.')
colors={'P':'#bd6900','PID':'#007f92'}
def chart(field,title,ylabel,command=False):
    fig=go.Figure()
    for kind,df in runs.items():
        fig.add_trace(go.Scatter(x=df.time,y=df[field],name=kind,mode='lines',line=dict(color=colors[kind])))
        if command: fig.add_trace(go.Scatter(x=df.time,y=df.commanded,name=f'{kind} commanded',line=dict(color=colors[kind],dash='dot')))
    if field=='altitude': fig.add_trace(go.Scatter(x=df.time,y=df.target,name='Target',line=dict(color='#666666',dash='dash')))
    if field=='saturated': fig.update_yaxes(range=[-0.05,1.05])
    fig.update_layout(title=title,xaxis_title='Time (s)',yaxis_title=ylabel,height=330,margin=dict(l=20,r=20,t=55,b=30),legend=dict(orientation='h'))
    st.plotly_chart(fig,use_container_width=True)
left,right=st.columns(2)
with left: chart('altitude','Altitude response','Altitude (m)'); chart('applied','Commanded vs applied thrust','Thrust (N)',True)
with right: chart('error','Tracking error · evaluator ground truth','Target − altitude (m)'); chart('saturated','Actuator saturation','At limit (0 or 1)')
with st.expander('All metrics & definitions'):
    st.dataframe(pd.DataFrame(metrics).T, use_container_width=True)
    st.caption('Missing means not reached or not applicable. Final signed error: last 5 s. RMS and IAE: entire run. Step metrics end before the disturbance; recovery starts at force removal. Settling: max(2% step, 0.02 m), at least 2 s with no later departure. Effort is ∫ thrust² dt, not energy. Evaluator uses true altitude; controllers do not.')
if st.checkbox('Show bounded simulation animation (90 frames)'):
    st.image(animation(runs),caption='30 seconds compressed into an approximately 8-second loop. Each frame comes from this run.')
config=dict(scenario=asdict(cfg),gains=asdict(st.session_state.gains),seed=st.session_state.run_seed)
combined=pd.concat([d.assign(controller=k) for k,d in runs.items()],ignore_index=True)
a,b=st.columns(2)
a.download_button('Download current data (CSV)',combined.to_csv(index=False),'hoverlab-current.csv','text/csv')
b.download_button('Download current configuration',json.dumps(config,indent=2),'hoverlab-current.json','application/json')
with st.expander('Frozen benchmark · independent of current controls'):
    path=Path(__file__).parent/'results/summary.csv'
    if path.exists(): st.dataframe(pd.read_csv(path),use_container_width=True)
    st.caption('Fixed gains and 20 paired seeds for each noisy scenario. Regenerate using python -m hoverlab.benchmark. Current control changes do not alter this report.')
st.caption('AI-assisted educational model. No motor lag, tilt, battery, sensor delay or real-world validation. Not deployable flight-control software.')
