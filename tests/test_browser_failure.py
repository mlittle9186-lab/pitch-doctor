"""What the report says when our headless browser fails but the site is fine.

The bug this guards against: a Playwright failure used to be swallowed, leaving
``load_time_seconds=None`` and ``viewport_meta_present=False``, which the checks
then reported as confident criticals about the customer's site -- including the
nonsense sentence "your site takes N/As to show anything on a phone".
"""

from __future__ import annotations

from pitch_doctor.checks import load_speed, mobile_rendering
from pitch_doctor.models import ScanReport, Severity
from pitch_doctor.report.builder import BrandInfo, render_html
from tests.conftest import make_context

_MOBILE_READY = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
</head><body><p>hi</p></body></html>
"""

_NOT_MOBILE_READY = "<html><head><title>Old site</title></head><body><p>hi</p></body></html>"


def _browser_died(**overrides):
    """The page fetched fine over HTTP; only the browser stage blew up."""
    defaults = dict(
        html=_MOBILE_READY,
        load_time_seconds=None,
        mobile_overflow_px=None,
        viewport_meta_present=True,  # the runner derives this from the HTML
        browser_error="Executable doesn't exist at /ms-playwright/chromium-1148/chrome",
        dns_resolves=True,
        error=None,
    )
    defaults.update(overrides)
    return make_context(**defaults)


# --------------------------------------------------------------------------
# Load speed
# --------------------------------------------------------------------------


def test_unmeasurable_load_speed_never_says_n_a(strings_en):
    result = load_speed.evaluate(_browser_died(), strings_en)
    joined = " ".join(result.evidence) + result.impact
    assert "N/A" not in joined
    assert "N/As" not in joined


def test_a_browser_failure_is_not_blamed_on_the_site(strings_en):
    result = load_speed.evaluate(_browser_died(), strings_en)
    # Not critical, and flagged as unevaluated so it never drives a finding.
    assert result.severity == Severity.WARNING
    assert result.not_applicable is True
    assert "limitation of our scan" in result.impact


def test_the_browser_error_is_surfaced_for_diagnosis(strings_en):
    result = load_speed.evaluate(_browser_died(), strings_en)
    assert "/ms-playwright/" in result.evidence[0]


def test_an_unreachable_site_is_still_a_real_critical_finding(strings_en):
    # Distinct from a browser failure: here the site genuinely never loaded.
    ctx = make_context(
        html="",
        load_time_seconds=None,
        dns_resolves=False,
        error="DNS resolution failed",
        browser_error=None,
    )
    result = load_speed.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL
    assert result.not_applicable is False
    assert "N/A" not in result.impact
    assert "DNS resolution failed" in result.evidence[0]


def test_a_measured_load_time_is_unaffected(strings_en):
    ctx = make_context(load_time_seconds=1.4)
    result = load_speed.evaluate(ctx, strings_en)
    assert result.severity == Severity.OK
    assert "1.4" in result.evidence[0]


def test_spanish_unmeasured_copy_is_translated(strings_es):
    result = load_speed.evaluate(_browser_died(), strings_es)
    assert "N/A" not in result.impact
    assert "limitación de nuestro análisis" in result.impact


# --------------------------------------------------------------------------
# Mobile rendering
# --------------------------------------------------------------------------


def test_viewport_tag_in_the_html_is_not_reported_as_missing(strings_en):
    # The exact false positive that showed up on every production scan.
    result = mobile_rendering.evaluate(_browser_died(), strings_en)
    assert "no mobile viewport tag" not in " ".join(result.evidence)
    assert result.severity != Severity.CRITICAL


def test_a_half_checked_render_is_reported_as_such(strings_en):
    result = mobile_rendering.evaluate(_browser_died(), strings_en)
    assert result.severity == Severity.WARNING
    assert result.not_applicable is True
    assert "could not check whether content overflows" in result.evidence[0]


def test_a_genuinely_missing_viewport_tag_stays_critical(strings_en):
    # Knowable from the markup alone, so a dead browser doesn't excuse it --
    # but the report must still admit what it couldn't see.
    ctx = _browser_died(html=_NOT_MOBILE_READY, viewport_meta_present=False)
    result = mobile_rendering.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL
    assert "no mobile viewport tag" in result.evidence[0]
    assert any("was not checked" in item for item in result.evidence)


def test_overflow_is_not_claimed_when_nothing_was_rendered(strings_en):
    # A stale overflow value must never be reported as measured.
    ctx = _browser_died(mobile_overflow_px=400)
    result = mobile_rendering.evaluate(ctx, strings_en)
    assert "400px" not in " ".join(result.evidence)


def test_a_successful_render_is_unaffected(strings_en):
    ctx = make_context(viewport_meta_present=True, mobile_overflow_px=0, browser_error=None)
    result = mobile_rendering.evaluate(ctx, strings_en)
    assert result.severity == Severity.OK
    assert result.not_applicable is False


def test_real_overflow_is_still_caught(strings_en):
    ctx = make_context(viewport_meta_present=True, mobile_overflow_px=120, browser_error=None)
    result = mobile_rendering.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL
    assert "120px" in result.evidence[0]


# --------------------------------------------------------------------------
# The report
# --------------------------------------------------------------------------


def test_browser_failures_keep_their_own_cards_on_a_site_that_exists(strings_en):
    # They must not fall into the "No website to check" group -- there *is* a
    # website, we just failed to render it.
    ctx = _browser_died()
    checks = [load_speed.evaluate(ctx, strings_en), mobile_rendering.evaluate(ctx, strings_en)]
    report = ScanReport(
        url="https://joesplumbing.test",
        lang="en",
        checks=checks,
        score=86,
        grade="B",
        has_website=True,
    )
    html = render_html(report, strings_en, BrandInfo())
    assert "No website to check" not in html
    assert html.count('class="finding"') == 2
