from __future__ import annotations

from pitch_doctor.checks import load_speed
from pitch_doctor.models import Severity
from tests.conftest import make_context


def test_fast_load_is_ok(strings_en):
    ctx = make_context(load_time_seconds=1.5)
    result = load_speed.evaluate(ctx, strings_en)
    assert result.severity == Severity.OK


def test_borderline_load_is_warning(strings_en):
    ctx = make_context(load_time_seconds=4.2)
    result = load_speed.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING
    assert "4.2" in result.impact


def test_slow_load_is_critical(strings_en):
    ctx = make_context(load_time_seconds=9.0)
    result = load_speed.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL
    assert "9.0" in result.impact


def test_unmeasurable_load_on_a_reachable_site_is_not_blamed_on_the_site(strings_en):
    # No number, but the site answered fine -- so the render failed on our end.
    # Reporting that as critical (as this once did) asserts the site is slow on
    # the strength of our own failure. See tests/test_browser_failure.py.
    ctx = make_context(load_time_seconds=None)
    result = load_speed.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING
    assert result.not_applicable is True


def test_unmeasurable_load_on_an_unreachable_site_is_critical(strings_en):
    ctx = make_context(load_time_seconds=None, dns_resolves=False, error="DNS resolution failed")
    result = load_speed.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL
    assert result.not_applicable is False


def test_fast_load_renders_in_all_four_languages(strings_en, strings_es, strings_fr, strings_zh):
    ctx = make_context(load_time_seconds=1.0)
    for strings in (strings_en, strings_es, strings_fr, strings_zh):
        result = load_speed.evaluate(ctx, strings)
        assert result.severity == Severity.OK
        assert "1.0" in result.impact
        assert result.name  # non-empty localized check name
