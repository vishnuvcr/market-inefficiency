from pathlib import Path
import csv
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from phase13_trade_table_validator import validate

def write_csv(path: Path, rows):
    fields = [
        'candidate', 'decision_time', 'entry_time', 'exit_time',
        'contract_id', 'side', 'quantity', 'entry_fill', 'exit_fill',
        'gross_pnl', 'fees', 'taxes', 'net_pnl', 'capital_at_risk',
    ]
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def base(candidate='A', entry='2026-01-02T09:30:00Z', exit_='2026-02-02T09:30:00Z'):
    return {
        'candidate': candidate,
        'decision_time': '2026-01-02T09:00:00Z',
        'entry_time': entry,
        'exit_time': exit_,
        'contract_id': 'NIFTY|2026-03-26|25000|PE',
        'side': '1',
        'quantity': '65',
        'entry_fill': '100',
        'exit_fill': '110',
        'gross_pnl': '650',
        'fees': '20',
        'taxes': '5',
        'net_pnl': '625',
        'capital_at_risk': '5000',
    }

def test_valid_trade_table(tmp_path):
    p = tmp_path / 'trades.csv'
    write_csv(p, [base()])
    result = validate(p)
    assert result['status'] == 'PASS'
    assert result['rows'] == 1

def test_overlapping_same_candidate_rejected(tmp_path):
    p = tmp_path / 'trades.csv'
    r1 = base()
    r2 = base(entry='2026-01-15T09:30:00Z', exit_='2026-02-15T09:30:00Z')
    write_csv(p, [r1, r2])
    result = validate(p)
    assert result['status'] == 'FAIL'
    assert result['overlapping_same_candidate_rows'] == 1

def test_missing_columns_rejected(tmp_path):
    p = tmp_path / 'trades.csv'
    p.write_text('candidate,entry_time\nA,2026-01-02T09:30:00Z\n', encoding='utf-8')
    result = validate(p)
    assert result['status'] == 'FAIL'