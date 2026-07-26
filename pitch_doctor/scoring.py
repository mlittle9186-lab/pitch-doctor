"""The pitch-doctor health-score formula.

Every check contributes a fixed point deduction depending on its severity.
Deductions are summed and subtracted from a perfect 100. This is intentionally
simple and transparent -- a freelancer reading the report (or its README)
should be able to reconstruct the number by hand.

    score = max(0, 100 - sum(deduction(check) for check in checks))

Weight table (points lost per check, by severity). "ok" always costs 0.
These weights roughly track how directly the issue costs the business
customers versus how much it merely looks unpolished, in three tiers.

Tier 1 -- the visitor never gets to see the site, or doesn't trust it:

+--------------------------+----------+---------+
| check                    | critical | warning |
+--------------------------+----------+---------+
| load_speed               |    15    |    8    |
| ssl                      |    15    |    8    |
| reachability             |    12    |    6    |
| mobile_rendering         |    12    |    6    |
+--------------------------+----------+---------+

Tier 2 -- the visitor arrives but can't find, use, or act on the site:

+--------------------------+----------+---------+
| security_headers         |     8    |    4    |
| broken_links             |     8    |    4    |
| contact_friction         |     8    |    4    |
| search_visibility        |     8    |    4    |
| accessibility            |     7    |    3    |
| seo_advanced             |     6    |    3    |
| compliance               |     6    |    3    |
+--------------------------+----------+---------+

Tier 3 -- polish, conversion, and measurement:

+--------------------------+----------+---------+
| outdated_signals         |     5    |    3    |
| mobile_ux_advanced       |     5    |    3    |
| user_experience          |     5    |    3    |
| performance_optimization |     5    |    3    |
| analytics_tracking       |     4    |    2    |
+--------------------------+----------+---------+

The weights are deliberately front-loaded: the four Tier 1 checks alone can
cost 54 points, so a site that is slow, insecure, unreachable and unusable on
a phone lands in F territory no matter how well it does on the rest. All 16
checks at critical sum to 129, which is more than 100 -- the score floors at
0 rather than going negative.

Letter grades follow the usual US school scale:
A 90-100, B 80-89, C 70-79, D 60-69, F below 60.
"""

from __future__ import annotations

from pitch_doctor.models import CheckResult, Severity

CHECK_WEIGHTS: dict[str, dict[str, int]] = {
    # Tier 1 -- reach and trust.
    "load_speed": {"critical": 15, "warning": 8},
    "ssl": {"critical": 15, "warning": 8},
    "reachability": {"critical": 12, "warning": 6},
    "mobile_rendering": {"critical": 12, "warning": 6},
    # Tier 2 -- findability and usability.
    "security_headers": {"critical": 8, "warning": 4},
    "broken_links": {"critical": 8, "warning": 4},
    "contact_friction": {"critical": 8, "warning": 4},
    "search_visibility": {"critical": 8, "warning": 4},
    "accessibility": {"critical": 7, "warning": 3},
    "seo_advanced": {"critical": 6, "warning": 3},
    "compliance": {"critical": 6, "warning": 3},
    # Tier 3 -- polish, conversion, measurement.
    "outdated_signals": {"critical": 5, "warning": 3},
    "mobile_ux_advanced": {"critical": 5, "warning": 3},
    "user_experience": {"critical": 5, "warning": 3},
    "performance_optimization": {"critical": 5, "warning": 3},
    "analytics_tracking": {"critical": 4, "warning": 2},
}


def deduction_for(check: CheckResult) -> int:
    if check.severity == Severity.OK:
        return 0
    weights = CHECK_WEIGHTS.get(check.id, {"critical": 10, "warning": 5})
    return weights.get(check.severity.value, 0)


def compute_score(checks: list[CheckResult]) -> int:
    total_deduction = sum(deduction_for(c) for c in checks)
    return max(0, 100 - total_deduction)


def grade_for_score(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def score_and_grade(checks: list[CheckResult]) -> tuple[int, str]:
    score = compute_score(checks)
    return score, grade_for_score(score)
