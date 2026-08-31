"""Nitro 605 Studios customization layer for Pitch Doctor."""
from __future__ import annotations
import os
import re
from pathlib import Path
import pitch_doctor.web.app as base
from pitch_doctor.report.builder import BrandInfo as RealBrandInfo
from pitch_doctor.report.builder import write_report as original_write_report

BRAND_NAME = "Nitro 605 Studios"
INTERNAL_EMAIL = "internal@nitro605studios.invalid"
INTERNAL_PHONE = "000-000-0000"
OUT_DIR = Path(os.getenv("PITCH_DOCTOR_OUT", "/app/reports"))
MANGO = "#F36C21"
MANGO_DIM = "rgba(243,108,33,.18)"
HATCH_BLUE = "#2F6FED"
MIDNIGHT = "#08111f"

base.COPY["en"].update({
    "heading": "Prospect Audit Console",
    "subheading": "Nitro 605 Studios • Internal prospecting tool",
    "placeholder": "Paste a prospect website (or leave blank for no website)",
    "cta": "Run Audit", "advanced_label": "Prospect details",
    "email_label": "Internal email", "business_name_label": "Business name",
    "city_label": "City", "brand_name_label": "Report brand",
    "brand_phone_label": "Internal phone", "contact_cta": "Nitro 605 Studios • Internal Use",
    "progress_note": "Running website, search, mobile, and conversion checks…",
    "redirecting": "Audit complete. Opening report…",
})

# Keep hidden upstream fields/IDs alive so its JS can initialize normally.
base.PAGE = (
    base.PAGE.replace("<title>Pitch Doctor</title>", "<title>Nitro 605 Studios | Prospect Audit</title>")
    .replace("<h1>Pitch Doctor</h1>", "<h1><span class=\"nitro-word\">Nitro</span> <span class=\"blue-word\">605</span> Studios</h1>")
    .replace('<div>\n            <label id="email-label"></label>\n            <input type="email" name="email" id="email-input" required>\n          </div>', f'<div style="display:none"><label id="email-label"></label><input type="email" name="email" id="email-input" value="{INTERNAL_EMAIL}" required></div>')
    .replace('<div>\n            <label id="brand-name-label"></label>\n            <input type="text" name="brand_name" id="brand-name-input" required>\n          </div>', f'<div style="display:none"><label id="brand-name-label"></label><input type="text" name="brand_name" id="brand-name-input" value="{BRAND_NAME}" required></div>')
    .replace('<div>\n            <label id="brand-phone-label"></label>\n            <input type="tel" name="brand_phone" id="brand-phone-input" placeholder="xxx-xxx-xxxx" required>\n          </div>', f'<div style="display:none"><label id="brand-phone-label"></label><input type="tel" name="brand_phone" id="brand-phone-input" value="{INTERNAL_PHONE}" required></div>')
    .replace('<a href="https://zerodigitx.com" class="contact-cta" id="contact-cta"></a>', '<div class="footer-note" id="contact-cta"></div>')
    .replace('<label id="business-name-label"></label>', '<label id="business-name-label">Business name</label>')
    .replace('<input type="text" name="business_name" id="business-name-input">', '<input type="text" name="business_name" id="business-name-input" placeholder="Business name">')
    .replace('<label id="city-label"></label>', '<label id="city-label">City</label>')
    .replace('<input type="text" name="city" id="city-input">', '<input type="text" name="city" id="city-input" placeholder="City">')
    .replace("--emerald: #10b981; --emerald-dim: rgba(16,185,129,.16);", f"--emerald: {MANGO}; --emerald-dim: {MANGO_DIM}; --nitro-blue: {HATCH_BLUE};")
    .replace("background: radial-gradient(circle at 30% 0%, #142238 0%, var(--slate-950) 45%, #060a14 100%);", f"background: radial-gradient(circle at 30% 0%, #182947 0%, {MIDNIGHT} 48%, #040914 100%);")
    .replace("</style>", f"\n.nitro-word{{color:{MANGO}}}.blue-word{{color:{HATCH_BLUE}}}.subheading{{color:{MANGO}}}.search-row{{border-color:rgba(47,111,237,.55)}}.search-row:focus-within{{border-color:{MANGO};box-shadow:0 0 0 3px {MANGO_DIM}}}button{{background:{MANGO};color:#1f0b02}}.stage.done{{color:{MANGO}}}.stage.active .stage-dot{{border-color:{MANGO}}}.stage.active .stage-dot::after{{background:{MANGO}}}.stage.done .stage-dot{{border-color:{HATCH_BLUE};background:{HATCH_BLUE}}}\n</style>")
)

def nitro_brand_info(*_args, **_kwargs) -> RealBrandInfo:
    return RealBrandInfo(name=BRAND_NAME, email=None, phone=None)

def nitro_write_report(*args, **kwargs):
    path = original_write_report(*args, **kwargs)
    html = path.read_text(encoding="utf-8")

    # Nitro voice: direct and useful, but every punch must be defensible.
    replacements = {
        "Zero Digit X - Mario Alvarez": BRAND_NAME,
        "Zero Digit X": BRAND_NAME,
        "Mario Alvarez": BRAND_NAME,
        "Talk to Mario": "Nitro 605 Studios",
        "https://zerodigitx.com/contact": "#",
        "https://zerodigitx.com": "#",
        "Turn any bad website into your next client.": "Digital Presence Audit",
        "are costing you customers right now.": "can weaken visibility, trust, and conversions.",
        "You're at risk for GDPR fines (up to €20M) and legal action.": "Missing privacy, terms, and cookie information can create compliance gaps and weaken visitor trust. Requirements vary by location and business type.",
        "You’re at risk for GDPR fines (up to €20M) and legal action.": "Missing privacy, terms, and cookie information can create compliance gaps and weaken visitor trust. Requirements vary by location and business type.",
        "Your site is accessible to people with disabilities and complies with WCAG 2.1 standards.": "This automated scan found several positive accessibility signals. A full WCAG 2.1 conformance review requires additional manual testing.",
        "Professional ($1,000) -- make contacting and booking you effortless: tap-to-call, a short form, and an obvious next step on every page.": "Priority modernization -- fix the highest-impact visibility, trust, performance, and conversion issues identified in this audit first.",
        "Professional ($1,000) — make contacting and booking you effortless: tap-to-call, a short form, and an obvious next step on every page.": "Priority modernization — fix the highest-impact visibility, trust, performance, and conversion issues identified in this audit first.",
        "Basic ($500)": "Essential fixes",
        "Professional ($1,000)": "Priority modernization",
    }
    for old, new in replacements.items():
        html = html.replace(old, new)

    # Catch wording variants from the upstream i18n/template without depending on punctuation.
    html = re.sub(r"You're at risk for\s*GDPR fines\s*\(up to €20M\)\s*and legal action\.", "Missing privacy, terms, and cookie information can create compliance gaps and weaken visitor trust. Requirements vary by location and business type.", html, flags=re.I)
    html = re.sub(r"You(?:'|’)re at risk for\s*GDPR fines\s*\(up to €20M\)\s*and legal action\.", "Missing privacy, terms, and cookie information can create compliance gaps and weaken visitor trust. Requirements vary by location and business type.", html, flags=re.I)

    # The old CTA combined translated copy + brand name, producing nonsense like
    # 'Nitro 605 Studios at Nitro 605 Studios'. Replace the whole rendered line.
    html = re.sub(r"Nitro 605 Studios\s+at\s+Nitro 605\s*Studios\s+for updating your website", "Ready to fix what this audit found? Nitro 605 Studios can handle the modernization work.", html, flags=re.I)
    html = re.sub(r"Contact\s+Nitro 605 Studios\s+at\s+Nitro 605 Studios[^<]*", "Ready to fix what this audit found? Nitro 605 Studios can handle the modernization work.", html, flags=re.I)

    html = html.replace("--emerald: #10b981;", f"--emerald: {MANGO};")
    html = html.replace("--emerald-dark: #047857;", f"--emerald-dark: {HATCH_BLUE};")
    path.write_text(html, encoding="utf-8")
    return path

base.BrandInfo = nitro_brand_info
base.write_report = nitro_write_report
app = base.create_app(OUT_DIR)
