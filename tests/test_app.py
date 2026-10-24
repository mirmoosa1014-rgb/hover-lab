from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_dashboard_presets_and_run():
    at=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=30).run()
    assert not at.exception
    assert len(at.metric)==4
    at.selectbox[0].select('Insufficient thrust').run()
    assert not at.exception
    assert any('infeasible' in e.value for e in at.error)
    at.selectbox[0].select('Calm ascent').run()
    assert not at.error
    next(s for s in at.slider if s.label=='Target altitude (m)').set_value(3.0)
    next(b for b in at.button if b.label=='Run simulation').click().run()
    assert at.session_state['config'].target==3.0
    next(b for b in at.button if b.label=='Reset controls').click().run()
    assert at.session_state['config'].target==2.0
    assert not at.exception
