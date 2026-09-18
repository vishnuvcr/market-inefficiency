        rate_for_ttm(a, b, c, t) if all(np.isfinite(v) for v in (a, b, c, t)) else np.nan
        for a, b, c, t in zip(x.yield_pct_91, x.yield_pct_182, x.yield_pct_364, x.T)
    ]

    # The contract master is used as a PIT validation input and supplies lot size.
    # Any source-provided lot_size is ignored in favor of the PIT master.
    x = x.drop(columns=["lot_size"], errors="ignore")
    lm = lot[["contract_id", "effective_from", "effective_to", "lot_size"]].copy()
    lm["effective_from"] = pd.to_datetime(lm["effective_from"])
    lm["effective_to"] = pd.to_datetime(lm["effective_to"])
    m = x[["contract_id", "trade_date"]].reset_index(names="_row_id").merge(lm, on="contract_id", how="left")
    m = m[m["trade_date"].ge(m["effective_from"]) & m["trade_date"].le(m["effective_to"])]
    if m["_row_id"].duplicated().any():
        raise SystemExit(f"{path}: overlapping lot-master intervals")
    x = x.merge(m[["_row_id", "lot_size"]], left_index=True, right_on="_row_id", how="left").set_index("_row_id")
    # lot_size now comes exclusively from the PIT contract master.

    # Remove the two documented external-input gaps from formal IV reconstruction.
    x = x[~x["date_key"].isin(GAP_DATES)].copy()
    x = x[
        x["settlement"].gt(0)
        & x["spot"].gt(0)
        & x["strike"].gt(0)
        & x["T"].gt(MIN_T)
        & x[["yield_pct_91", "yield_pct_182", "yield_pct_364"]].notna().all(axis=1)
        & x["lot_size"].gt(0)