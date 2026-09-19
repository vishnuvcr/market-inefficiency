from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from phase10_execution_parser import (
    jiffies_to_utc,
    parse_order_line,
    parse_trade_line,
)


def pad(value, width):
    s = str(value)
    assert len(s) == width, (s, width)
    return s


def make_order(length=91):
    fields = [
        pad("RM", 2), pad("FAOb", 4), pad("0000000000000001", 16),
        pad("00000006553600", 14), pad("B", 1), pad("1", 1),
        pad("bbbbbNIFTY", 10), pad("OPTIDX", 6), pad("28MAR2027", 9),
        pad("00250000", 8), pad("PE", 2), pad("00000010", 8),
        pad("00012500", 8), pad("*", 1), pad("Y", 1)
    ]
    raw = "".join(fields)
    if length == 111:
        raw += "0" * (111 - len(raw))
    elif length == 112:
        raw += "0" * (112 - len(raw))
    return raw


def make_trade(length=103):
    fields = [
        pad("RM", 2), pad("FAOb", 4), pad("00000006553600", 14),
        pad("bbbbbNIFTY", 10), pad("OPTIDX", 6), pad("28MAR2027", 9),
        pad("00250000", 8), pad("PE", 2), pad("00012500", 8),
        pad("00000010", 8), pad("0000000000000001", 16),
        pad("0000000000000002", 16)
    ]
    raw = "".join(fields)
    if length == 123:
        raw += "0" * (123 - len(raw))
    elif length == 124:
        raw += "0" * (124 - len(raw))
    return raw


def test_jiffy_conversion_exact_second():
    assert jiffies_to_utc(0) == datetime(1980, 1, 1, tzinfo=timezone.utc)
    assert jiffies_to_utc(65536) == datetime(1980, 1, 1, 0, 0, 1, tzinfo=timezone.utc)


def test_trim_order_and_trade():
    o = parse_order_line(make_order(91), "2026-09-18")
    t = parse_trade_line(make_trade(103), "2026-09-18")
    assert o["source_format"] == "trim-v1.18"
    assert o["symbol"] == "NIFTY"
    assert o["strike"] == 2500.0
    assert o["quantity_lots"] == 10
    assert t["source_format"] == "trim-v1.18"
    assert t["trade_price"] == 125.0
    assert t["buy_order_number"] == 1
    assert t["sell_order_number"] == 2


def test_full_lengths_supported():
    assert parse_order_line(make_order(111), "2026-01-01")["raw_record_length"] == 111
    assert parse_order_line(make_order(112), "2026-01-01")["raw_record_length"] == 112
    assert parse_trade_line(make_trade(123), "2026-01-01")["raw_record_length"] == 123
    assert parse_trade_line(make_trade(124), "2026-01-01")["raw_record_length"] == 124
