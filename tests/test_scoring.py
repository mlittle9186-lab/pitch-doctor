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
    # A business that is slow, insecure, unreachable, broken on mobile and
    # invisible on Google fails regardless of the other thirteen checks.
    checks = [
        _result(cid, Severity.CRITICAL)
        for cid in (
            "load_speed",
            "ssl",
            "reachability",
            "mobile_rendering",
            "google_business",
        )
    ]
    score, grade = score_and_grade(checks)
    assert score == 34
    assert grade == "F"


def test_google_business_outweighs_every_tier_two_check():
    # For a local business the Google listing is often the only thing a nearby
    # customer sees, so it has to cost more than an on-site nicety.
    assert CHECK_WEIGHTS["google_business"]["critical"] > CHECK_WEIGHTS["seo_advanced"]["critical"]
    assert CHECK_WEIGHTS["google_business"]["critical"] == 12


def test_social_presence_is_the_lightest_check():
    # It's the one we can verify least, so it must never dominate a score.
    lightest = min(w["critical"] for w in CHECK_WEIGHTS.values())
    assert CHECK_WEIGHTS["social_presence"]["critical"] == lightest


def test_a_missing_google_profile_alone_is_not_a_failing_grade():
    # A business whose only problem is an unclaimed listing still has a
    # working website -- the report should say "fix this", not "start over".
    score, grade = score_and_grade([_result("google_business", Severity.CRITICAL)])
    assert score == 88
    assert grade == "B"


def test_the_sixteen_website_checks_alone_floor_the_score_at_zero():
    # This is what a business with no website scores: every website check is
    # reported as a not-applicable critical, which sums past 100 on its own.
    from pitch_doctor.checks import WEBSITE_CHECK_IDS

    checks = [_result(cid, Severity.CRITICAL) for cid in WEBSITE_CHECK_IDS]
    assert compute_score(checks) == 0


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
