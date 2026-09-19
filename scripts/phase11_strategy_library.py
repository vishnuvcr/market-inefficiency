#!/usr/bin/env python3
"""Phase 11 — executable surface-relative-value strategy representation.

The module defines the preregistered candidate structures and deterministic
diagnostic exposures/payoffs. It does not backtest, rank, or select a winner.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from scipy.stats import norm


@dataclass(frozen=True)
class OptionLeg:
    side: int              # +1 long, -1 short
    option_type: str       # CE / PE
    strike: float
    expiry_days: float
    iv: float
    quantity: float = 1.0


@dataclass(frozen=True)
class Strategy:
    name: str
    legs: tuple[OptionLeg, ...]
    signal_exposure: str
    max_loss_formula: str


def _bs(forward: float, strike: float, t: float, iv: float, r: float, cp: str):
    if min(forward, strike, t, iv) <= 0:
        raise ValueError("forward, strike, t and iv must be positive")
    sqrt_t = math.sqrt(t)
    d1 = (math.log(forward / strike) + 0.5 * iv * iv * t) / (iv * sqrt_t)
    d2 = d1 - iv * sqrt_t
    disc = math.exp(-r * t)
    if cp == "CE":
        price = disc * (forward * norm.cdf(d1) - strike * norm.cdf(d2))
        delta = disc * norm.cdf(d1)
    elif cp == "PE":
        price = disc * (strike * norm.cdf(-d2) - forward * norm.cdf(-d1))
        delta = disc * (norm.cdf(d1) - 1.0)
    else:
        raise ValueError("option_type must be CE or PE")
    gamma = disc * norm.pdf(d1) / (forward * iv * sqrt_t)
    vega = disc * forward * norm.pdf(d1) * sqrt_t
    theta = -0.5 * disc * forward * norm.pdf(d1) * iv / sqrt_t
    return price, delta, gamma, vega, theta


def strategy_exposure(strategy: Strategy, forward: float, rate: float = 0.0) -> dict:
    totals = {"price": 0.0, "delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0}
    for leg in strategy.legs:
        t = leg.expiry_days / 365.0
        vals = _bs(forward, leg.strike, t, leg.iv, rate, leg.option_type)
        weight = leg.side * leg.quantity
        totals["price"] += weight * vals[0]
        totals["delta"] += weight * vals[1]
        totals["gamma"] += weight * vals[2]
        totals["vega"] += weight * vals[3]
        totals["theta"] += weight * vals[4]
    return totals


def terminal_payoff(strategy: Strategy, spot: float) -> float:
    payoff = 0.0
    for leg in strategy.legs:
        intrinsic = max(spot - leg.strike, 0.0) if leg.option_type == "CE" else max(leg.strike - spot, 0.0)
        payoff += leg.side * leg.quantity * intrinsic
    return payoff


def delta_hedge_units(strategy: Strategy, forward: float, rate: float = 0.0) -> float:
    """Underlying units required to neutralise the option delta."""
    return -strategy_exposure(strategy, forward, rate)["delta"]


def long_skew_vertical(k10: float, katm: float, expiry_days: float, iv10: float, ivatm: float) -> Strategy:
    return Strategy(
        name="put_skew_vertical_long",
        legs=(
            OptionLeg(+1, "PE", k10, expiry_days, iv10),
            OptionLeg(-1, "PE", katm, expiry_days, ivatm),
        ),
        signal_exposure="positive downside-skew exposure",
        max_loss_formula="limited by strike difference and entry premium",
    )


def risk_reversal_put_call(kput: float, kcall: float, expiry_days: float, ivput: float, ivcall: float) -> Strategy:
    return Strategy(
        name="put_call_risk_reversal",
        legs=(
            OptionLeg(+1, "PE", kput, expiry_days, ivput),
            OptionLeg(-1, "CE", kcall, expiry_days, ivcall),
        ),
        signal_exposure="downside-skew plus directional delta exposure",
        max_loss_formula="requires underlying delta hedge; unhedged tail risk is not bounded by the option spread alone",
    )


def butterfly_put(k1: float, k2: float, k3: float, expiry_days: float, iv1: float, iv2: float, iv3: float) -> Strategy:
    return Strategy(
        name="put_butterfly",
        legs=(
            OptionLeg(+1, "PE", k1, expiry_days, iv1),
            OptionLeg(-2, "PE", k2, expiry_days, iv2),
            OptionLeg(+1, "PE", k3, expiry_days, iv3),
        ),
        signal_exposure="localized downside-wing curvature/skew exposure",
        max_loss_formula="limited by wing separation and entry debit/credit",
    )


def call_butterfly(k1: float, k2: float, k3: float, expiry_days: float, iv1: float, iv2: float, iv3: float) -> Strategy:
    return Strategy(
        name="call_butterfly",
        legs=(
            OptionLeg(+1, "CE", k1, expiry_days, iv1),
            OptionLeg(-2, "CE", k2, expiry_days, iv2),
            OptionLeg(+1, "CE", k3, expiry_days, iv3),
        ),
        signal_exposure="localized upside-wing curvature/skew exposure",
        max_loss_formula="limited by wing separation and entry debit/credit",
    )


def iron_condor(
    kput_wing: float,
    kput_short: float,
    kcall_short: float,
    kcall_wing: float,
    expiry_days: float,
    iv_pw: float,
    iv_ps: float,
    iv_cs: float,
    iv_cw: float,
) -> Strategy:
    return Strategy(
        name="iron_condor",
        legs=(
            OptionLeg(+1, "PE", kput_wing, expiry_days, iv_pw),
            OptionLeg(-1, "PE", kput_short, expiry_days, iv_ps),
            OptionLeg(-1, "CE", kcall_short, expiry_days, iv_cs),
            OptionLeg(+1, "CE", kcall_wing, expiry_days, iv_cw),
        ),
        signal_exposure="combined skew, curvature and variance exposure; sign must be solved from frozen surface forecast",
        max_loss_formula="limited by wider wing minus net credit",
    )


def calendar_atm(
    strike: float,
    front_days: float,
    back_days: float,
    front_iv: float,
    back_iv: float,
    option_type: str = "CE",
    long_back: bool = True,
) -> Strategy:
    sign_back = 1 if long_back else -1
    sign_front = -sign_back
    return Strategy(
        name="atm_calendar",
        legs=(
            OptionLeg(sign_front, option_type, strike, front_days, front_iv),
            OptionLeg(sign_back, option_type, strike, back_days, back_iv),
        ),
        signal_exposure="30D–60D term-slope exposure at fixed strike",
        max_loss_formula="depends on net entry debit/credit; terminal payoff is maturity-path dependent",
    )


def skew_butterfly(
    k10: float,
    k25: float,
    k50: float,
    expiry_days: float,
    iv10: float,
    iv25: float,
    iv50: float,
) -> Strategy:
    return Strategy(
        name="skew_butterfly",
        legs=(
            OptionLeg(+1, "PE", k10, expiry_days, iv10),
            OptionLeg(-2, "PE", k25, expiry_days, iv25),
            OptionLeg(+1, "PE", k50, expiry_days, iv50),
        ),
        signal_exposure="downside-skew curvature across wing and near-ATM points",
        max_loss_formula="limited by strike geometry and net entry premium",
    )


def four_leg_surface_box(
    k10_front: float,
    katm_front: float,
    k10_back: float,
    katm_back: float,
    front_days: float,
    back_days: float,
    iv10_front: float,
    ivatm_front: float,
    iv10_back: float,
    ivatm_back: float,
) -> Strategy:
    return Strategy(
        name="four_leg_surface_box",
        legs=(
            OptionLeg(+1, "PE", k10_front, front_days, iv10_front),
            OptionLeg(-1, "PE", katm_front, front_days, ivatm_front),
            OptionLeg(-1, "PE", k10_back, back_days, iv10_back),
            OptionLeg(+1, "PE", katm_back, back_days, ivatm_back),
        ),
        signal_exposure="difference between near- and far-maturity downside skew",
        max_loss_formula="bounded by combined strike geometry if strikes are properly ordered",
    )


def straddle_strangle(
    k1: float,
    k2: float,
    expiry_days: float,
    iv_call: float,
    iv_put: float,
    long: bool = True,
) -> Strategy:
    side = 1 if long else -1
    return Strategy(
        name="straddle_strangle",
        legs=(
            OptionLeg(side, "CE", k1, expiry_days, iv_call),
            OptionLeg(side, "PE", k2, expiry_days, iv_put),
        ),
        signal_exposure="aggregate variance/ATM-versus-wing exposure",
        max_loss_formula="long structure loss is limited to premium; short structure has large tail loss",
    )


def catalogue() -> tuple[str, ...]:
    return (
        "put_skew_vertical_long",
        "put_call_risk_reversal",
        "put_butterfly",
        "call_butterfly",
        "iron_condor",
        "atm_calendar",
        "skew_butterfly",
        "four_leg_surface_box",
        "straddle_strangle",
    )
