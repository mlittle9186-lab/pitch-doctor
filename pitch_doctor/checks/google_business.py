"""Check #17: Google Business Profile.

For a local business this is usually the *first* thing a customer sees -- often
before the website, and sometimes instead of it. A missing or neglected profile
costs more phone calls than most on-site problems do.

Pure decision logic: the Places API call happens in ``checks/runner.py`` and
arrives here as ``ctx.gbp``.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, GbpProfile, ScanContext, Severity

CHECK_ID = "google_business"

# Below this, a profile has too little social proof to win a comparison
# against a competitor down the street.
THIN_REVIEW_COUNT = 10
LOW_RATING = 4.0


def _unverified(strings: Strings, detail: str) -> CheckResult:
    """We could not look the profile up -- say so, rather than implying a pass.

    Marked not-applicable because the failure is ours (no API key, a quota, a
    dead network), not the business's: it still costs points so the score never
    flatters an unchecked profile, but it must not be quoted back as a finding
    the business needs to fix.
    """
    return CheckResult(
        id=CHECK_ID,
        name=strings.check_name(CHECK_ID),
        severity=Severity.WARNING,
        evidence=[strings.check_text(CHECK_ID, "found_unverified", detail=detail)],
        impact=strings.check_text(CHECK_ID, "impact_unverified"),
        recommendation=strings.check_text(CHECK_ID, "benefit"),
        not_applicable=True,
    )


def _collect_issues(gbp: GbpProfile, strings: Strings) -> tuple[list[str], bool]:
    """Profile weaknesses, plus whether any of them is severe enough to be critical."""
    issues: list[str] = []
    critical = False

    if (gbp.business_status or "").upper() == "CLOSED_PERMANENTLY":
        issues.append(strings.check_text(CHECK_ID, "issue_closed"))
        critical = True
    if not gbp.primary_type:
        issues.append(strings.check_text(CHECK_ID, "issue_no_category"))
    if not gbp.has_hours:
        issues.append(strings.check_text(CHECK_ID, "issue_no_hours"))
    if gbp.photo_count == 0:
        issues.append(strings.check_text(CHECK_ID, "issue_no_photos"))
    if gbp.review_count == 0:
        issues.append(strings.check_text(CHECK_ID, "issue_no_reviews"))
    elif gbp.review_count < THIN_REVIEW_COUNT:
        issues.append(strings.check_text(CHECK_ID, "issue_few_reviews", count=gbp.review_count))
    if gbp.rating is not None and gbp.rating < LOW_RATING:
        issues.append(strings.check_text(CHECK_ID, "issue_low_rating", rating=gbp.rating))

    return issues, critical


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    gbp = ctx.gbp

    if gbp is None:
        return _unverified(strings, strings.check_text(CHECK_ID, "detail_not_attempted"))
    if gbp.error:
        return _unverified(strings, gbp.error)

    if not gbp.found:
        query = ctx.business_name or ctx.url or ""
        return CheckResult(
            id=CHECK_ID,
            name=strings.check_name(CHECK_ID),
            severity=Severity.CRITICAL,
            evidence=[
                strings.check_text(
                    CHECK_ID,
                    "found_critical",
                    detail=strings.check_text(CHECK_ID, "detail_not_found", query=query),
                )
            ],
            impact=strings.check_text(CHECK_ID, "impact_critical"),
            recommendation=strings.check_text(CHECK_ID, "benefit"),
        )

    issues, critical = _collect_issues(gbp, strings)
    profile_name = gbp.name or ctx.business_name or ""

    if critical:
        severity = Severity.CRITICAL
    elif issues:
        severity = Severity.WARNING
    else:
        severity = Severity.OK

    if severity == Severity.OK:
        evidence = [
            strings.check_text(
                CHECK_ID,
                "found_ok",
                name=profile_name,
                rating=gbp.rating if gbp.rating is not None else "-",
                count=gbp.review_count,
                photos=gbp.photo_count,
            )
        ]
    else:
        evidence = [
            strings.check_text(
                CHECK_ID,
                f"found_{severity.value}",
                detail=strings.check_text(
                    CHECK_ID,
                    "detail_weak_profile",
                    name=profile_name,
                    issues="; ".join(issues),
                ),
            )
        ]

    # Owner replies are invisible to the Places API at every tier, so we note
    # the blind spot instead of guessing that reviews go unanswered.
    if gbp.review_count > 0 and gbp.reviews_without_reply is None:
        evidence.append(strings.check_text(CHECK_ID, "issue_replies_unknown"))

    return CheckResult(
        id=CHECK_ID,
        name=strings.check_name(CHECK_ID),
        severity=severity,
        evidence=evidence,
        impact=strings.check_text(CHECK_ID, f"impact_{severity.value}"),
        recommendation=strings.check_text(CHECK_ID, "benefit"),
    )
