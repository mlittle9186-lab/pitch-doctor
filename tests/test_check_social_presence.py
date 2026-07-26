from __future__ import annotations

from pitch_doctor.checks import social_presence
from pitch_doctor.checks.social_presence import REACHABLE, UNVERIFIABLE
from pitch_doctor.models import Severity
from tests.conftest import make_context

_WITH_SOCIAL = """
<html><body>
  <a href="https://www.facebook.com/joesplumbing">Facebook</a>
  <a href="https://instagram.com/joesplumbing">Instagram</a>
</body></html>
"""

_SHARE_BUTTONS_ONLY = """
<html><body>
  <a href="https://www.facebook.com/sharer/sharer.php?u=https://joes.test">Share</a>
  <a href="https://www.facebook.com/plugins/like.php">Like us</a>
</body></html>
"""


def test_linked_profiles_are_ok(strings_en):
    ctx = make_context(
        html=_WITH_SOCIAL,
        social_probes={"Facebook": REACHABLE, "Instagram": REACHABLE},
    )
    result = social_presence.evaluate(ctx, strings_en)
    assert result.severity == Severity.OK
    assert "Facebook, Instagram" in result.evidence[0]


def test_no_social_links_is_warning_not_critical(strings_en):
    # Social matters less than Google or the site itself for a local business,
    # so its worst outcome is a warning.
    ctx = make_context(html="<html><body><p>No socials here</p></body></html>")
    result = social_presence.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING


def test_share_buttons_do_not_count_as_presence(strings_en):
    ctx = make_context(html=_SHARE_BUTTONS_ONLY)
    result = social_presence.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING


def test_unverifiable_profiles_are_noted_but_not_penalised(strings_en):
    ctx = make_context(
        html=_WITH_SOCIAL,
        social_probes={"Facebook": UNVERIFIABLE, "Instagram": REACHABLE},
    )
    result = social_presence.evaluate(ctx, strings_en)
    assert result.severity == Severity.OK
    assert any("Facebook" in item and "without logging in" in item for item in result.evidence)


def test_unprobed_profiles_default_to_unverifiable(strings_en):
    ctx = make_context(html=_WITH_SOCIAL, social_probes={})
    result = social_presence.evaluate(ctx, strings_en)
    assert result.severity == Severity.OK
    assert any("without logging in" in item for item in result.evidence)


def test_websiteless_business_says_there_was_nowhere_to_look(strings_en):
    ctx = make_context(html="", has_website=False)
    result = social_presence.evaluate(ctx, strings_en)
    assert result.severity == Severity.WARNING
    assert any("no website" in item for item in result.evidence)


def test_spanish_copy_is_translated(strings_es):
    ctx = make_context(html="")
    result = social_presence.evaluate(ctx, strings_es)
    assert result.name == "Presencia en Redes Sociales"
