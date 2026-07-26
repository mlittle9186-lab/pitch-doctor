# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **The website is now optional.** `pitch-doctor scan` accepts
  `--business-name` and `--city` instead of a URL, so a business with no
  website -- usually the most valuable prospect -- can be audited. The 16
  website checks are then reported as *not applicable* at critical severity,
  keeping their full deduction (a business with no site has forfeited those
  points, not passed them) and collapsing into one report section instead of 16
  near-identical finding pages. `pitch-doctor scan https://example.com` and
  `batch` are unchanged.
- When a URL *is* given, the business name and city are inferred from the page's
  `LocalBusiness` JSON-LD, `og:site_name`, or `<title>`; anything passed
  explicitly wins.
- **Google Business Profile check** (`checks/google_business.py`): profile
  existence, category, published hours, photo count, review count and average
  rating, via the Google Places API (New). Uses field masking and a SQLite
  cache with a 30-day TTL to keep lookups cheap. Needs
  `GOOGLE_PLACES_API_KEY`; without it -- or on any API failure -- it reports an
  explicit unverified state that costs points but is never presented as a
  finding against the business, and never drives a recommendation. Owner
  replies to reviews are reported as a known blind spot: the Places API exposes
  no such field at any tier.
- **Social presence check** (`checks/social_presence.py`): Facebook/Instagram
  profiles linked from the site, probed anonymously. Nothing authenticates or
  scrapes past a login wall, so unconfirmable profiles are reported as
  *unverified* rather than as failures, and the worst outcome is a warning.
- Report CTA now maps findings to a starting point in a diagnostic tone: no
  website → Basic ($500), missing or thin Google listing → Growth, contact
  friction on an existing site → Professional ($1,000). All copy lives in
  `i18n/` so it can be edited without touching code.
- Web UI: the form requires the visitor's email before starting a scan and
  records the lead (email, business name, city, URL, score, timestamp) in
  `leads.db`. Web-layer only -- the scan engine never sees an email address and
  the CLI contract is untouched. Nothing is emailed yet.

### Changed
- Scoring gains two entries in the same deduction table: Google Business
  Profile at -12/-6 (Tier 1: for a local business the listing is often the only
  thing a nearby customer sees) and social presence at -4/-2 (lowest weight of
  all -- least verifiable, least consequential). All 18 checks at critical now
  sum to 145; the score still floors at 0.
- New i18n keys ship with complete **en** and **es**. `fr` and `zh` carry the
  English text as a placeholder so every language keeps an identical key set;
  translating them is open work.

### Fixed
- **Load speed measurement was reporting misleadingly high times.** It waited
  for the browser's full `load` event (which blocks on every slow
  third-party script, ad, or tracker) under an aggressive "Slow 4G" CDP
  throttle -- producing numbers far worse than what a real visitor on a
  normal connection experiences. Now measures First Contentful Paint (time
  until visible content appears) on a more realistic mid-range mobile
  throttle profile, and the report copy is explicit about the methodology.

### Added
- `pitch-doctor serve`: an optional local reactive web UI (`pip install -e
  ".[web]"`) -- paste a URL, watch live scan progress, get redirected to the
  finished report. Same scan engine as the CLI.
- French and Chinese report/CLI languages (`--lang fr|zh`), alongside
  English and Spanish -- all four fully externalized to `i18n/*.json`.

## [0.1.0] - 2026-07-07

### Added
- Initial release of `pitch-doctor`.
- `scan` and `batch` CLI commands built with Typer + Rich.
- 8 V1 checks: load speed, SSL/HTTPS, mobile rendering, outdated signals,
  broken links, contact friction, search visibility basics, and
  reachability/uptime.
- Health score formula (0-100) with A-F letter grades.
- Client-ready branded report generation: self-contained HTML by default,
  optional PDF via headless Chromium (`--pdf`).
- English and Spanish report/CLI copy (`--lang en|es`), fully externalized
  to `i18n/en.json` and `i18n/es.json`.
- Unit test suite (offline, fixture-based) for scoring and every check.
- GitHub Actions CI (ruff + pytest).
