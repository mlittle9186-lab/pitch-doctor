# pitch-doctor

**Turn any bad website into your next client.**

[![License: MIT](https://img.shields.io/badge/license-MIT-10b981.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-10b981.svg)](pyproject.toml)
[![CI](https://github.com/NezbiT/pitch-doctor/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)

`pitch-doctor` is a CLI for web freelancers. Point it at a local business and
it audits that business's whole **digital presence** -- website, Google
Business Profile, and social accounts -- then produces a client-ready,
plain-English report as a polished PDF or standalone HTML file you can send
straight to the owner. No dev jargon. No Lighthouse-dump anxiety. Just "here's
what's costing you customers, and here's what fixing it gets you."

**The website is optional.** A business with no website at all is a valid --
and usually the most valuable -- thing to audit: pass a name and city instead
of a URL and you get a report that leads with the missing site as the single
biggest opportunity, plus everything its Google listing is or isn't doing.

Scan it, brand it with your own name and contact info, send it, close the
deal. Reports render in English, Spanish, French, or Chinese.

## Demo

<!-- TODO: record a short terminal + report walkthrough GIF and drop it here -->
`![pitch-doctor demo](docs/demo.gif)`

## Install

```bash
pip install -e ".[dev]"
playwright install chromium  # skip this if you already have Google Chrome installed
```

(Published to PyPI as `pitch-doctor` once the first tag ships -- until then,
install from a checkout as above.)

By default pitch-doctor drives your system-installed Google Chrome
(Playwright's `channel="chrome"`) instead of downloading its own ~150 MB
Chromium bundle. If Chrome isn't installed, run `playwright install chromium`
and change `channel="chrome"` to plain `pw.chromium.launch()` in
`checks/runner.py` and `report/builder.py`.

## Usage

Scan a single site:

```bash
pitch-doctor scan https://example.com --lang en --out reports/
```

Audit a business that has **no website** -- name and city instead of a URL:

```bash
pitch-doctor scan --business-name "Joe's Plumbing" --city "Houston" --lang es
```

`--business-name` and `--city` are both required when you omit the URL. When
you *do* pass a URL they're optional: pitch-doctor infers the business name and
city from the page's `LocalBusiness` JSON-LD, `og:site_name`, or `<title>`, and
anything you pass explicitly wins. `--url` also works as a flag if you prefer
it next to the other options.

Scan a list of sites (one URL per line in `urls.txt`), continuing past any
failures, with a summary table at the end:

```bash
pitch-doctor batch urls.txt --lang es --out reports/
```

Brand the report as your own agency's deliverable:

```bash
pitch-doctor scan https://example.com \
  --brand-name "Acme Web Studio" \
  --brand-email hello@acmewebstudio.com \
  --brand-phone "+1 555 010 2020" \
  --brand-logo ./logo.png \
  --pdf
```

### Google Business Profile lookups (optional but recommended)

The Google Business Profile check needs a **Google Places API (New)** key:

```bash
export GOOGLE_PLACES_API_KEY="..."     # PowerShell: $env:GOOGLE_PLACES_API_KEY="..."
```

Get one from the [Google Cloud console](https://console.cloud.google.com/):
create (or pick) a project, enable **Places API (New)** under *APIs & Services →
Library*, then create an API key under *Credentials*. Restrict it to the Places
API. Google's free monthly credit covers a lot of prospecting.

Without the key nothing crashes and nothing is faked -- the check reports an
explicit "could not be verified" state, which costs points (so an unchecked
listing never reads as a clean bill of health) but is never quoted back to the
business as a problem of theirs, and never triggers a recommendation.

Two things keep the bill small:

- **Field masking.** Only the twelve fields the check actually reads are
  requested (`FIELD_MASK` in `integrations/places.py`). Notably `places.reviews`
  is *not* requested: it's the priciest tier and still wouldn't tell us whether
  the owner replied.
- **A SQLite cache with a 30-day TTL**, at `~/.pitch-doctor/places-cache.db`
  (override the directory with `PITCH_DOCTOR_CACHE_DIR`). Re-scanning the same
  town costs nothing inside the TTL.

### Web UI (optional)

Prefer a search bar over a terminal? `pitch-doctor serve` launches a small
local web app -- paste a URL, watch the scan progress live (DNS → fetch →
mobile/desktop capture → links → scoring), and get redirected straight to
the finished report:

```bash
pip install -e ".[web]"
pitch-doctor serve   # http://127.0.0.1:8765
```

It calls the exact same scan engine as the CLI and writes reports to the
same `--out` directory -- there's no separate code path to keep in sync. Leave
the URL box empty and fill in the business name and city to audit a business
with no website, exactly as on the CLI.

**Lead capture.** The web form requires the visitor's email before it will
start a scan, and records the lead -- email, business name, city, URL, score,
timestamp -- in `leads.db` (SQLite) next to the reports. Nothing is emailed;
leads are only stored. This lives entirely in the web layer: the scan engine
never sees an email address, and the CLI is unchanged. Query it with any
SQLite client:

```bash
sqlite3 reports/leads.db "SELECT created_at, email, business_name, score FROM leads;"
```

### Flags

| Flag | Default | Description |
|---|---|---|
| `--url` | _(none)_ | Website to audit. Also accepted positionally. Omit it to audit a business with no website |
| `--business-name` | _(inferred)_ | Business name. Required when no URL is given |
| `--city` | _(inferred)_ | City. Required when no URL is given |
| `--lang` | `en` | Report/CLI language: `en`, `es`, `fr`, or `zh` |
| `--out` | `reports/` | Output directory |
| `--brand-name` | `Your Agency` | Name shown on the report cover and CTA |
| `--brand-email` | _(none)_ | Contact email on the final CTA page |
| `--brand-phone` | _(none)_ | Contact phone on the final CTA page |
| `--brand-logo` | _(none)_ | Path to a logo image for the cover |
| `--json` | off | Also dump raw findings as JSON next to the report |
| `--timeout` | `20` | Per-site timeout, in seconds |
| `--pdf` | off | Also render a PDF (via headless Chromium) alongside the HTML report |

### Sample report

<!-- TODO: replace with an actual screenshot of examples/example.com.html once you have one you like -->
`![sample report cover](docs/sample-report-cover.png)`

A generated example lives in [`examples/`](examples/) after you run the scan
described below.

## The checks

Each check returns a severity (`critical` / `warning` / `ok`), the evidence
that led to it, and a business-language explanation of why it matters. They
run in the order below, which is also roughly their order of importance to
the business.

**Reach and trust**

1. **Reachability / uptime** -- DNS resolution, response status, redirect chain length, www/non-www consistency.
2. **SSL / HTTPS** -- missing HTTPS or an invalid certificate.
3. **Security headers** -- `X-Frame-Options`, `X-Content-Type-Options`, CSP, HSTS.
4. **Load speed** -- time until visible content appears (First Contentful Paint), measured via Playwright on a simulated mid-range mobile connection. We deliberately measure *perceived* load time, not the browser's full `load` event -- the latter blocks on every slow third-party script/ad/tracker and can report numbers far worse than what a real visitor actually experiences.
5. **Mobile rendering** -- viewport meta tag, horizontal overflow, and side-by-side phone + desktop screenshots.
6. **Mobile UX (advanced)** -- responsive images (`srcset`), mobile navigation, tappable `tel:` numbers, viewport handling on notched devices.

**Findability and usability**

7. **Outdated signals** -- stale copyright year in the footer.
8. **Broken links** -- up to 25 internal links checked concurrently for 404s.
9. **Contact friction** -- phone numbers not wrapped in `tel:` links, missing email/contact link, missing address.
10. **Search visibility basics** -- title, meta description, Open Graph tags, favicon, `LocalBusiness` JSON-LD.
11. **SEO (advanced)** -- Open Graph completeness, Schema.org JSON-LD, canonical tags, `robots` meta.
12. **Accessibility (WCAG 2.1)** -- image alt text, heading structure, form labels, semantic navigation.
13. **Legal compliance** -- privacy policy, terms of service, cookie notice, a way to make a data request.

**Conversion and measurement**

14. **User experience / CTA clarity** -- clear calls to action, trust signals, pricing transparency, form complexity.
15. **Analytics & tracking** -- Google Analytics, GTM, Facebook Pixel, event tracking, UTM handling.
16. **Performance optimization details** -- gzip/Brotli compression, cache headers, lazy loading, WebP, third-party script count.

**Presence beyond the website** -- the two checks that still have real work to
do when there's no site at all:

17. **Google Business Profile** -- whether a profile exists at all, plus category, published hours, photo count, review count and average rating. Needs `GOOGLE_PLACES_API_KEY` (see above); reports an explicit unverified state without it.
18. **Social media presence** -- Facebook/Instagram profiles linked from the site, and whether those links resolve for a logged-out visitor.

Check 18 is deliberately modest. Both platforms hide real profile data behind a
login, and pitch-doctor never authenticates or scrapes past a login wall -- so
anything it can't confirm anonymously is reported as *unverified*, not as a
failure. That's also why its worst outcome is a warning: for a plumber whose
customers find them on Google, social is the least of it.

> **Owner replies to reviews are not available.** The Places API exposes no
> owner-response field at any pricing tier, so "reviews the owner never
> answered" is reported as a known blind spot rather than guessed at.

> **Translation status.** Checks 3, 6, and 11-16 emit English-only copy
> (hardcoded in their modules). Checks 17-18 are fully externalized to
> `i18n/*.json` with complete **en + es**; `fr` and `zh` currently carry the
> English text as a placeholder, so their key sets stay in sync. `--lang` fully
> translates the report chrome and the original eight checks. Finishing the
> `fr`/`zh` copy is open work.

## The health score

Every check starts from a perfect site (100 points) and loses points based on
its severity. The formula is intentionally simple enough to reconstruct by
hand from the report:

```
score = max(0, 100 - sum(deduction(check) for check in checks))
```

| Check | Critical | Warning |
|---|---|---|
| Load speed | -15 | -8 |
| SSL / HTTPS | -15 | -8 |
| Reachability / uptime | -12 | -6 |
| Mobile rendering | -12 | -6 |
| **Google Business Profile** | **-12** | **-6** |
| Security headers | -8 | -4 |
| Broken links | -8 | -4 |
| Contact friction | -8 | -4 |
| Search visibility basics | -8 | -4 |
| Accessibility | -7 | -3 |
| SEO (advanced) | -6 | -3 |
| Legal compliance | -6 | -3 |
| Outdated signals | -5 | -3 |
| Mobile UX (advanced) | -5 | -3 |
| User experience / CTA | -5 | -3 |
| Performance optimization | -5 | -3 |
| Analytics & tracking | -4 | -2 |
| **Social presence** | **-4** | **-2** |

The weights are front-loaded on purpose: the top five checks alone cost 66
points, so a business that's slow, insecure, unreachable, broken on phones and
invisible on Google grades **F** no matter how it does elsewhere. Google
Business Profile sits in that top tier because for a local business the listing
is frequently the only thing a nearby customer sees. Social presence is
weighted lowest of all -- it's the check we can verify least and the one that
matters least. All 18 at critical sum to 145 -- more than 100 -- so the score
floors at 0 rather than going negative.

An `ok` result always costs 0. Letter grades: **A** 90-100, **B** 80-89,
**C** 70-79, **D** 60-69, **F** below 60. See `pitch_doctor/scoring.py` for
the implementation.

### Scoring a business with no website

The 16 website checks are still reported -- as *not applicable*, at critical
severity. They keep their full deduction (a business with no website hasn't
passed those checks, it has forfeited them), so a websiteless business always
scores **0/F**. Those 16 checks alone sum to 129, past the floor on their own.

In the report they collapse into a single "No website to check" section instead
of 16 near-identical finding pages, and the two presence checks still get full
cards of their own. Feeding the website checks an empty page instead would
produce findings like "no meta description" about a site that doesn't exist.

## Why HTML by default, and PDF on demand

Every report is generated as a single self-contained HTML file first
(screenshots and any logo are embedded as base64 data URIs -- no external
assets, opens offline, emails cleanly as an attachment). PDF is a second step,
and there are two routes to it depending on where you are:

- **CLI (`--pdf`)** -- renders that same HTML with the headless Chromium
  instance Playwright already ships with (`page.pdf()`). No extra system
  dependencies, since Playwright is a hard requirement anyway.
- **Web UI ("Download as PDF" button, or Ctrl/Cmd+S)** -- posts to
  `/reports/{filename}/generate-pdf`, which converts the HTML with
  **WeasyPrint** and serves the result from `/pdf/{filename}`. WeasyPrint is
  an optional dependency of the `[web]` extra; if it isn't importable the
  endpoint returns an error and the button degrades to a no-op rather than
  breaking the page.

WeasyPrint is kept out of the CLI path deliberately: it depends on native
GTK/Pango libraries that are awkward to install on Windows, and the CLI must
work on a bare checkout. On Debian/Ubuntu hosts, the button needs those
libraries present:

```bash
apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libffi8
```

## Deploy the web UI (free)

This is a **single Python service** (FastAPI UI + scan engine + Playwright).
There is no separate static frontend — **Vercel is not a good fit** (serverless
timeouts, no long-lived Chromium).

Recommended free host: **[Render](https://render.com)** (Docker web service).

1. Push this repo to GitHub.
2. In Render: **New → Blueprint** (uses `render.yaml`) or **New → Web Service**
   with Docker runtime.
3. After deploy, attach a custom domain (e.g. `test.mariosalvarez.com`):
   - Render → service → **Settings → Custom Domains**
   - At your DNS: CNAME `test` → the hostname Render gives you
     (e.g. `pitch-doctor.onrender.com`).

Environment variables used in production:

| Variable | Value | Purpose |
|---|---|---|
| `PLAYWRIGHT_CHANNEL` | `chromium` | Use Playwright's bundled browser (not system Chrome) |
| `PLAYWRIGHT_NO_SANDBOX` | `1` | Required inside most containers |
| `PORT` | set by host | Listen port |
| `GOOGLE_PLACES_API_KEY` | your key | Enables the Google Business Profile check. Without it that check reports "unverified" |
| `PITCH_DOCTOR_CACHE_DIR` | a writable path | Where the Places TTL cache lives. Point it at a persistent disk so the cache survives restarts |

On an ephemeral filesystem (Render's free tier included) both the Places cache
and `leads.db` are lost on redeploy -- attach a persistent disk and point
`PITCH_DOCTOR_CACHE_DIR` and `--out` at it if either matters to you.

Local Docker:

```bash
docker build -t pitch-doctor .
docker run --rm -p 8765:8765 pitch-doctor
# open http://localhost:8765
```

**Free-tier caveats:** cold starts after idle, and 512 MB RAM can OOM on heavy
scans — upgrade the plan if Chromium is killed.

Alternatives (also free/credit-based, Docker-friendly): [Fly.io](https://fly.io),
[Railway](https://railway.app), [Koyeb](https://www.koyeb.com).

## Project layout

```
pitch_doctor/
  cli.py                Typer app: scan / batch / serve
  models.py             CheckResult, GbpProfile, ScanContext, ScanReport
  scoring.py            Health score formula
  checks/               One module per check (pure decision logic) + runner.py (I/O)
  integrations/         places.py -- Google Places client, field masking + TTL cache
  report/               Jinja2 template + HTML/PDF builder
  web/                  FastAPI search UI wrapping the same scan engine
    leads.py            Lead capture (web-only; the engine never sees an email)
  i18n/                 en/es/fr/zh -- all report and CLI copy
tests/                  Offline unit tests with static HTML fixtures and mocks
```

All network I/O lives in exactly two places -- `checks/runner.py` and
`integrations/` -- which is what keeps every check's decision logic pure and
testable offline.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: `ruff check .` and
`pytest` must both pass before opening a PR, and check logic must stay
network-free and unit-testable.

## License

MIT -- see [LICENSE](LICENSE).

---

## Español: inicio rápido

`pitch-doctor` es una CLI para freelancers web: analiza la presencia digital
completa de un negocio local -sitio web, ficha de Google Business y redes
sociales- y genera un reporte de auditoría listo para el cliente, en lenguaje
de negocio (no de programador), como PDF o HTML.

**Instalación:**

```bash
pip install -e ".[dev]"
playwright install chromium
```

**Analizar un sitio:**

```bash
pitch-doctor scan https://ejemplo.com --lang es --out reportes/
```

**Analizar un negocio sin sitio web** (el cliente ideal): pasa el nombre y la
ciudad en lugar de una URL. Los 16 chequeos del sitio se reportan como no
aplicables en severidad crítica -no como aprobados- así que el reporte abre con
la ausencia del sitio como la mayor oportunidad perdida:

```bash
pitch-doctor scan --business-name "Plomería Joe" --city "Houston" --lang es
```

**Ficha de Google Business:** requiere la variable de entorno
`GOOGLE_PLACES_API_KEY` (Places API New). Sin ella el chequeo reporta
explícitamente que no se pudo verificar, en lugar de fingir un resultado.

**Analizar una lista de sitios** (un URL por línea en `urls.txt`, continúa
aunque algunos fallen, con una tabla resumen al final):

```bash
pitch-doctor batch urls.txt --lang es --out reportes/
```

Usa `--brand-name`, `--brand-email`, `--brand-phone` y `--brand-logo` para
poner tu propia marca en el reporte, y `--pdf` para generar también un PDF.
