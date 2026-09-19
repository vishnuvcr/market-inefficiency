from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from phase13_cpcv_stats import (
    TradeEvent,
    approximate_dsr,
    cpcv,
    event_sharpe,
    pbo_from_paths,
)


def t(day):
    return datetime(2025, 1, 1, tzinfo=timezone.utc) + timedelta(days=day)


def make_events():
    out = []
    for i in range(48):
        for candidate, shift in (("A", 0.30), ("B", -0.05), ("C", 0.02)):
            out.append(
                TradeEvent(
                    candidate=candidate,
                    decision_time=t(i),
                    entry_time=t(i + 1),
                    exit_time=t(i + 2),
                    return_on_risk=(shift + (0.02 if i % 3 == 0 else -0.01)),
                )
            )
    return out


def test_event_sharpe_finite():
    assert event_sharpe([0.1, 0.2, 0.0]) > 0


def test_cpcv_produces_expected_path_count():
    events = make_events()
    paths = cpcv(events, n_groups=6, n_test_groups=2, purge_days=0, embargo_days=0)
    assert len(paths) == 15
    assert all(p.test_count > 0 for p in paths)


def test_pbo_and_dsr_are_finite_diagnostics():
    events = make_events()
    paths = cpcv(events, n_groups=6, n_test_groups=2, purge_days=0, embargo_days=0)
    pbo = pbo_from_paths(events, paths, n_groups=6, n_test_groups=2, purge_days=0, embargo_days=0)
    dsr = approximate_dsr([e.return_on_risk for e in events if e.candidate == "A"], n_trials=3)
    assert pbo is not None
    assert 0 <= pbo <= 1
    assert dsr is not None
