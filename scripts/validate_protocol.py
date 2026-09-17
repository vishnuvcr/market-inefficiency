"""Deterministic repository-level research protocol checks."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "RESEARCH_PLAN.md",
    "STATUS.md",
    "docs/RESEARCH_CHARTER.md",
    "docs/HYPOTHESES.md",
    "docs/DATA_SPECIFICATION.md",
    "docs/VALIDATION_FRAMEWORK.md",
    "docs/SOURCE_AUDIT.md",
    "docs/EXPERIMENT_REGISTRY.md",
    "config/research_config.json",
]

REQUIRED_PLAN_PHASES = [f"Phase {i}" for i in range(10)]


def main() -> int:
    missing = [p for p in REQUIRED_FILES if not (ROOT / p).exists()]
    if missing:
        raise SystemExit(f"Missing required research files: {missing}")

    config = json.loads((ROOT / "config/research_config.json").read_text())
    required_flags = [
        "purging",
        "embargo",
        "cpcv",
        "dsr",
        "pbo",
        "untouched_holdout",
    ]
    validation = config.get("validation", {})
    missing_flags = [flag for flag in required_flags if validation.get(flag) is not True]
    if missing_flags:
        raise SystemExit(f"Validation controls disabled or missing: {missing_flags}")

    plan = (ROOT / "RESEARCH_PLAN.md").read_text()
    missing_phases = [phase for phase in REQUIRED_PLAN_PHASES if phase not in plan]
    if missing_phases:
        raise SystemExit(f"Missing research phases: {missing_phases}")

    hypotheses = (ROOT / "docs/HYPOTHESES.md").read_text()
    for prefix in ("H-A", "H-B", "H-C", "H-D", "H-E", "H-F", "H-G", "H-H"):
        if prefix not in hypotheses:
            raise SystemExit(f"Missing hypothesis track: {prefix}")

    print("Research protocol validation: PASS")
    print(f"Required files: {len(REQUIRED_FILES)}")
    print(f"Phases detected: {len(REQUIRED_PLAN_PHASES)}")
    print("Leakage controls: purging, embargo, CPCV")
    print("Multiple-testing controls: DSR, PBO, trial ledger")
    print("Holdout control: untouched final holdout")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
