"""Shared helpers used by more than one check: HTML parsing, business
identity inference, and the uniform "couldn't evaluate this" result.
"""

from __future__ import annotations

import json
import re
from typing import Any

from bs4 import BeautifulSoup

from pitch_doctor.i18n import Strings
from pitch_doctor.models import CheckResult, Severity

YEAR_RE = re.compile(r"(19|20)\d{2}")
PHONE_RE = re.compile(
    r"(\+?\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}"
)
ADDRESS_HINT_RE = re.compile(
    r"\b(street|st\.|avenue|ave\.|road|rd\.|calle|avenida|suite|ste\.|"
    r"boulevard|blvd\.?|p\.?o\.?\s?box)\b",
    re.IGNORECASE,
)


def soupify(html: str) -> BeautifulSoup:
    return BeautifulSoup(html or "", "html.parser")


def footer_text(soup: BeautifulSoup) -> str:
    footer = soup.find("footer")
    if footer is not None:
        return footer.get_text(" ", strip=True)
    # Fallback: some sites use a div with an id/class of "footer" instead of <footer>.
    candidate = soup.find(id=re.compile("footer", re.IGNORECASE))
    if candidate is None:
        candidate = soup.find(class_=re.compile("footer", re.IGNORECASE))
    if candidate is not None:
        return candidate.get_text(" ", strip=True)
    return ""


def latest_year_in_text(text: str) -> int | None:
    years = [int(m.group(0)) for m in YEAR_RE.finditer(text)]
    return max(years) if years else None


def has_viewport_meta(soup: BeautifulSoup) -> bool:
    tag = soup.find("meta", attrs={"name": "viewport"})
    return tag is not None and bool(tag.get("content"))


def has_tappable_phone_link(soup: BeautifulSoup) -> bool:
    return any(
        a.get("href", "").lower().startswith("tel:") for a in soup.find_all("a", href=True)
    )


def find_plain_text_phone(soup: BeautifulSoup) -> bool:
    body_text = soup.get_text(" ", strip=True)
    return bool(PHONE_RE.search(body_text))


def has_email_or_contact_link(soup: BeautifulSoup) -> bool:
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if href.startswith("mailto:") or "contact" in href:
            return True
    return False


def has_address_hint(soup: BeautifulSoup) -> bool:
    text = soup.get_text(" ", strip=True)
    if ADDRESS_HINT_RE.search(text):
        return True
    return soup.find(attrs={"itemtype": re.compile("PostalAddress", re.IGNORECASE)}) is not None


def has_title(soup: BeautifulSoup) -> bool:
    tag = soup.find("title")
    return tag is not None and bool(tag.get_text(strip=True))


def has_meta_description(soup: BeautifulSoup) -> bool:
    tag = soup.find("meta", attrs={"name": "description"})
    return tag is not None and bool(tag.get("content", "").strip())


def has_open_graph(soup: BeautifulSoup) -> bool:
    return soup.find("meta", attrs={"property": re.compile("^og:")}) is not None


def has_favicon(soup: BeautifulSoup) -> bool:
    return soup.find("link", rel=re.compile("icon", re.IGNORECASE)) is not None


def has_local_business_jsonld(soup: BeautifulSoup) -> bool:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if "LocalBusiness" in (script.string or "") or "localbusiness" in (
            script.string or ""
        ).lower():
            return True
    return False


# --------------------------------------------------------------------------
# Business identity: who is this site for?
# --------------------------------------------------------------------------

# Separators sites put between the business name and their tagline in <title>.
_TITLE_SEPARATORS = re.compile(r"\s+[|–—·]\s+|\s+-\s+")

# Any JSON-LD @type that describes an organization we can name.
_ORG_TYPES = ("localbusiness", "organization", "restaurant", "store", "professionalservice")


def _jsonld_nodes(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Every JSON-LD object on the page, flattening @graph and top-level lists.

    Malformed JSON-LD is common in the wild, so a parse failure on one block
    must never take down the scan -- it is simply skipped.
    """
    nodes: list[dict[str, Any]] = []

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            nodes.append(value)
            graph = value.get("@graph")
            if isinstance(graph, list):
                for item in graph:
                    collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text() or ""
        if not raw.strip():
            continue
        try:
            collect(json.loads(raw))
        except (ValueError, TypeError):
            continue
    return nodes


def _is_org_node(node: dict[str, Any]) -> bool:
    node_type = node.get("@type")
    types = node_type if isinstance(node_type, list) else [node_type]
    return any(isinstance(t, str) and t.lower() in _ORG_TYPES for t in types)


def extract_business_name(soup: BeautifulSoup) -> str | None:
    """Best guess at the business name, in descending order of reliability.

    Structured data first (the business told Google this explicitly), then the
    social preview name, then the leading segment of <title> -- which is where
    almost every site puts the business name before its tagline.
    """
    for node in _jsonld_nodes(soup):
        if _is_org_node(node):
            name = node.get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()

    site_name = soup.find("meta", attrs={"property": "og:site_name"})
    if site_name is not None:
        content = (site_name.get("content") or "").strip()
        if content:
            return content

    title_tag = soup.find("title")
    if title_tag is not None:
        title = title_tag.get_text(strip=True)
        if title:
            first = _TITLE_SEPARATORS.split(title)[0].strip()
            if first:
                return first
    return None


def extract_city(soup: BeautifulSoup) -> str | None:
    """City from LocalBusiness structured data, if the site publishes any."""
    for node in _jsonld_nodes(soup):
        address = node.get("address")
        candidates = address if isinstance(address, list) else [address]
        for candidate in candidates:
            if isinstance(candidate, dict):
                locality = candidate.get("addressLocality")
                if isinstance(locality, str) and locality.strip():
                    return locality.strip()
    return None


# --------------------------------------------------------------------------
# Social profiles linked from the site
# --------------------------------------------------------------------------

# Only platforms a local business actually uses to be found by customers.
# Value is the label shown in the report.
SOCIAL_PLATFORMS: dict[str, str] = {
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
}

# Links that live on a platform domain but are not a business profile.
_SOCIAL_NON_PROFILE_PATHS = (
    "/sharer",
    "/share.php",
    "/plugins/",
    "/intent/",
    "/login",
    "/dialog/",
)


def find_social_profile_links(soup: BeautifulSoup) -> dict[str, str]:
    """Map platform label -> first profile URL linked from the page.

    Share buttons and login links point at the same domains as real profiles,
    so they are filtered out -- a "Share on Facebook" button is not social
    presence.
    """
    found: dict[str, str] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        lowered = href.lower()
        if not lowered.startswith(("http://", "https://", "//")):
            continue
        if any(part in lowered for part in _SOCIAL_NON_PROFILE_PATHS):
            continue
        for domain, label in SOCIAL_PLATFORMS.items():
            if domain in lowered and label not in found:
                found[label] = href
    return found


# --------------------------------------------------------------------------
# The "we could not evaluate this" result
# --------------------------------------------------------------------------


def not_applicable_result(
    check_id: str, name: str, strings: Strings, *, reason_key: str
) -> CheckResult:
    """A check that had nothing to inspect, reported as the loss that it is.

    A business with no website hasn't "passed" its website checks -- it has
    forfeited them, which is exactly the finding the report needs to lead
    with. So the severity is real (and so is the deduction); only the
    presentation is collapsed. ``reason_key`` names a block under ``report``
    in the i18n files with ``_found``/``_impact``/``_benefit`` suffixes.
    """
    return CheckResult(
        id=check_id,
        name=name,
        severity=Severity.CRITICAL,
        evidence=[strings.get(f"report.{reason_key}_found", check=name)],
        impact=strings.get(f"report.{reason_key}_impact"),
        recommendation=strings.get(f"report.{reason_key}_benefit"),
        not_applicable=True,
    )
