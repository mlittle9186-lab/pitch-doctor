"""Nitro 605 Studios customization layer for Pitch Doctor.

Keeps the upstream scanner intact while turning the hosted web UI into an
internal prospecting console and cleaning client-facing report branding.
"""

from __future__ import annotations

import os
from pathlib import Path

import pitch_doctor.web.app as base
from pitch_doctor.report.builder import BrandInfo as RealBrandInfo
from pitch_doctor.report.builder import write_report as original_write_report

BRAND_NAME = "Nitro 605 Studios"
INTERNAL_EMAIL = "internal@nitro605studios.invalid"
INTERNAL_PHONE = "000-000-0000"
OUT_DIR = Path(os.getenv("PITCH_DOCTOR_OUT", "/app/reports"))


# ----- Internal dashboard copy -------------------------------------------------
base.COPY["en"].update(
    {
        "heading": "Prospect Audit Console",
        "subheading": "Nitro 605 Studios • Internal prospecting tool",
        "placeholder": "Paste a prospect website (or leave blank for no website)",
        "cta": "Run Audit",
        "advanced_label": "Prospect details",
        "email_label": "Internal email",
        "business_name_label": "Business name (required if there is no website)",
        "city_label": "City",
        "brand_name_label": "Report brand",
        "brand_phone_label": "Internal phone",
        "contact_cta": "Nitro 605 Studios • Internal Use",
        "progress_note": "Running website, search, mobile, and conversion checks…",
        "redirecting": "Audit complete. Opening report…",
    }
)

# Preserve the useful business/city/language fields while hiding lead-capture
# fields that are irrelevant in our private prospecting workflow.
base.PAGE = (
    base.PAGE.replace("<title>Pitch Doctor</title>", "<title>Nitro 605 Studios | Prospect Audit</title>")
    .replace("<h1>Pitch Doctor</h1>", "<h1>Nitro 605 Studios</h1>")
    .replace(
        '<div>\n            <label id="email-label"></label>\n            <input type="email" name="email" id="email-input" required>\n          </div>',
        f'<input type="hidden" name="email" id="email-input" value="{INTERNAL_EMAIL}">',
    )
    .replace(
        '<div>\n            <label id="brand-name-label"></label>\n            <input type="text" name="brand_name" id="brand-name-input" required>\n          </div>',
        f'<input type="hidden" name="brand_name" id="brand-name-input" value="{BRAND_NAME}">',
    )
    .replace(
        '<div>\n            <label id="brand-phone-label"></label>\n            <input type="tel" name="brand_phone" id="brand-phone-input" placeholder="xxx-xxx-xxxx" required>\n          </div>',
        f'<input type="hidden" name="brand_phone" id="brand-phone-input" value="{INTERNAL_PHONE}">',
    )
    .replace(
        '<a href="https://zerodigitx.com" class="contact-cta" id="contact-cta"></a>',
        '<div class="footer-note" id="contact-cta"></div>',
    )
)


# ----- Client-facing report cleanup -------------------------------------------
def nitro_brand_info(*_args, **_kwargs) -> RealBrandInfo:
    """Force consistent public branding and suppress fake internal contact data."""
    return RealBrandInfo(name=BRAND_NAME, email=None, phone=None)


def nitro_write_report(*args, **kwargs):
    """Generate upstream report, then remove legacy branding and risky claims."""
    path = original_write_report(*args, **kwargs)
    html = path.read_text(encoding="utf-8")

    replacements = {
        "Zero Digit X - Mario Alvarez": BRAND_NAME,
        "Zero Digit X": BRAND_NAME,
        "Mario Alvarez": BRAND_NAME,
        "Talk to Mario": "Nitro 605 Studios",
        "https://zerodigitx.com/contact": "#",
        "https://zerodigitx.com": "#",
        "You're at risk for GDPR fines (up to €20M) and legal action.": (
            "Privacy and cookie requirements vary by location and business type. "
            "These items are worth reviewing for compliance and visitor trust."
        ),
        "Your site is accessible to people with disabilities and complies with WCAG 2.1 standards.": (
            "This automated scan found several positive accessibility signals. "
            "A full WCAG 2.1 conformance review requires additional manual testing."
        ),
        "Turn any bad website into your next client.": "Digital Presence Audit",
    }
    for old, new in replacements.items():
        html = html.replace(old, new)

    path.write_text(html, encoding="utf-8")
    return path


base.BrandInfo = nitro_brand_info
base.write_report = nitro_write_report

# ASGI application used by Render/uvicorn.
app = base.create_app(OUT_DIR)
