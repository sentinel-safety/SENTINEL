# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.compliance.bias_gate import (
    BiasAuditReport,
    GroupRates,
    evaluate_bias_gate,
    evaluate_bias_gate_from_dict,
)

pytestmark = pytest.mark.unit


def _group(name: str, tp: int, fp: int, tn: int, fn: int) -> GroupRates:
    return GroupRates(
        group=name,
        total_cases=tp + fp + tn + fn,
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
    )


def test_passes_when_parity_within_10pct() -> None:
    audit = BiasAuditReport(
        groups=(
            _group("A", tp=50, fp=5, tn=95, fn=10),  # FPR=0.05, FNR=0.167
            _group("B", tp=60, fp=7, tn=93, fn=12),  # FPR=0.07, FNR=0.167
        )
    )
    report = evaluate_bias_gate(audit)
    assert report.passed is True
    assert report.reasons == ()


def test_fails_on_fpr_spread_above_10pct() -> None:
    audit = BiasAuditReport(
        groups=(
            _group("A", tp=50, fp=5, tn=95, fn=10),  # FPR=0.05
            _group("B", tp=50, fp=25, tn=75, fn=10),  # FPR=0.25 — 20% spread
        )
    )
    report = evaluate_bias_gate(audit)
    assert report.passed is False
    assert any("FPR spread" in r for r in report.reasons)


def test_fails_on_fnr_spread_above_10pct() -> None:
    audit = BiasAuditReport(
        groups=(
            _group("A", tp=50, fp=5, tn=95, fn=5),  # FNR=0.091
            _group("B", tp=30, fp=5, tn=95, fn=40),  # FNR=0.571
        )
    )
    report = evaluate_bias_gate(audit)
    assert report.passed is False
    assert any("FNR spread" in r for r in report.reasons)


def test_fails_when_single_group_only() -> None:
    audit = BiasAuditReport(groups=(_group("only", tp=50, fp=5, tn=95, fn=10),))
    report = evaluate_bias_gate(audit)
    assert report.passed is False
    assert any(">=2" in r for r in report.reasons)


def test_fails_when_empty_audit() -> None:
    audit = BiasAuditReport(groups=())
    report = evaluate_bias_gate(audit)
    assert report.passed is False


def test_fails_on_insufficient_group_size() -> None:
    audit = BiasAuditReport(
        groups=(
            _group("A", tp=5, fp=0, tn=20, fn=0),  # 25 cases
            _group("B", tp=60, fp=5, tn=90, fn=10),  # enough
        )
    )
    report = evaluate_bias_gate(audit)
    assert report.passed is False
    assert any("<30 is insufficient" in r for r in report.reasons)


def test_evaluate_from_dict_wrapper() -> None:
    report = evaluate_bias_gate_from_dict(
        {
            "A": {
                "total_cases": 160,
                "true_positives": 50,
                "false_positives": 5,
                "true_negatives": 95,
                "false_negatives": 10,
            },
            "B": {
                "total_cases": 172,
                "true_positives": 60,
                "false_positives": 7,
                "true_negatives": 93,
                "false_negatives": 12,
            },
        }
    )
    assert report.passed is True


def test_parity_delta_override() -> None:
    audit = BiasAuditReport(
        groups=(
            _group("A", tp=50, fp=5, tn=95, fn=10),
            _group("B", tp=50, fp=15, tn=85, fn=10),  # FPR spread ~10%
        )
    )
    strict = evaluate_bias_gate(audit, parity_delta=0.05)
    assert strict.passed is False
    lenient = evaluate_bias_gate(audit, parity_delta=0.15)
    assert lenient.passed is True
