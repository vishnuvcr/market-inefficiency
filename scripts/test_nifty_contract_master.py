#!/usr/bin/env python3
"""Unit tests for the Phase 4A NIFTY contract-level lot-size mapper."""
from datetime import date

from build_nifty_contract_master import legacy_lot


def test_legacy_transition_rules() -> None:
    lot, source, available = legacy_lot(date(2020, 4, 13), date(2020, 4, 30))
    assert lot == 75
    assert source == "NSE_FAOP44039"
    assert available == "2020-03-31"

    lot, source, available = legacy_lot(date(2021, 7, 8), date(2021, 7, 8))
    assert lot == 75
    assert source == "NSE_FAOP47854"
    assert available == "2021-03-31"

    lot, source, _ = legacy_lot(date(2021, 7, 29), date(2021, 7, 29))
    assert lot == 50
    assert source == "NSE_FAOP47854"

    lot, source, _ = legacy_lot(date(2024, 4, 25), date(2024, 4, 25))
    assert lot == 50
    assert source == "NSE_FAOP47854"

    lot, source, available = legacy_lot(date(2024, 4, 26), date(2024, 5, 2))
    assert lot == 25
    assert source == "NSE_FAOP61415"
    assert available == "2024-04-02"


def main() -> int:
    test_legacy_transition_rules()
    print("NIFTY contract master tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
