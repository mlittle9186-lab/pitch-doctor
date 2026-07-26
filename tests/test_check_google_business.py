from __future__ import annotations

from pitch_doctor.checks import google_business
from pitch_doctor.models import GbpProfile, Severity
from tests.conftest import make_context


def _solid_profile(**overrides) -> GbpProfile:
    defaults = dict(
        found=True,
        place_id="places/abc123",
        name="Joe's Plumbing",
        formatted_address="100 Main St, Houston, TX",
        primary_type="Plumber",
        business_status="OPERATIONAL",
        has_hours=True,
        photo_count=12,
        rating=4.7,
        review_count=64,
    )
    defaults.update(overrides)
    return GbpProfile(**defaults)


def test_complete_profile_is_ok(strings_en):
    ctx = make_context(gbp=_solid_profile())
    result = google_business.evaluate(ctx, strings_en)
    assert result.severity == Severity.OK


def test_no_matching_profile_is_critical(strings_en):
    ctx = make_context(gbp=GbpProfile(found=False))
    result = google_business.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL


def test_profile_without_hours_or_photos_is_warning(strings_en):
    ctx = make_context(gbp=_solid_profile(has_hours=False, photo_count=0))
    result = google_business.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING


def test_profile_without_reviews_is_warning(strings_en):
    ctx = make_context(gbp=_solid_profile(review_count=0, rating=None))
    result = google_business.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING


def test_thin_review_count_is_warning(strings_en):
    ctx = make_context(gbp=_solid_profile(review_count=3))
    result = google_business.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING


def test_low_rating_is_warning(strings_en):
    ctx = make_context(gbp=_solid_profile(rating=3.1))
    result = google_business.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING


def test_permanently_closed_listing_is_critical(strings_en):
    ctx = make_context(gbp=_solid_profile(business_status="CLOSED_PERMANENTLY"))
    result = google_business.evaluate(ctx, strings_en)
    assert result.severity == Severity.CRITICAL


def test_missing_api_key_is_reported_as_unverified_not_ok(strings_en):
    # A missing key is our problem, not the business's -- but it must never
    # read as a clean bill of health either.
    ctx = make_context(gbp=GbpProfile(found=False, error="GOOGLE_PLACES_API_KEY is not set"))
    result = google_business.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING
    assert "GOOGLE_PLACES_API_KEY" in result.evidence[0]
    # Flagged as unevaluated so it never becomes a finding pinned on the business.
    assert result.not_applicable is True


def test_api_failure_is_reported_as_unverified(strings_en):
    ctx = make_context(gbp=GbpProfile(found=False, error="Places API returned 429: quota"))
    result = google_business.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING
    assert "429" in result.evidence[0]


def test_no_lookup_attempted_is_unverified(strings_en):
    ctx = make_context(gbp=None)
    result = google_business.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING


def test_unknown_review_replies_are_flagged_as_a_blind_spot(strings_en):
    # The Places API exposes no owner-reply field, so a profile with reviews
    # must say so rather than implying they all go unanswered.
    ctx = make_context(gbp=_solid_profile(reviews_without_reply=None))
    result = google_business.evaluate(ctx, strings_en)
    assert any("owner responses" in item for item in result.evidence)


def test_spanish_copy_is_translated(strings_es):
    ctx = make_context(gbp=GbpProfile(found=False))
    result = google_business.evaluate(ctx, strings_es)
    assert result.name == "Ficha de Google Business"
    assert "Google" in result.impact
