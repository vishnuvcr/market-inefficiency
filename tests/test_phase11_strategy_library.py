from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from phase11_strategy_library import (
    catalogue,
    atm_calendar,
    butterfly_put,
    call_butterfly,
    delta_hedge_units,
    four_leg_surface_box,
    iron_condor,
    long_skew_vertical,
    risk_reversal_put_call,
    skew_butterfly,
    strategy_exposure,
    straddle_strangle,
    terminal_payoff,
)


def test_catalogue_is_broad_and_complete():
    names = catalogue()
    assert len(names) >= 9
    for name in (
        "put_skew_vertical_long",
        "put_call_risk_reversal",
        "put_butterfly",
        "call_butterfly",
        "iron_condor",
        "atm_calendar",
        "skew_butterfly",
        "four_leg_surface_box",
        "straddle_strangle",
    ):
        assert name in names


def test_vertical_payoff_is_finite():
    s = long_skew_vertical(24000, 25000, 60, 0.25, 0.20)
    e = strategy_exposure(s, 25000, 0.06)
    assert all(k in e for k in ("price", "delta", "gamma", "vega", "theta"))
    assert all(abs(v) < 1e9 for v in e.values())
    assert terminal_payoff(s, 23000) == -1000


def test_risk_reversal_exposes_delta_and_hedge_quantity_is_defined():
    s = risk_reversal_put_call(24000, 26000, 60, 0.28, 0.20)
    e = strategy_exposure(s, 25000, 0.06)
    assert e["delta"] != 0
    assert delta_hedge_units(s, 25000, 0.06) == -e["delta"]


def test_iron_condor_is_four_legs():
    s = iron_condor(23500, 24000, 26000, 26500, 45, 0.30, 0.25, 0.24, 0.28)
    assert len(s.legs) == 4
    e = strategy_exposure(s, 25000, 0.06)
    assert e["gamma"] != 0


def test_all_structure_builders_have_explicit_legs():
    structures = [
        call_butterfly(25000, 25500, 26000, 45, 0.24, 0.20, 0.19),
        atm_calendar(25000, 30, 60, 0.22, 0.24),
        skew_butterfly(24000, 24500, 25000, 45, 0.30, 0.25, 0.21),
        four_leg_surface_box(24000, 25000, 24500, 25500, 30, 60, 0.30, 0.22, 0.29, 0.24),
        straddle_strangle(25000, 25000, 30, 0.22, 0.23),
        butterfly_put(24000, 24500, 25000, 45, 0.28, 0.25, 0.22),
    ]
    assert all(len(s.legs) >= 2 for s in structures)
