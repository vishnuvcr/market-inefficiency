from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from phase11_strategy_library import (
    catalogue,
    iron_condor,
    long_skew_vertical,
    strategy_exposure,
    terminal_payoff,
)


def test_catalogue_is_broad_and_non_empty():
    names = catalogue()
    assert len(names) >= 8
    assert "iron_condor" in names
    assert "put_skew_vertical_long" in names


def test_vertical_payoff_is_finite():
    s = long_skew_vertical(24000, 25000, 60, 0.25, 0.20)
    e = strategy_exposure(s, 25000, 0.06)
    assert all(k in e for k in ("price", "delta", "gamma", "vega", "theta"))
    assert all(abs(v) < 1e9 for v in e.values())
    assert terminal_payoff(s, 23000) >= 0


def test_iron_condor_is_four_legs():
    s = iron_condor(23500, 24000, 26000, 26500, 45, 0.30, 0.25, 0.24, 0.28)
    assert len(s.legs) == 4
    e = strategy_exposure(s, 25000, 0.06)
    assert e["gamma"] != 0
