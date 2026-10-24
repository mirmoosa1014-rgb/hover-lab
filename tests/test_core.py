from dataclasses import replace
import numpy as np
import pandas as pd
import pytest
from hoverlab.physics import Scenario, acceleration, advance
from hoverlab.controllers import Controller, Gains
from hoverlab.simulation import paired_runs
from hoverlab.metrics import evaluate, settling_time

def test_hover_force_balance():
    c=Scenario()
    assert acceleration(2,0,9.81,0,c)==0
    assert advance(2,0,9.81,0,c)==(2,0)
    assert acceleration(2,2,9.81,0,c)==-1

def test_limits_and_feasibility():
    c=Scenario(max_thrust=8)
    assert not c.feasible
    assert Scenario(max_thrust=9.81).feasible
    for kind,df in paired_runs(c).items():
        assert df.applied.between(0,8).all()
        assert (df.altitude==0).all()

def test_antiwindup_and_release():
    c=Controller('PID',Gains(),Scenario(max_thrust=8))
    for _ in range(10000): c.step(0)
    assert c.integral==0
    c.cfg=Scenario()
    c.step(0)
    assert c.integral>0

def test_derivative_initialization_filter_and_setpoint():
    c=Controller('PID',Gains(),Scenario())
    c.step(5)
    assert c.derivative==0
    c.step(5.1)
    assert c.derivative==pytest.approx((1-.1/.11)*10)
    c=Controller('PID',Gains(),Scenario())
    c.step(0); c.cfg=replace(c.cfg,target=3); c.step(0)
    assert c.derivative==0

def test_ground():
    assert advance(.001,-5,0,0,Scenario())==(0,0)
    assert advance(0,0,20,0,Scenario())[0]>0

def test_determinism_fairness():
    cfg=Scenario(noise=.1)
    a=paired_runs(cfg,seed=17); b=paired_runs(cfg,seed=17)
    for k in a: pd.testing.assert_frame_equal(a[k],b[k])
    np.testing.assert_array_equal(a['P'].noise,a['PID'].noise)
    assert not np.array_equal(a['P'].noise,paired_runs(cfg,seed=18)['P'].noise)

def test_settling_examples():
    t=np.arange(0,5.01,.01)
    assert settling_time(t,np.zeros(len(t)),.02)==0
    assert settling_time(t,np.ones(len(t)),.02) is None
    e=np.where(t<2,1,0)
    assert settling_time(t,e,.02)==pytest.approx(2)
    e[-1]=1
    assert settling_time(t,e,.02) is None
    assert settling_time(t,np.zeros(len(t)),.02,start=2)==0

def test_known_metrics_zero_step():
    cfg=Scenario(target=0)
    m=evaluate(paired_runs(cfg)['PID'],cfg)
    assert m['overshoot_pct'] is None and m['settling_s'] is None
    assert m['rms_error_m']==0 and m['iae_m_s']==0
    cfg=Scenario(max_thrust=8)
    m=evaluate(paired_runs(cfg)['PID'],cfg)
    assert m['iae_m_s']==pytest.approx(60)
    assert m['rms_error_m']==2 and m['saturation_pct']==100
    assert m['effort_n2_s']==pytest.approx(8**2*30)

@pytest.mark.parametrize('changes',[{'mass':0},{'noise':-1},{'dt':0},{'drag':-1},{'target':float('nan')},{'force_end':40},{'initial_z':-1},{'nominal_mass':-1},{'max_thrust':0},{'duration':1000},{'dt':.00001}])
def test_invalid(changes):
    with pytest.raises(ValueError): Scenario(**changes)

@pytest.mark.parametrize('changes',[{'kp':-1},{'tau':0},{'ki':float('inf')}])
def test_bad_gains(changes):
    with pytest.raises(ValueError): Gains(**changes)


def test_disturbance_from_start_has_no_step_window():
    cfg=Scenario(force=-2,force_start=0)
    m=evaluate(paired_runs(cfg)['PID'],cfg)
    assert m['overshoot_pct'] is None and m['settling_s'] is None
    assert m['recovery_s'] is not None
