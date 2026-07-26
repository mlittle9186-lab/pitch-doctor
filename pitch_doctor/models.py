"""Shared data types used across checks, scoring, and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Severity(StrEnum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class CheckResult:
    """The uniform output every check module produces.

    ``id`` must match a key under ``checks`` in the i18n string files.
    ``impact`` and ``name`` are already-localized, ready-to-render strings.

    ``not_applicable`` marks a check that could not be evaluated at all
    because the thing it inspects doesn't exist -- today that means every
    website check when the business has no website. Such a result still
    carries a real severity (and therefore a real deduction), it is just
    rendered compactly instead of as a full finding page.
    """

    id: str
    name: str
    severity: Severity
    evidence: list[str]
    impact: str
    recommendation: str
    screenshots: list[str] = field(default_factory=list)
    not_applicable: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "severity": self.severity.value,
            "evidence": self.evidence,
            "impact": self.impact,
            "recommendation": self.recommendation,
            "screenshots": self.screenshots,
            "not_applicable": self.not_applicable,
        }


@dataclass
class GbpProfile:
    """What we could learn about a business's Google Business Profile.

    ``found`` false with ``error`` set means the lookup itself failed (no API
    key, quota, network) -- a degraded state the check reports honestly rather
    than as a missing profile. ``found`` false with no ``error`` means the
    lookup worked and genuinely matched nothing.

    ``reviews_without_reply`` is ``None`` whenever owner replies aren't
    available: the Places API does not expose them at any tier today.
    """

    found: bool = False
    place_id: str | None = None
    name: str | None = None
    formatted_address: str | None = None
    primary_type: str | None = None
    business_status: str | None = None
    has_hours: bool = False
    photo_count: int = 0
    rating: float | None = None
    review_count: int = 0
    reviews_without_reply: int | None = None
    website_uri: str | None = None
    phone: str | None = None
    error: str | None = None
    from_cache: bool = False


@dataclass
class ScanContext:
    """Raw data gathered once per site and shared by every check.

    Keeping network/browser I/O here (and out of the check modules) is what
    lets check *decision logic* be unit tested with static HTML fixtures and
    no live network access.
    """

    url: str
    final_url: str
    html: str
    status_code: int | None
    redirect_chain: list[str]
    headers: dict[str, str]
    load_time_seconds: float | None
    has_valid_ssl: bool
    ssl_error: str | None
    mobile_screenshot_b64: str | None
    desktop_screenshot_b64: str | None
    mobile_overflow_px: int | None
    viewport_meta_present: bool
    internal_links: list[str]
    broken_links: list[tuple[str, int | str]]
    dns_resolves: bool
    www_mismatch: bool = False
    timeout_seconds: float = 20.0
    error: str | None = None

    # Business identity. Supplied by the caller, or inferred from the page's
    # LocalBusiness JSON-LD / og:site_name / <title> when only a URL is given.
    business_name: str | None = None
    city: str | None = None

    # False when the scan was started from a business name alone. Every
    # website check is then reported as not applicable instead of being fed
    # empty HTML, which would produce a page of misleading findings.
    has_website: bool = True

    # Presence data that lives outside the website itself.
    gbp: GbpProfile | None = None
    social_probes: dict[str, str] = field(default_factory=dict)


@dataclass
class ScanReport:
    url: str | None
    lang: str
    checks: list[CheckResult]
    score: int
    grade: str
    mobile_screenshot_b64: str | None = None
    desktop_screenshot_b64: str | None = None
    scanned_at: str = ""
    error: str | None = None
    business_name: str | None = None
    city: str | None = None
    has_website: bool = True

    @property
    def display_name(self) -> str:
        """What to title the report with: the business, falling back to the URL."""
        if self.business_name and self.city:
            return f"{self.business_name} - {self.city}"
        return self.business_name or self.url or ""
