# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


"""CI gate: refuse to deploy a pattern/model update without bias parity.

Reads a bias audit JSON (produced by the BFF /bias-audit endpoint or an offline
run of the scoring engine across a labelled corpus) and exits 0 if parity holds,
non-zero otherwise.

Example:
    python -m scripts.verify_model_update \
        --audit docs/compliance/bias-audit-latest.json \
        --parity-delta 0.10
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shared.compliance.bias_gate import evaluate_bias_gate_from_dict


def main() -> int:
    parser = argparse.ArgumentParser(description="Model-update bias gate")
    parser.add_argument("--audit", required=True, help="Path to bias audit JSON file")
    parser.add_argument("--parity-delta", type=float, default=0.10)
    args = parser.parse_args()

    audit_path = Path(args.audit)
    if not audit_path.exists():
        print(f"ERROR: audit file {audit_path} does not exist", file=sys.stderr)
        return 2

    payload = json.loads(audit_path.read_text())
    groups = payload.get("groups", payload)
    report = evaluate_bias_gate_from_dict(groups, parity_delta=args.parity_delta)

    print(
        json.dumps(
            {
                "passed": report.passed,
                "parity_delta": report.parity_delta,
                "fpr_spread": round(report.fpr_spread, 4),
                "fnr_spread": round(report.fnr_spread, 4),
                "reasons": list(report.reasons),
            },
            indent=2,
        )
    )
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
