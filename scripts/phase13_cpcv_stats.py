#!/usr/bin/env python3
"""Phase 13 — generic CPCV / PBO / approximate DSR engine.

This module operates on already-reconstructed executable trade events. It does
not create fills, infer prices, or choose a strategy from the 2026 rejected
forward sample. It uses event-time Sharpe (not annualized) unless the input
events themselves are fixed-frequency observations.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from itertools import combinations
import math
from statistics import NormalDist


@dataclass(frozen=True)
class TradeEvent:
    candidate: str
    decision_time: datetime
    entry_time: datetime
    exit_time: datetime
    return_on_risk: float


@dataclass(frozen=True)
class CPCVPath:
    path_id: int
    test_groups: tuple[int, ...]
    train_count: int
    test_count: int
    selected_candidate: str | None
    selected_train_sharpe: float | None
    selected_test_sharpe: float | None


def parse_time(value: str) -> datetime:
    ts = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def event_sharpe(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    var = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    if var <= 0 or not math.isfinite(var):
        return None
    return mean / math.sqrt(var)


def _group_assignments(events: list[TradeEvent], n_groups: int) -> list[int]:
    """Assign all events sharing a decision date to the same contiguous group."""
    unique_dates = sorted({e.decision_time.date() for e in events})
    if n_groups < 2 or len(unique_dates) < n_groups:
        raise ValueError("not enough unique decision dates for requested groups")
    date_group = {
        d: min(n_groups - 1, i * n_groups // len(unique_dates))
        for i, d in enumerate(unique_dates)
    }
    return [date_group[e.decision_time.date()] for e in events]


def purged_train_indices(
    events: list[TradeEvent],
    test_indices: set[int],
    purge_days: int,
    embargo_days: int,
) -> list[int]:
    if purge_days < 0 or embargo_days < 0:
        raise ValueError("purge/embargo must be non-negative")
    test_windows = [(events[i].entry_time, events[i].exit_time) for i in test_indices]
    kept = []
    purge = timedelta(days=purge_days)
    embargo = timedelta(days=embargo_days)

    for i, event in enumerate(events):
        if i in test_indices:
            continue
        eligible = True
        for test_entry, test_exit in test_windows:
            before = event.exit_time < test_entry - purge
            after = event.entry_time > test_exit + embargo
            if not (before or after):
                eligible = False
                break
        if eligible:
            kept.append(i)
    return kept


def cpcv(
    events: list[TradeEvent],
    n_groups: int = 8,
    n_test_groups: int = 2,
    purge_days: int = 30,
    embargo_days: int = 5,
) -> list[CPCVPath]:
    if n_test_groups <= 0 or n_test_groups >= n_groups:
        raise ValueError("n_test_groups must be between 1 and n_groups-1")

    events = sorted(events, key=lambda x: (x.decision_time, x.entry_time, x.candidate))
    groups = _group_assignments(events, n_groups)
    paths = []

    for path_id, test_groups in enumerate(combinations(range(n_groups), n_test_groups)):
        test_idx = {i for i, g in enumerate(groups) if g in test_groups}
        train_idx = purged_train_indices(events, test_idx, purge_days, embargo_days)

        candidates = sorted({e.candidate for e in events})
        train_sharpes = {}
        test_sharpes = {}
        for candidate in candidates:
            train_vals = [events[i].return_on_risk for i in train_idx if events[i].candidate == candidate]
            test_vals = [events[i].return_on_risk for i in test_idx if events[i].candidate == candidate]
            train_sharpes[candidate] = event_sharpe(train_vals)
            test_sharpes[candidate] = event_sharpe(test_vals)

        valid = {k: v for k, v in train_sharpes.items() if v is not None}
        selected = max(valid, key=valid.get) if valid else None
        paths.append(
            CPCVPath(
                path_id=path_id,
                test_groups=test_groups,
                train_count=len(train_idx),
                test_count=len(test_idx),
                selected_candidate=selected,
                selected_train_sharpe=valid.get(selected) if selected else None,
                selected_test_sharpe=test_sharpes.get(selected) if selected else None,
            )
        )
    return paths


def pbo_from_paths(
    events: list[TradeEvent],
    paths: list[CPCVPath],
    n_groups: int,
    n_test_groups: int,
    purge_days: int = 30,
    embargo_days: int = 5,
) -> float | None:
    if len(paths) == 0:
        return None

    events = sorted(events, key=lambda x: (x.decision_time, x.entry_time, x.candidate))
    groups = _group_assignments(events, n_groups)
    all_candidates = sorted({e.candidate for e in events})
    negative_logit = 0
    usable = 0

    for path in paths:
        test_idx = {i for i, g in enumerate(groups) if g in path.test_groups}
        train_idx = purged_train_indices(events, test_idx, purge_days, embargo_days)
        train = {}
        test = {}
        for candidate in all_candidates:
            train[candidate] = event_sharpe([events[i].return_on_risk for i in train_idx if events[i].candidate == candidate])
            test[candidate] = event_sharpe([events[i].return_on_risk for i in test_idx if events[i].candidate == candidate])
        if path.selected_candidate is None:
            continue
        out_vals = sorted(v for v in test.values() if v is not None)
        selected_oos = test.get(path.selected_candidate)
        if selected_oos is None or len(out_vals) < 2:
            continue
        rank = 1 + out_vals.index(selected_oos)
        percentile = (rank - 0.5) / len(out_vals)
        percentile = min(max(percentile, 1e-6), 1 - 1e-6)
        logit = math.log(percentile / (1 - percentile))
        if logit < 0:
            negative_logit += 1
        usable += 1

    return negative_logit / usable if usable else None


def approximate_dsr(returns: list[float], n_trials: int) -> float | None:
    """Approximate deflated Sharpe statistic using the standard-order-statistic benchmark.

    This is an approximation. It assumes comparable trial lengths and weak
    dependence between trials; the result is a diagnostic, not a promotion
    criterion by itself.
    """
    if n_trials < 1 or len(returns) < 3:
        return None
    sr = event_sharpe(returns)
    if sr is None:
        return None

    mean = sum(returns) / len(returns)
    sd = math.sqrt(sum((x - mean) ** 2 for x in returns) / (len(returns) - 1))
    if sd <= 0:
        return None
    skew = sum((x - mean) ** 3 for x in returns) / len(returns) / sd**3
    kurt = sum((x - mean) ** 4 for x in returns) / len(returns) / sd**4

    nd = NormalDist()
    euler_gamma = 0.5772156649015329
    q1 = nd.inv_cdf(1.0 - 1.0 / n_trials)
    q2 = nd.inv_cdf(1.0 - 1.0 / (n_trials * math.e))
    benchmark = (1.0 - euler_gamma) * q1 + euler_gamma * q2

    variance_sr = (
        1.0
        - skew * sr
        + ((kurt - 1.0) / 4.0) * sr * sr
    ) / (len(returns) - 1)
    if variance_sr <= 0 or not math.isfinite(variance_sr):
        return None
    return (sr - benchmark) / math.sqrt(variance_sr)
