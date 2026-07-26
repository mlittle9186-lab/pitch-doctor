"""One module per check. Each module exposes a pure ``evaluate(ctx, strings)``
function so decision logic can be unit tested against static HTML fixtures with
no live network access. All network/browser I/O lives in ``runner.py``.
"""

from pitch_doctor.checks import (
    accessibility,
    analytics_tracking,
    broken_links,
    compliance,
    contact_friction,
    google_business,
    load_speed,
    mobile_rendering,
    mobile_ux_advanced,
    outdated_signals,
    performance_optimization,
    reachability,
    search_visibility,
    security_headers,
    seo_advanced,
    social_presence,
    ssl_check,
    user_experience,
)

# Checks that inspect the business's own website. When a scan is started from a
# business name alone, these are the ones with nothing left to inspect.
WEBSITE_CHECKS = (
    reachability,
    ssl_check,
    security_headers,
    load_speed,
    mobile_rendering,
    mobile_ux_advanced,
    outdated_signals,
    broken_links,
    contact_friction,
    search_visibility,
    seo_advanced,
    accessibility,
    compliance,
    user_experience,
    analytics_tracking,
    performance_optimization,
)

# Checks that look at presence living outside the website, so they still have
# real work to do for a business that has no site at all.
PRESENCE_CHECKS = (
    google_business,
    social_presence,
)

ALL_CHECKS = WEBSITE_CHECKS + PRESENCE_CHECKS

WEBSITE_CHECK_IDS = frozenset(module.CHECK_ID for module in WEBSITE_CHECKS)

__all__ = ["ALL_CHECKS", "PRESENCE_CHECKS", "WEBSITE_CHECKS", "WEBSITE_CHECK_IDS"]
