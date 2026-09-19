import pandas as pd
from scripts.phase14a_cross_section_screen import main

def test_cross_section_screen_smoke(tmp_path, monkeypatch):
    rows=[]
    dates=pd.date_range('2020-01-01',periods=120,freq='B')
    for d in dates:
        for i in range(50):
            px=100+i*0.01+len(rows)*0.001
            rows.append({'date':d,'symbol':f'S{i:02d}','active_nifty50':True,'close':px,'prev_close':px-0.01,'turnover_inr':1e8+i*1e6})
    inp=tmp_path/'x.csv'; out=tmp_path/'y.json'
    pd.DataFrame(rows).to_csv(inp,index=False)
    monkeypatch.setattr('sys.argv',['x','--input',str(inp),'--output',str(out)])
    main()
    assert out.exists()
    data=__import__('json').loads(out.read_text())
    assert data['phase']=='14A.1'
    assert 'XS_MOMENTUM' in data['results']