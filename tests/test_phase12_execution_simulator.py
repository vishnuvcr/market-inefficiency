from pathlib import Path
import csv, sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from phase12_execution_simulator import Quote, LegOrder, execute_market, execute_synchronised, net_cash_flow

def test_public_fixture_has_executable_quotes():
    p=Path(__file__).parent/"fixtures/tickbytes_nifty_opt_sample.csv"
    with p.open(newline="",encoding="utf-8") as f:
        r=next(x for x in csv.DictReader(f) if float(x["bid_px"])>0 and float(x["ask_px"])>0)
    q=Quote(r["symbol"],r["datetime"],float(r["bid_px"]),float(r["bid_qty"]),float(r["ask_px"]),float(r["ask_qty"]))
    fill=execute_market(q,1,1)
    assert fill.price==q.ask

def test_two_leg_fill_uses_ask_for_buy_and_bid_for_sell():
    q1=Quote("A","2026-01-01T09:15:00Z",99,10,101,10)
    q2=Quote("B","2026-01-01T09:15:00Z",49,10,51,10)
    fills=execute_synchronised({"A":q1,"B":q2},[LegOrder("A",1,1),LegOrder("B",-1,1)])
    assert fills[0].price==101
    assert fills[1].price==49
    assert net_cash_flow(fills)==-52

def test_crossed_quote_rejected():
    q=Quote("A","2026-01-01T09:15:00Z",101,10,100,10)
    try:
        execute_market(q,1,1)
    except ValueError as e:
        assert "crossed" in str(e)
    else:
        raise AssertionError("crossed quote accepted")
