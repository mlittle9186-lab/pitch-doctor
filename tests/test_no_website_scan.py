"""A business with no website is a valid -- and for a freelancer, the most
valuable -- thing to audit. These tests pin down what such a scan produces.
"""

from __future__ import annotations

from pathlib import Path

from pitch_doctor.checks import PRESENCE_CHECKS, WEBSITE_CHECK_IDS
from pitch_doctor.checks.base import extract_business_name, extract_city
from pitch_doctor.checks.runner import build_scan_context, run_all_checks
from pitch_doctor.i18n import load_strings
from pitch_doctor.models import GbpProfile, ScanReport, Severity
from pitch_doctor.report.builder import BrandInfo, render_html, write_report
from pitch_doctor.scoring import compute_score, score_and_grade
from tests.conftest import make_context

_PRESENCE_IDS = {module.CHECK_ID for module in PRESENCE_CHECKS}


def _websiteless_checks(strings, gbp=None):
    ctx = make_context(
        url=None,
        final_url="",
        html="",
        status_code=None,
        headers={},
        load_time_seconds=None,
        has_valid_ssl=False,
        dns_resolves=False,
        viewport_meta_present=False,
        mobile_overflow_px=None,
        business_name="Joe's Plumbing",
        city="Houston",
        has_website=False,
        gbp=gbp,
    )
    return run_all_checks(ctx, strings)


def test_every_website_check_is_reported_as_not_applicable(strings_en):
    checks = _websiteless_checks(strings_en)
    website_results = [c for c in checks if c.id in WEBSITE_CHECK_IDS]

    assert len(website_results) == len(WEBSITE_CHECK_IDS)
    for result in website_results:
        assert result.not_applicable is True
        assert result.severity == Severity.CRITICAL
        assert "no website" in result.evidence[0]


def test_presence_checks_still_run_for_a_websiteless_business(strings_en):
    checks = _websiteless_checks(strings_en, gbp=GbpProfile(found=False))
    presence = [c for c in checks if c.id in _PRESENCE_IDS]

    assert {c.id for c in presence} == _PRESENCE_IDS
    # They did real work, so they are not marked as skipped.
    assert all(c.not_applicable is False for c in presence)


def test_not_applicable_results_keep_their_localised_check_name(strings_es):
    checks = _websiteless_checks(strings_es)
    by_id = {c.id: c for c in checks}
    # Names come from each module, so the eight translated checks stay translated.
    assert by_id["ssl"].name == "Seguridad SSL / HTTPS"
    assert by_id["contact_friction"].name == "Fricción de Contacto"


def test_a_websiteless_business_scores_zero(strings_en):
    checks = _websiteless_checks(strings_en, gbp=GbpProfile(found=False))
    score, grade = score_and_grade(checks)
    assert score == 0
    assert grade == "F"


def test_a_perfect_google_profile_cannot_rescue_a_missing_website(strings_en):
    strong = GbpProfile(
        found=True,
        name="Joe's Plumbing",
        primary_type="Plumber",
        business_status="OPERATIONAL",
        has_hours=True,
        photo_count=20,
        rating=4.9,
        review_count=200,
    )
    checks = _websiteless_checks(strings_en, gbp=strong)
    by_id = {c.id: c for c in checks}
    assert by_id["google_business"].severity == Severity.OK
    assert compute_score(checks) == 0


async def test_scan_without_a_url_produces_a_valid_report(monkeypatch, tmp_path):
    # No API key, so the Google lookup degrades -- and the scan still completes
    # end to end without touching the network or a browser.
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)

    ctx = await build_scan_context(
        None,
        timeout=5.0,
        business_name="Joe's Plumbing",
        city="Houston",
        places_cache_path=tmp_path / "places.db",
    )
    assert ctx.has_website is False
    assert ctx.url is None
    assert ctx.business_name == "Joe's Plumbing"
    assert ctx.gbp is not None and ctx.gbp.error is not None

    strings = load_strings("en")
    checks = run_all_checks(ctx, strings)
    score, grade = score_and_grade(checks)
    report = ScanReport(
        url=None,
        lang="en",
        checks=checks,
        score=score,
        grade=grade,
        business_name=ctx.business_name,
        city=ctx.city,
        has_website=False,
    )

    html = render_html(report, strings, BrandInfo(name="Acme Web Studio"))
    # Jinja autoescapes, so the apostrophe arrives as an entity.
    assert "Joe&#39;s Plumbing" in html
    assert "Houston" in html
    # The grouped section replaces sixteen identical finding pages.
    assert "No website to check" in html


async def test_report_for_a_websiteless_business_gets_a_business_filename(monkeypatch, tmp_path):
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)
    strings = load_strings("en")
    report = ScanReport(
        url=None,
        lang="en",
        checks=_websiteless_checks(strings, gbp=GbpProfile(found=False)),
        score=0,
        grade="F",
        business_name="Joe's Plumbing",
        city="Houston",
        has_website=False,
    )
    path = write_report(report, strings, BrandInfo(), Path(tmp_path))
    assert path.name == "Joe-s-Plumbing-Houston.html"
    assert path.exists()


def _websiteless_report(strings, gbp):
    checks = _websiteless_checks(strings, gbp=gbp)
    score, grade = score_and_grade(checks)
    return ScanReport(
        url=None,
        lang="en",
        checks=checks,
        score=score,
        grade=grade,
        business_name="Joe's Plumbing",
        city="Houston",
        has_website=False,
    )


def test_cta_recommends_the_basic_package_when_there_is_no_website(strings_en):
    html = render_html(
        _websiteless_report(strings_en, GbpProfile(found=False)), strings_en, BrandInfo()
    )
    assert "Basic ($500)" in html
    # A missing Google listing is a Growth problem.
    assert "Growth" in html
    # There is no site to reduce contact friction on, so don't suggest it.
    assert "Professional ($1,000)" not in html


def test_an_unverifiable_google_lookup_does_not_recommend_growth(strings_en):
    # Failing to check the listing is our problem, not a diagnosis we can bill
    # against -- so it must not turn into a recommendation.
    unverified = GbpProfile(found=False, error="GOOGLE_PLACES_API_KEY is not set")
    html = render_html(_websiteless_report(strings_en, unverified), strings_en, BrandInfo())
    assert "Basic ($500)" in html
    assert "Growth" not in html


def test_an_unverifiable_google_check_keeps_its_own_card(strings_en):
    # It is grouped with neither the website checks nor hidden -- the reason it
    # couldn't be checked is specific and worth reading.
    unverified = GbpProfile(found=False, error="Places API returned 429: quota")
    html = render_html(_websiteless_report(strings_en, unverified), strings_en, BrandInfo())
    assert "429" in html
    assert html.count("not-evaluated-name") == 17  # 16 website rows + the CSS rule


# --------------------------------------------------------------------------
# Inferring the business from the page, when a URL *is* given
# --------------------------------------------------------------------------

_JSONLD_PAGE = """
<html><head>
  <title>Joe's Plumbing | 24/7 Emergency Service in Houston</title>
  <script type="application/ld+json">
  {"@context": "https://schema.org", "@type": "LocalBusiness",
   "name": "Joe's Plumbing LLC",
   "address": {"@type": "PostalAddress", "addressLocality": "Houston", "addressRegion": "TX"}}
  </script>
</head><body></body></html>
"""

_TITLE_ONLY_PAGE = """
<html><head><title>Corner Barber Shop - Best Cuts in Town</title></head><body></body></html>
"""

_GRAPH_PAGE = """
<html><head>
  <script type="application/ld+json">
  {"@graph": [{"@type": "WebSite", "name": "Ignore me"},
              {"@type": "Organization", "name": "Graph Motors",
               "address": {"addressLocality": "Katy"}}]}
  </script>
</head><body></body></html>
"""

_BROKEN_JSONLD_PAGE = """
<html><head>
  <title>Fallback Bakery | Fresh Daily</title>
  <script type="application/ld+json">{ this is not json </script>
</head><body></body></html>
"""


def _soup(html):
    from pitch_doctor.checks.base import soupify

    return soupify(html)


def test_business_name_prefers_structured_data_over_the_title():
    soup = _soup(_JSONLD_PAGE)
    assert extract_business_name(soup) == "Joe's Plumbing LLC"
    assert extract_city(soup) == "Houston"


def test_business_name_falls_back_to_the_title_lead_segment():
    assert extract_business_name(_soup(_TITLE_ONLY_PAGE)) == "Corner Barber Shop"
    assert extract_city(_soup(_TITLE_ONLY_PAGE)) is None


def test_structured_data_inside_a_graph_is_found():
    soup = _soup(_GRAPH_PAGE)
    assert extract_business_name(soup) == "Graph Motors"
    assert extract_city(soup) == "Katy"


def test_malformed_json_ld_does_not_break_inference():
    assert extract_business_name(_soup(_BROKEN_JSONLD_PAGE)) == "Fallback Bakery"


def test_a_page_with_nothing_to_go_on_yields_no_name():
    assert extract_business_name(_soup("<html><body>hi</body></html>")) is None
