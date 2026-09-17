"""Create a deterministic manifest for an acquired research snapshot.

The manifest records source/provenance and SHA-256 hashes. It does not upload or
modify source data and therefore can be used with restricted/licensed datasets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--source-version", required=True)
    parser.add_argument("--preprocessing-version", required=True)
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()

    if not args.input.is_file():
        raise SystemExit(f"Snapshot input does not exist: {args.input}")
    payload = {
        "dataset_id": args.dataset_id,
        "snapshot_created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": args.source,
        "source_version": args.source_version,
        "preprocessing_version": args.preprocessing_version,
        "code_commit": args.code_commit,
        "sha256": sha256(args.input),
        "row_count": None,
        "input_path_label": args.input.name,
    }
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("records"), list):
            payload["row_count"] = len(data["records"])
        elif isinstance(data, list):
            payload["row_count"] = len(data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Snapshot manifest created: {args.output}")
    print(f"sha256={payload['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
