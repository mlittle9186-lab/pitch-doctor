"""Check #3: mobile rendering.

Screenshots at iPhone (390x844) and desktop (1440x900) viewports are captured
by the runner and attached to the report so the owner sees their own site.
This module only judges the viewport meta tag and horizontal overflow.
"""

from __future__ import annotations

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, ScanContext, Severity

CHECK_ID = "mobile_rendering"

MINOR_OVERFLOW_PX = 20
MAJOR_OVERFLOW_PX = 50


def evaluate(ctx: ScanContext, strings: Strings) -> CheckResult:
    benefit = strings.check_text(CHECK_ID, "benefit")
    screenshots = [s for s in (ctx.mobile_screenshot_b64, ctx.desktop_screenshot_b64) if s]
    # Overflow can only be seen by actually rendering the page. The viewport
    # tag, by contrast, is in the markup and stays knowable either way.
    overflow_known = ctx.browser_error is None and ctx.dns_resolves and not ctx.error
    overflow = ctx.mobile_overflow_px or 0
    missing_viewport = not ctx.viewport_meta_present

    issue_fragments = []
    if missing_viewport:
        issue_fragments.append(strings.check_text(CHECK_ID, "issue_viewport"))
    if overflow_known and overflow > MINOR_OVERFLOW_PX:
        issue_fragments.append(strings.check_text(CHECK_ID, "issue_overflow", px=overflow))

    # A missing viewport tag is a real finding whether or not we could render,
    # so it still lands as critical. But when the page never rendered and the
    # tag *is* there, the honest verdict is "half-checked", not "looks good".
    if missing_viewport or (overflow_known and overflow > MAJOR_OVERFLOW_PX):
        severity = Severity.CRITICAL
    elif overflow_known and overflow > MINOR_OVERFLOW_PX:
        severity = Severity.WARNING
    elif not overflow_known:
        return CheckResult(
            id=CHECK_ID,
            name=strings.check_name(CHECK_ID),
            severity=Severity.WARNING,
            evidence=[
                strings.check_text(
                    CHECK_ID, "found_partial", detail=ctx.browser_error or ctx.error or ""
                )
            ],
            impact=strings.check_text(CHECK_ID, "impact_partial"),
            recommendation=benefit,
            screenshots=screenshots,
            not_applicable=True,
        )
    else:
        severity = Severity.OK

    issues_str = "; ".join(issue_fragments)
    if severity == Severity.OK:
        evidence = [strings.check_text(CHECK_ID, "found_ok")]
    else:
        evidence = [strings.check_text(CHECK_ID, f"found_{severity.value}", issues=issues_str)]
    if not overflow_known:
        # Say what we could not see, so a critical verdict isn't read as complete.
        evidence.append(strings.check_text(CHECK_ID, "issue_overflow_unknown"))

    return CheckResult(
        id=CHECK_ID,
        name=strings.check_name(CHECK_ID),
        severity=severity,
        evidence=evidence,
        impact=strings.check_text(CHECK_ID, f"impact_{severity.value}"),
        recommendation=benefit,
        screenshots=screenshots,
    )
