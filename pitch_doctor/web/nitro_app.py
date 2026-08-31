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

base.COPY["en"].update({"heading":"Prospect Audit Console","subheading":"Nitro 605 Studios • Internal prospecting tool","placeholder":"Paste a prospect website (or leave blank for no website)","cta":"Run Audit","advanced_label":"Prospect details","email_label":"Internal email","business_name_label":"Business name","city_label":"City","brand_name_label":"Report brand","brand_phone_label":"Internal phone","contact_cta":"Nitro 605 Studios • Internal Use","progress_note":"Running website, search, mobile, and conversion checks…","redirecting":"Audit complete. Opening report…"})

base.PAGE = (base.PAGE.replace("<title>Pitch Doctor</title>,","<title>Nitro 605 Studios | Prospect Audit</title>") if False else base.PAGE.replace("<title>Pitch Doctor</title>","<title>Nitro 605 Studios | Prospect Audit</title>"))
base.PAGE = (base.PAGE.replace("<h1>Pitch Doctor</h1>","<h1><span class=\"nitro-word\">Nitro</span> <span class=\"blue-word\">605</span> Studios</h1>")
.replace('<div>\n            <label id="email-label"></label>\n            <input type="email" name="email" id="email-input" required>\n          </div>',f'<div style="display:none"><label id="email-label"></label><input type="email" name="email" id="email-input" value="{INTERNAL_EMAIL}" required></div>')
.replace('<div>\n            <label id="brand-name-label"></label>\n            <input type="text" name="brand_name" id="brand-name-input" required>\n          </div>',f'<div style="display:none"><label id="brand-name-label"></label><input type="text" name="brand_name" id="brand-name-input" value="{BRAND_NAME}" required></div>')
.replace('<div>\n            <label id="brand-phone-label"></label>\n            <input type="tel" name="brand_phone" id="brand-phone-input" placeholder="xxx-xxx-xxxx" required>\n          </div>',f'<div style="display:none"><label id="brand-phone-label"></label><input type="tel" name="brand_phone" id="brand-phone-input" value="{INTERNAL_PHONE}" required></div>')
.replace('<a href="https://zerodigitx.com" class="contact-cta" id="contact-cta"></a>','<div class="footer-note" id="contact-cta"></div>')
.replace('<label id="business-name-label"></label>','<label id="business-name-label">Business name</label>').replace('<input type="text" name="business_name" id="business-name-input">','<input type="text" name="business_name" id="business-name-input" placeholder="Business name">')
.replace('<label id="city-label"></label>','<label id="city-label">City</label>').replace('<input type="text" name="city" id="city-input">','<input type="text" name="city" id="city-input" placeholder="City">')
.replace("--emerald: #10b981; --emerald-dim: rgba(16,185,129,.16);",f"--emerald: {MANGO}; --emerald-dim: {MANGO_DIM}; --nitro-blue: {HATCH_BLUE};")
.replace("background: radial-gradient(circle at 30% 0%, #142238 0%, var(--slate-950) 45%, #060a14 100%);",f"background: radial-gradient(circle at 30% 0%, #182947 0%, {MIDNIGHT} 48%, #040914 100%);")
.replace("</style>",f"\n.nitro-word{{color:{MANGO}}}.blue-word{{color:{HATCH_BLUE}}}.subheading{{color:{MANGO}}}.search-row{{border-color:rgba(47,111,237,.55)}}.search-row:focus-within{{border-color:{MANGO};box-shadow:0 0 0 3px {MANGO_DIM}}}button{{background:{MANGO};color:#1f0b02}}.stage.done{{color:{MANGO}}}.stage.active .stage-dot{{border-color:{MANGO}}}.stage.active .stage-dot::after{{background:{MANGO}}}.stage.done .stage-dot{{border-color:{HATCH_BLUE};background:{HATCH_BLUE}}}\n</style>"))

def nitro_brand_info(*_args,**_kwargs)->RealBrandInfo:
    return RealBrandInfo(name=BRAND_NAME,email=None,phone=None)

def _friendly_issue(name: str) -> str:
    n=name.lower()
    if "security header" in n: return "missing website security protections"
    if "advanced seo" in n or "search visibility" in n: return "weak search metadata and structured data"
    if "mobile load" in n or "performance" in n: return "mobile loading and performance issues"
    if "mobile ux" in n: return "a few mobile usability gaps"
    if "analytics" in n: return "no visitor or conversion tracking"
    if "privacy" in n or "gdpr" in n or "legal" in n: return "missing privacy and policy information"
    if "social" in n: return "a weak connection between the website and social profiles"
    if "contact" in n or "cta" in n: return "friction in how visitors contact the business"
    return name.lower()

def _friendly_positive(name: str) -> str:
    n=name.lower()
    if "reachability" in n or "uptime" in n: return "the site is online and reachable"
    if "ssl" in n or "https" in n: return "the site is protected with HTTPS"
    if "contact" in n: return "your contact information is easy to find"
    if "mobile rendering" in n: return "the site renders properly on mobile"
    if "broken link" in n: return "the scan didn't uncover broken-link problems"
    return name.lower()

def _outreach_text(scan_report) -> str:
    name=scan_report.business_name or "your business"
    bad=[c for c in scan_report.checks if c.severity.value in ("critical","warning")]
    good=[c for c in scan_report.checks if c.severity.value=="ok"]
    positives=[]
    for c in good:
        p=_friendly_positive(c.name)
        if p not in positives: positives.append(p)
        if len(positives)==2: break
    if not positives: positives=["the site is online and reachable"]
    if len(positives)==1: positive_sentence=positives[0]
    else: positive_sentence=positives[0]+", and "+positives[1]
    issues=[]
    for c in bad:
        issue=_friendly_issue(c.name)
        if issue not in issues: issues.append(issue)
        if len(issues)==3: break
    if issues:
        issue_text=", ".join(issues[:-1])+((", and " if len(issues)>2 else " and ")+issues[-1] if len(issues)>1 else issues[0])
        issue_sentence=f"I also found several things worth fixing, including {issue_text}."
    else:
        issue_sentence="I also found a few opportunities to tighten up the site's digital presence."
    return (f"Subject: Quick website audit for {name}\n\nHi,\n\n"
            f"I took a quick look at {name}'s website. A couple things are already working well — {positive_sentence}.\n\n"
            f"{issue_sentence} Those issues can make the site harder to find, slower or less effective for potential customers.\n\n"
            "I put together a short audit showing exactly what I found and what I'd tackle first.\n\n"
            "Nitro 605 Studios can handle the modernization work without turning it into a giant rebuild.\n\n"
            "Interested in seeing what I'd fix first?\n\nNitro 605 Studios")

def nitro_write_report(*args,**kwargs):
    scan_report=args[0] if args else kwargs.get("scan") or kwargs.get("scan_report")
    path=original_write_report(*args,**kwargs); html=path.read_text(encoding="utf-8")
    replacements={"Zero Digit X - Mario Alvarez":BRAND_NAME,"Zero Digit X":BRAND_NAME,"Mario Alvarez":BRAND_NAME,"Talk to Mario":"Nitro 605 Studios","https://zerodigitx.com/contact":"#","https://zerodigitx.com":"#","Turn any bad website into your next client.":"Digital Presence Audit","are costing you customers right now.":"can weaken visibility, trust, and conversions.","GDPR &amp; Legal Compliance":"Privacy &amp; Legal Basics","GDPR & Legal Compliance":"Privacy & Legal Basics"," (GDPR requirement)":""," (GDPR/ePrivacy requirement)":""," (legal protection)":"","Your site lacks 3 critical legal compliance requirements.":"Your site is missing several common privacy and policy disclosures.","You're at risk for GDPR fines (up to €20M) and legal action.":"Privacy and disclosure requirements vary by location and business type; these missing items are worth reviewing for compliance and visitor trust.","You’re at risk for GDPR fines (up to €20M) and legal action.":"Privacy and disclosure requirements vary by location and business type; these missing items are worth reviewing for compliance and visitor trust.","Adding privacy policies, terms, cookie notices, and contact methods protects your business legally and builds visitor trust.":"Clear privacy and policy information can strengthen visitor trust and help address requirements that apply to your business and location.","Your site is accessible to people with disabilities and complies with WCAG 2.1 standards.":"This automated scan found several positive accessibility signals. A full WCAG 2.1 conformance review requires additional manual testing.","Pages are slow, bandwidth-heavy, and fail Core Web Vitals.":"These patterns can add page weight and hurt loading performance, especially on slower connections.","Implementing gzip, caching, lazy loading, and modern image formats makes pages faster, saves bandwidth, and improves SEO rankings.":"Improving caching, lazy loading, compression, and image formats can make pages faster, reduce bandwidth use, and support a better search experience.","Every extra second past 3 quietly costs you visitors.":"Slower first paint can increase abandonment, especially on mobile.","Adding Schema.org structured data, Open Graph tags, and canonical tags improves search rankings, makes social links more attractive, and prevents duplicate content penalties.":"Adding structured data, Open Graph tags, and canonical tags helps search engines understand the site, improves social previews, and identifies the preferred URL for indexing.","GOOGLE_PLACES_API_KEY is not set.":"The listing lookup was unavailable during this scan.","Professional ($1,000) -- make contacting and booking you effortless: tap-to-call, a short form, and an obvious next step on every page.":"Priority modernization -- fix the highest-impact visibility, trust, performance, and conversion issues identified in this audit first.","Professional ($1,000) — make contacting and booking you effortless: tap-to-call, a short form, and an obvious next step on every page.":"Priority modernization — fix the highest-impact visibility, trust, performance, and conversion issues identified in this audit first.","Basic ($500)":"Essential fixes","Professional ($1,000)":"Priority modernization"}
    for old,new in replacements.items(): html=html.replace(old,new)
    html=re.sub(r"You(?:'|’)re at risk for GDPR fines \(up to €20M\) and legal action\.","Privacy and disclosure requirements vary by location and business type; these missing items are worth reviewing for compliance and visitor trust.",html,flags=re.I)
    html=html.replace("disclosures. You Privacy and disclosure requirements","disclosures. Privacy and disclosure requirements")
    html=re.sub(r"Nitro 605 Studios\s+at\s+Nitro 605\s*Studios\s+for updating your website","Ready to fix what this audit found? Nitro 605 Studios can handle the modernization work.",html,flags=re.I)
    html=re.sub(r"Contact\s+Nitro 605 Studios\s+at\s+Nitro 605 Studios[^<]*","Ready to fix what this audit found? Nitro 605 Studios can handle the modernization work.",html,flags=re.I)
    html=html.replace("--emerald: #10b981;",f"--emerald: {MANGO};").replace("--emerald-dark: #047857;",f"--emerald-dark: {HATCH_BLUE};")
    if scan_report is not None:
        import html as html_lib
        outreach=html_lib.escape(_outreach_text(scan_report))
        outreach_ui=f'''<div id="nitro-outreach" style="background:#08111f;padding:30px;max-width:900px;margin:0 auto;color:white;font-family:-apple-system,'Segoe UI',sans-serif"><div style="font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:{MANGO};font-weight:800">Internal Sales Tool</div><h2 style="margin:6px 0 8px">Approved Outreach Draft</h2><p style="color:#cbd5e1;margin-top:0">Generated from this audit. Nothing is sent automatically. Review it, edit it, then copy when you're happy.</p><textarea id="nitro-email" style="width:100%;min-height:330px;background:#0f172a;color:#f8fafc;border:1px solid {HATCH_BLUE};border-radius:10px;padding:16px;font:14px/1.55 monospace">{outreach}</textarea><button onclick="nitroCopyEmail()" style="margin-top:12px;background:{MANGO};border:0;border-radius:8px;padding:12px 22px;font-weight:800;cursor:pointer">Copy Approved Email</button><span id="nitro-copy-status" style="margin-left:12px;color:#cbd5e1"></span></div><script>async function nitroCopyEmail(){{const e=document.getElementById('nitro-email');try{{await navigator.clipboard.writeText(e.value);document.getElementById('nitro-copy-status').textContent='Copied — ready for manual send.';}}catch(_e){{e.select();document.execCommand('copy');document.getElementById('nitro-copy-status').textContent='Copied — ready for manual send.';}}}}</script>'''
        html=html.replace('<div class="report-footer">',outreach_ui+'<div class="report-footer">')
    path.write_text(html,encoding="utf-8"); return path

base.BrandInfo=nitro_brand_info
base.write_report=nitro_write_report
app=base.create_app(OUT_DIR)
