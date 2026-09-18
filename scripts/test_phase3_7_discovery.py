#!/usr/bin/env python3
"""Smoke test for Phase 3.7 discovery diagnostics."""
from pathlib import Path
import json
import subprocess
import tempfile
import pandas as pd


def main():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)

        # The production sessionizer represents each trading session by
        # session-date midnight in Asia/Kolkata converted to UTC. Build the
        # synthetic NIFTY timestamps with the same convention so the merge
        # tests the intended date alignment rather than an arbitrary timezone.
        session_dates = pd.date_range(
            "2024-01-01", periods=40, freq="D", tz="Asia/Kolkata"
        )
        n = pd.DataFrame(
            {
                "timestamp": session_dates,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": [100 + i * 0.1 for i in range(40)],
            }
        )
        n.to_csv(td / "nifty.csv", index=False)

        rows = []
        for session_date in session_dates:
            local_date = session_date.date()
            for minute in range(6):
                rows.append(
                    {
                        "date": f"{local_date} 09:{15 + minute:02d}:00",
                        "open": 15,
                        "high": 16,
                        "low": 14,
                        "close": 15.5,
                        "volume": 0,
                    }
                )
        pd.DataFrame(rows).to_csv(td / "vix.csv", index=False)

        out = td / "out.json"
        subprocess.run(
            [
                "python",
                "scripts/phase3_7_discovery.py",
                "--nifty",
                str(td / "nifty.csv"),
                "--vix",
                str(td / "vix.csv"),
                "--output",
                str(out),
            ],
            check=True,
        )
        x = json.loads(out.read_text())
        assert x["phase"] == "3.7"
        assert x["diagnostic_only"] is True
        assert x["execution_backtest_allowed"] is False
        assert x["overlap_rows"] == 40
        assert "conditional_by_vix_tercile" in x
        print("Phase 3.7 discovery test passed.")


if __name__ == "__main__":
    main()
