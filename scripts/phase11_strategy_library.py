#!/usr/bin/env python3
"""Phase 11 — surface-relative-value strategy representation.

This module contains structure definitions and deterministic exposure/payoff
calculations only. It does not backtest or select a strategy.
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
        max_loss_formula="unbounded in one direction before hedge; requires hedge model",
    )


def butterfly_put(k1: float, k2: float, k3: float, expiry_days: float, iv1: float, iv2: float, iv3: float) -> Strategy:
    return Strategy(
        name="put_butterfly",
        legs=(
            OptionLeg(+1, "PE", k1, expiry_days, iv1),
            OptionLeg(-2, "PE", k2, expiry_days, iv2),
            OptionLeg(+1, "PE", k3, expiry_days, iv3),
        ),
        signal_exposure="localized curvature/skew exposure",
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
        signal_exposure="combined skew, term and variance exposure; sign must be solved from frozen surface forecast",
        max_loss_formula="limited by wider wing minus net credit",
    )


def catalogue() -> tuple[str, ...]:
    return (
        "put_skew_vertical_long",
        "put_call_risk_reversal",
        "put_butterfly",
        "iron_condor",
        "calendar",
        "skew_butterfly",
        "four_leg_surface_box",
        "straddle_strangle",
    )
