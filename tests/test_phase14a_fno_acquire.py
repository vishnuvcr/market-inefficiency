from scripts.phase14a_fno_acquire import chunks

def test_chunks_cover_range():
    got = list(chunks(__import__("datetime").date(2020,1,1), __import__("datetime").date(2020,2,15), days=30))
    assert got[0] == (__import__("datetime").date(2020,1,1), __import__("datetime").date(2020,1,30))
    assert got[-1][1] == __import__("datetime").date(2020,2,15)