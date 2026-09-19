from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from phase12_quote_normalizer import load


def test_tickbytes_schema_normalizes():
    p = Path(__file__).parent / "fixtures/tickbytes_nifty_opt_sample.csv"
    schema, rows, errors = load(p)
    assert schema == "tickbytes_l1"
    assert rows
    assert errors
    assert all(r.bid > 0 and r.ask > 0 for r in rows)


def test_optionvault_schema_normalizes():
    p = Path(__file__).parent / "fixtures/optionvault_nifty_level2_sample.csv"
    schema, rows, errors = load(p)
    assert schema == "optionvault_l2"
    assert len(rows) == 13
    assert not errors
