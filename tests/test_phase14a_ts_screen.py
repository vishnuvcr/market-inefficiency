from pathlib import Path
import json
import pandas as pd
from scripts.phase14a_ts_screen import main as screen_main

def test_phase14a_screen_smoke(tmp_path, monkeypatch):
    df = pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=160, freq="B"),
        "open": 100.0,
        "high": 101.0,
        "low": 99.0,
        "close": [100.0 + i * 0.1 for i in range(160)],
    })
    inp = tmp_path / "nifty.csv"
    out = tmp_path / "result.json"
    df.to_csv(inp, index=False)

    monkeypatch.setattr(
        "sys.argv",
        ["phase14a_ts_screen.py", "--input", str(inp), "--output", str(out)],
    )
    screen_main()
    data = json.loads(out.read_text())
    assert data["phase"] == "14A.1"
    assert set(data["results"]) == {"TS_MOMENTUM", "TS_REVERSAL", "COMBO_TS"}
    assert Path(str(out.with_suffix(".events.csv"))).exists()
