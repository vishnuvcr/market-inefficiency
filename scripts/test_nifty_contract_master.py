#!/usr/bin/env python3
"""Unit tests for the Phase 4A NIFTY contract-level lot-size mapper."""
import pandas as pd

from build_nifty_contract_master import legacy_map


def test_legacy_transition_rules() -> None:
    x = pd.DataFrame(
        {
            "trade_date": pd.to_datetime([
                "2020-04-13", "2021-07-08", "2021-07-29",
                "2024-04-25", "2024-04-26",
            ]),
            "expiry": pd.to_datetime([
                "2020-04-16", "2021-07-08", "2021-07-29",
                "2024-04-25", "2024-05-02",
            ]),
        }
    )
    y = legacy_map(x)
    assert y["lot_size"].tolist() == [75, 75, 50, 50, 25]
    assert y["source_version"].tolist() == [
        "NSE_FAOP44039",
        "NSE_FAOP47854",
        "NSE_FAOP47854",
        "NSE_FAOP61415",
        "NSE_FAOP61415",
    ]
    assert y["available_at"].tolist() == [
        "2020-03-31T23:59:59+00:00",
        "2021-03-31T23:59:59+00:00",
        "2021-03-31T23:59:59+00:00",
        "2024-04-02T23:59:59+00:00",
        "2024-04-02T23:59:59+00:00",
    ]


def main() -> int:
    test_legacy_transition_rules()
    print("NIFTY contract master tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
