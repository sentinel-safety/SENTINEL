# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


"""Model-update bias gate.

Per SENTINEL spec §14 acceptance criteria, a model or pattern update cannot ship
unless the bias audit shows parity within 10% across measured demographic
groups. This module provides the pure-Python gate used by the deployment
pipeline.

Usage from deployment tooling:

    from shared.compliance.bias_gate import evaluate_bias_gate, BiasGateReport

    report = evaluate_bias_gate(audit)
    if not report.passed:
        raise SystemExit(f"bias gate failed: {report.reasons}")
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from pydantic import Field

from shared.schemas.base import FrozenModel

_DEFAULT_PARITY_DELTA: Final[float] = 0.10
"""Maximum allowed FP-rate or FN-rate variance across demographic groups."""


class GroupRates(FrozenModel):
    group: str = Field(min_length=1, max_length=120)
    total_cases: int = Field(ge=0)
    true_positives: int = Field(ge=0)
    false_positives: int = Field(ge=0)
    true_negatives: int = Field(ge=0)
    false_negatives: int = Field(ge=0)

    @property
    def fpr(self) -> float:
        denom = self.false_positives + self.true_negatives
        return self.false_positives / denom if denom else 0.0

    @property
    def fnr(self) -> float:
        denom = self.false_negatives + self.true_positives
        return self.false_negatives / denom if denom else 0.0


class BiasAuditReport(FrozenModel):
    groups: tuple[GroupRates, ...]


class BiasGateReport(FrozenModel):
    passed: bool
    parity_delta: float
    fpr_spread: float
    fnr_spread: float
    reasons: tuple[str, ...]


def evaluate_bias_gate(
    audit: BiasAuditReport, *, parity_delta: float = _DEFAULT_PARITY_DELTA
) -> BiasGateReport:
    if len(audit.groups) == 0:
        return BiasGateReport(
            passed=False,
            parity_delta=parity_delta,
            fpr_spread=0.0,
            fnr_spread=0.0,
            reasons=("bias audit contains zero groups; cannot evaluate parity",),
        )
    if len(audit.groups) < 2:
        return BiasGateReport(
            passed=False,
            parity_delta=parity_delta,
            fpr_spread=0.0,
            fnr_spread=0.0,
            reasons=(
                "bias audit requires >=2 demographic groups; single-group audits cannot "
                "demonstrate parity",
            ),
        )
    fprs = [g.fpr for g in audit.groups]
    fnrs = [g.fnr for g in audit.groups]
    fpr_spread = max(fprs) - min(fprs)
    fnr_spread = max(fnrs) - min(fnrs)
    reasons: list[str] = []
    if fpr_spread > parity_delta:
        reasons.append(f"FPR spread {fpr_spread:.3f} exceeds parity delta {parity_delta:.3f}")
    if fnr_spread > parity_delta:
        reasons.append(f"FNR spread {fnr_spread:.3f} exceeds parity delta {parity_delta:.3f}")
    for g in audit.groups:
        if g.total_cases < 30:
            reasons.append(f"group '{g.group}' has only {g.total_cases} cases; <30 is insufficient")
    return BiasGateReport(
        passed=len(reasons) == 0,
        parity_delta=parity_delta,
        fpr_spread=fpr_spread,
        fnr_spread=fnr_spread,
        reasons=tuple(reasons),
    )


def evaluate_bias_gate_from_dict(
    groups: Mapping[str, Mapping[str, int]],
    *,
    parity_delta: float = _DEFAULT_PARITY_DELTA,
) -> BiasGateReport:
    """Convenience wrapper for CLI callers passing JSON-shaped dicts."""
    audit = BiasAuditReport(
        groups=tuple(
            GroupRates(
                group=name,
                total_cases=int(metrics.get("total_cases", 0)),
                true_positives=int(metrics.get("true_positives", 0)),
                false_positives=int(metrics.get("false_positives", 0)),
                true_negatives=int(metrics.get("true_negatives", 0)),
                false_negatives=int(metrics.get("false_negatives", 0)),
            )
            for name, metrics in groups.items()
        )
    )
    return evaluate_bias_gate(audit, parity_delta=parity_delta)
