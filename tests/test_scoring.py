from __future__ import annotations

from pitch_doctor.checks import ALL_CHECKS
from pitch_doctor.models import CheckResult, Severity
from pitch_doctor.scoring import CHECK_WEIGHTS, compute_score, grade_for_score, score_and_grade


def _result(check_id: str, severity: Severity) -> CheckResult:
    return CheckResult(
        id=check_id,
        name=check_id,
        severity=severity,
        evidence=["evidence"],
        impact="impact",
        recommendation="benefit",
    )


def test_all_ok_scores_100():
    checks = [_result(cid, Severity.OK) for cid in ("load_speed", "ssl", "reachability")]
    assert compute_score(checks) == 100


def test_single_critical_deducts_its_weight():
    checks = [_result("ssl", Severity.CRITICAL)]
    # ssl critical weight is 15 points per the documented table.
    assert compute_score(checks) == 85


def test_every_shipped_check_has_an_explicit_weight():
    # Guards against a new check silently falling back to the default weight.
    missing = [m.CHECK_ID for m in ALL_CHECKS if m.CHECK_ID not in CHECK_WEIGHTS]
    assert missing == []


def test_score_never_goes_below_zero():
    checks = [_result(m.CHECK_ID, Severity.CRITICAL) for m in ALL_CHECKS]
    assert compute_score(checks) == 0


def test_tier_one_alone_is_a_failing_grade():
    # A site that is slow, insecure, unreachable and broken on mobile fails
    # regardless of how it does on the other twelve checks.
    checks = [
        _result(cid, Severity.CRITICAL)
        for cid in ("load_speed", "ssl", "reachability", "mobile_rendering")
    ]
    score, grade = score_and_grade(checks)
    assert score == 46
    assert grade == "F"


def test_grade_bands():
    assert grade_for_score(95) == "A"
    assert grade_for_score(85) == "B"
    assert grade_for_score(75) == "C"
    assert grade_for_score(65) == "D"
    assert grade_for_score(40) == "F"


def test_score_and_grade_combo():
    checks = [_result("load_speed", Severity.WARNING)]
    score, grade = score_and_grade(checks)
    assert score == 92
    assert grade == "A"
