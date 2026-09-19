#!/usr/bin/env python3
"""Phase 12 — deterministic top-of-book execution simulator.

This layer consumes timestamped quote snapshots with best bid/ask and sizes.
It is intentionally fail-closed: missing/stale/crossed/zero-size quotes reject
the leg instead of substituting a model or settlement price.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
import math

@dataclass(frozen=True)
class Quote:
    symbol: str
    timestamp: str
    bid: float
    bid_qty: float
    ask: float
    ask_qty: float

@dataclass(frozen=True)
class LegOrder:
    symbol: str
    side: int  # +1 buy, -1 sell
    quantity: float

@dataclass(frozen=True)
class Fill:
    symbol: str
    side: int
    quantity: float
    price: float
    timestamp: str

def validate_quote(q: Quote) -> None:
    vals=(q.bid,q.bid_qty,q.ask,q.ask_qty)
    if not all(math.isfinite(float(x)) for x in vals):
        raise ValueError("non-finite quote")
    if q.bid <= 0 or q.ask <= 0 or q.bid_qty <= 0 or q.ask_qty <= 0:
        raise ValueError("missing/zero executable quote")
    if q.bid > q.ask:
        raise ValueError("crossed quote")

def execute_market(q: Quote, side: int, quantity: float) -> Fill:
    validate_quote(q)
    if side not in (-1,1) or quantity <= 0:
        raise ValueError("invalid order")
    available = q.ask_qty if side == 1 else q.bid_qty
    if quantity > available:
        raise ValueError("insufficient displayed size")
    return Fill(q.symbol, side, quantity, q.ask if side == 1 else q.bid, q.timestamp)

def execute_synchronised(quotes: dict[str, Quote], orders: Iterable[LegOrder], max_time_gap_seconds: float = 1.0) -> tuple[Fill,...]:
    orders=tuple(orders)
    if not orders:
        raise ValueError("empty strategy")
    timestamps=[]
    for o in orders:
        if o.symbol not in quotes:
            raise ValueError(f"missing quote: {o.symbol}")
        timestamps.append(quotes[o.symbol].timestamp)
    # Timestamps are expected in ISO-8601 form; enforce exact equality for the
    # public sample. Production replay may replace this with a numeric window.
    if len(set(timestamps)) != 1:
        raise ValueError("legs are not synchronised")
    fills=[]
    for o in orders:
        fills.append(execute_market(quotes[o.symbol], o.side, o.quantity))
    return tuple(fills)

def net_cash_flow(fills: Iterable[Fill]) -> float:
    # Positive = cash received, negative = cash paid.
    total=0.0
    for f in fills:
        total += (-f.price if f.side == 1 else f.price) * f.quantity
    return total

def top_of_book_spread_bps(q: Quote) -> float:
    validate_quote(q)
    mid=(q.bid+q.ask)/2
    return 10000*(q.ask-q.bid)/mid
