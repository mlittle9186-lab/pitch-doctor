"""Check #18: social media presence.

Deliberately modest in scope. Facebook and Instagram both put real profile
data behind a login wall, and nothing here logs in or scrapes past one -- so
this check reports what it can actually see (profiles linked from the website,
and whether those links resolve for an anonymous visitor) and openly marks the
rest as unverifiable rather than scoring a business down for it.

That is also why the worst outcome here is a warning, never critical: for most
micro-businesses, Google and the website matter more than social.
"""

from __future__ import annotations

from pitch_doctor.checks.base import find_social_profile_links, soupify
from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "social_presence"

# Probe outcomes the runner records in ``ctx.social_probes``.
REACHABLE = "reachable"
UNVERIFIABLE = "unverifiable"


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    detected = find_social_profile_links(soupify(ctx.html))

    if not detected:
        evidence = [strings.check_text(CHECK_ID, "found_warning")]
        # Without a website there was nowhere to look -- say that plainly
        # instead of implying the business has no social accounts.
        if not ctx.has_website:
            evidence.append(strings.check_text(CHECK_ID, "detail_no_website"))
        return CheckResult(
            id=CHECK_ID,
            name=strings.check_name(CHECK_ID),
            severity=Severity.WARNING,
            evidence=evidence,
            impact=strings.check_text(CHECK_ID, "impact_warning"),
            recommendation=strings.check_text(CHECK_ID, "benefit"),
        )

    platforms = sorted(detected)
    evidence = [
        strings.check_text(CHECK_ID, "found_ok", platforms=", ".join(platforms))
    ]

    unverifiable = [
        platform
        for platform in platforms
        if ctx.social_probes.get(platform, UNVERIFIABLE) != REACHABLE
    ]
    if unverifiable:
        evidence.append(
            strings.check_text(
                CHECK_ID, "issue_unverifiable", platforms=", ".join(unverifiable)
            )
        )

    return CheckResult(
        id=CHECK_ID,
        name=strings.check_name(CHECK_ID),
        severity=Severity.OK,
        evidence=evidence,
        impact=strings.check_text(CHECK_ID, "impact_ok"),
        recommendation=strings.check_text(CHECK_ID, "benefit"),
    )
