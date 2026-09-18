"""Point-in-time enrich normalized derivative observations with contract metadata."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_ts(value: str | None) -> datetime | None:
    if value in (None, "", "-"):
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def contract_key(row: dict) -> str:
    return str(row.get("contract_id") or "").strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--observations", required=True, type=Path)
    parser.add_argument("--contract-master", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--decision-timestamp", required=True)
    args = parser.parse_args()

    decision_ts = parse_ts(args.decision_timestamp)
    if decision_ts is None:
        raise SystemExit("Invalid decision timestamp")
    observations = json.loads(args.observations.read_text(encoding="utf-8"))
    with args.contract_master.open("r", encoding="utf-8-sig", newline="") as fh:
        master_rows = list(csv.DictReader(fh))

    grouped: dict[str, list[dict]] = {}
    for row in master_rows:
        grouped.setdefault(contract_key(row), []).append(row)

    output_records = []
    exclusions = []
    for idx, obs in enumerate(observations.get("records", [])):
        key = obs.get("instrument_id", "")
        obs_ts = parse_ts(obs.get("timestamp"))
        candidates = []
        for master in grouped.get(key, []):
            effective_from = parse_ts(master.get("effective_from"))
            effective_to = parse_ts(master.get("effective_to"))
            available_at = parse_ts(master.get("available_at"))
            if not effective_from or not available_at or not obs_ts:
                continue
            if effective_from <= obs_ts and (effective_to is None or obs_ts <= effective_to) and available_at <= decision_ts:
                candidates.append(master)
        if len(candidates) != 1:
            reason = "CONTRACT_MASTER_NOT_FOUND" if not candidates else "CONTRACT_MASTER_AMBIGUOUS"
            exclusions.append({"record_index": idx, "instrument_id": key, "timestamp": obs.get("timestamp"), "reason_code": reason})
            continue
        master = candidates[0]
        enriched = dict(obs)
        enriched["contract_id"] = key
        enriched["lot_size"] = float(master["lot_size"]) if master.get("lot_size") not in (None, "") else None
        enriched["contract_effective_from"] = master.get("effective_from")
        enriched["contract_effective_to"] = master.get("effective_to")
        enriched["contract_master_available_at"] = master.get("available_at")
        enriched["contract_master_source_version"] = master.get("source_version")
        output_records.append(enriched)

    raw_hash = hashlib.sha256(args.contract_master.read_bytes()).hexdigest()
    report = {
        "dataset_id": observations.get("dataset_id"),
        "contract_master_sha256": raw_hash,
        "decision_timestamp": args.decision_timestamp,
        "input_row_count": len(observations.get("records", [])),
        "enriched_row_count": len(output_records),
        "excluded_row_count": len(exclusions),
        "exclusions": exclusions,
        "status": "PASS" if not exclusions else "RECONCILIATION_REJECT_ROWS",
        "records": output_records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Contract reconciliation: {len(output_records)}/{len(observations.get('records', []))} enriched")
    print(f"Status: {report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
