import pandas as pd
from scripts.phase14a_acquire_pit_nifty50 import actual_symbol, members_on

def test_reverse_rename():
    renames = [{"old": "MINDTREE", "new": "LTM", "effective_date": "2022-11-14"}]
    assert actual_symbol("LTM", pd.Timestamp("2022-01-03"), renames) == "MINDTREE"
    assert actual_symbol("LTM", pd.Timestamp("2023-01-03"), renames) == "LTM"

def test_membership_half_open_interval():
    m = pd.DataFrame({
        "index_name": ["Nifty 50"],
        "symbol": ["LTM"],
        "valid_from": pd.to_datetime(["2022-01-01"]),
        "valid_to": pd.to_datetime(["2023-01-01"]),
    })
    renames = [{"old": "MINDTREE", "new": "LTM", "effective_date": "2022-11-14"}]
    assert members_on(m, pd.Timestamp("2022-10-01"), renames) == {"MINDTREE": "LTM"}
    assert members_on(m, pd.Timestamp("2023-01-01"), renames) == {}