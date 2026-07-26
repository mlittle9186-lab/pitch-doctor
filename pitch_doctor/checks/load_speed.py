"""Check #1: mobile load speed.

Thresholds: <3s ok, 3-6s warning, >6s critical.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "load_speed"


def severity_for_seconds(seconds: float) -> Severity:
    if seconds < 3:
        return Severity.OK
    if seconds <= 6:
        return Severity.WARNING
    return Severity.CRITICAL


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    benefit = strings.check_text(CHECK_ID, "benefit")
    seconds = ctx.load_time_seconds

    if seconds is None:
        # Two very different reasons for having no number, and conflating them
        # is how a report ends up asserting "your site takes N/As to load".
        if ctx.error or not ctx.dns_resolves:
            # The site genuinely never loaded -- a real finding about the site.
            kind, severity, not_applicable = "unreachable", Severity.CRITICAL, False
            detail = ctx.error or ""
        else:
            # The page fetched fine; our headless browser is what failed.
            kind, severity, not_applicable = "unmeasured", Severity.WARNING, True
            detail = ctx.browser_error or ""
        return CheckResult(
            id=CHECK_ID,
            name=strings.check_name(CHECK_ID),
            severity=severity,
            evidence=[strings.check_text(CHECK_ID, f"found_{kind}", detail=detail)],
            impact=strings.check_text(CHECK_ID, f"impact_{kind}"),
            recommendation=benefit,
            not_applicable=not_applicable,
        )

    severity = severity_for_seconds(seconds)
    seconds_str = f"{seconds:.1f}"

    return CheckResult(
        id=CHECK_ID,
        name=strings.check_name(CHECK_ID),
        severity=severity,
        evidence=[strings.check_text(CHECK_ID, f"found_{severity.value}", seconds=seconds_str)],
        impact=strings.check_text(CHECK_ID, f"impact_{severity.value}", seconds=seconds_str),
        recommendation=benefit,
    )
