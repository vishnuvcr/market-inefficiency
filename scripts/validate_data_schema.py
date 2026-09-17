"""Validate the repository's machine-readable Phase 2 data contract.

This checks the contract itself; it deliberately does not ingest or commit market data.
Actual dataset validation will consume immutable snapshots after acquisition.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "config/data_schema.json"

EXPECTED_LAYERS = {
    "underlying_eod",
    "option_eod",
    "contract_master",
    "india_vix",
    "risk_free",
    "intraday_quotes_trades",
}

REQUIRED_GLOBAL_RULES = {
    "reject_negative_prices",
    "reject_crossed_quotes",
    "flag_stale_quotes",
    "detect_duplicates",
    "require_contract_metadata",
    "require_point_in_time_available_at",
    "preserve_raw_source",
    "record_excluded_observations",
}


def main() -> int:
    if not SCHEMA.exists():
        raise SystemExit("Missing config/data_schema.json")

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    if schema.get("schema_version") != "1.0":
        raise SystemExit("Unsupported data schema version")
    if schema.get("timezone") != "Asia/Kolkata":
        raise SystemExit("Expected market timezone Asia/Kolkata")

    layers = schema.get("layers", {})
    missing_layers = EXPECTED_LAYERS - set(layers)
    if missing_layers:
        raise SystemExit(f"Missing data layers: {sorted(missing_layers)}")

    for name, layer in layers.items():
        required = layer.get("required", [])
        if "timestamp" not in required or "available_at" not in required:
            raise SystemExit(f"Layer {name} lacks timestamp/available_at PIT fields")
        if "key" not in layer or not layer["key"]:
            raise SystemExit(f"Layer {name} lacks a deterministic key")

    rules = schema.get("global_quality_rules", {})
    missing_rules = [r for r in REQUIRED_GLOBAL_RULES if rules.get(r) is not True]
    if missing_rules:
        raise SystemExit(f"Missing mandatory quality rules: {missing_rules}")

    manifest = schema.get("snapshot_manifest", {})
    required_manifest = {
        "dataset_id", "snapshot_created_at", "source", "source_version",
        "preprocessing_version", "code_commit", "sha256", "row_count",
    }
    if set(manifest.get("required", [])) != required_manifest:
        raise SystemExit("Snapshot manifest fields do not match the required contract")
    if manifest.get("immutable_dataset_id") is not True:
        raise SystemExit("Dataset IDs must be immutable")

    print("Data contract validation: PASS")
    print(f"Schema version: {schema['schema_version']}")
    print(f"Layers detected: {len(layers)}")
    print("PIT control: timestamp + available_at")
    print("Snapshot control: immutable dataset_id + SHA-256")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
