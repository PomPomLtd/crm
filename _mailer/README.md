# _mailer — Pom Pom cold-outreach mailer

Custom Python app that sends the **MediTransfer** cold-outreach campaign
(~10–15k Swiss clinics, three-way A/B/C split) via Postmark, tracks opens
+ clicks + conversions, and serves a small dashboard.

Entry point: `send_mailer.py` (wraps `mailer.cli:main`), matching the
`find_clinic_emails.py` shim pattern.

- **Live deployment:** https://meditransfer-mailer.fly.dev (single Fly machine in `fra`)
- **Dashboard:** https://meditransfer-mailer.fly.dev/dashboard (HTTP Basic Auth)
- **Canvas (template preview):** https://meditransfer-mailer.fly.dev/canvas (same auth)
- **Conversion API contract:** see [`CONVERSION_API.md`](./CONVERSION_API.md) for the meditransfer.ch handoff

## Operations on Fly

The CLI runs **inside** the Fly machine so it shares the same SQLite DB on
the mounted volume. Local CLI runs are for development against an empty DB.

```bash
# Wake the machine + open a shell
fly ssh console --app meditransfer-mailer

# Inside the container — these all use /data/mailer.db on the volume:
python send_mailer.py campaign list
python send_mailer.py targets build --sections clinics,hospitals --has-referral yes -o /data/recipients.csv
python send_mailer.py campaign create --name cold-2026-04 --recipients /data/recipients.csv
python send_mailer.py send --campaign cold-2026-04 --limit 5             # dry-run
python send_mailer.py send --campaign cold-2026-04 --limit 500 --live    # real
python send_mailer.py stats --campaign cold-2026-04
python send_mailer.py opt-outs list
```

Inline test recipients (no CSV needed):
```
python send_mailer.py campaign create --name test-07 --emails a@x.ch,b@x.ch,c@x.ch
```

After a dry-run the recipients have `dry_run` rows in `sends`, blocking
the live send. Clear them with:
```
sqlite3 /data/mailer.db "DELETE FROM sends WHERE status='dry_run' AND campaign_id=(SELECT id FROM campaigns WHERE name='test-07');"
```

## Local development

```bash
# Deps go into the existing scraper venv (no new venv).
_scrapers/venv/bin/python -m pip install -r _mailer/requirements.txt

# Copy .env.example → .env and fill it in.
cp _mailer/.env.example _mailer/.env && $EDITOR _mailer/.env

# Run the test suite.
cd _mailer && ../_scrapers/venv/bin/python -m pytest tests/ -v   # 55 tests

# Render a preview locally.
../_scrapers/venv/bin/python send_mailer.py render --campaign foo --variant A --format html > preview.html

# Run the Flask app locally.
../_scrapers/venv/bin/python send_mailer.py webhook --port 8080
# → http://localhost:8080/canvas
```

For prod sends, **always** use the Fly machine. Local CLI writes to a
local `state/mailer.db` which is not the source of truth.

## Templates

Four Postmark-safe HTML designs in `mailer/templates/`:

| Stem | Style | Recommended role |
|---|---|---|
| `01-der-brief` | Founder letter, plain-text feel, minimal graphics | **Cold send** (default A) |
| `02-hero-cta` | Blue gradient hero + 3 bullets + VML CTA button | Brand awareness (default B) |
| `03-stunden-zu-minuten` | Two-column Heute-vs-Meditransfer compare | Benefits-forward (default C) |
| `04-bento-benefits` | Four-card bento grid, highest visual weight | Re-engagement / send #3 |

Each stem has a matching `.txt` plain-text alternative (deliverability requires it).

**Per-render injections:**
- `{{ unsubscribe_url }}` — signed per-recipient token resolving to `/unsubscribe`
- `{{ cta_url }}` — `https://meditransfer.ch/?code=WELCOME30` decorated with
  `utm_source=meditransfer-mailer&utm_medium=email&utm_campaign={name}&utm_content={template}`

The unsubscribe `<a>` tag carries `data-postmark-track="false"` so Postmark
won't rewrite it through its click-tracking redirector — recipients see
the raw signed URL on hover.

The designs were handed off from Claude Design — `https://api.anthropic.com/v1/design/h/5shmKrUWoFvo8iu8Az3pXQ`.

## HTTP routes

| Path | Auth | Purpose |
|---|---|---|
| `GET /` | public | health check |
| `GET /unsubscribe?t=…` | signed token | landing page with one-click confirm |
| `POST /unsubscribe` | signed token | One-Click List-Unsubscribe-Post target |
| `POST /webhook/postmark` | optional `X-Postmark-Token` header | open / bounce / spam / subscription events |
| `POST /api/conversion` | `X-Conversion-Token` header | receives conversion events from meditransfer.ch (see CONVERSION_API.md) |
| `GET /dashboard` | HTTP Basic | campaign list with per-variant aggregate stats |
| `GET /dashboard/c/<id>` | HTTP Basic | per-campaign drilldown (variant cards, conversions, top links, per-recipient table) |
| `GET /canvas` | HTTP Basic | side-by-side preview of all 4 templates (design tool) |
| `GET /canvas/preview/<stem>` | HTTP Basic | single template render against a fake recipient |

If `MAILER_DASHBOARD_USER`/`_PASS` aren't configured, the dashboard +
canvas routes return `404` (no info leak about their existence).

## Compliance (Switzerland)

Every rendered email contains, via the shared design system:

- **Sender identification**: Pom Pom GmbH · Kalkbreitestrasse 6 · 8003 Zürich · hello@meditransfer.ch
- **Unsubscribe link**: signed token resolving to `/unsubscribe` on the deployed webhook host
- **List-Unsubscribe + List-Unsubscribe-Post** headers for one-click mail-client unsubscribe
- **Why you received this** footer line
- **Plain-text alternative** (required by UWG-defensible cold-outreach practice)

UWG Art. 3(1)(o) + revFADP: publicly listed business contact info,
single-touch outreach, working opt-out, clear sender. Every opt-out is
recorded in `opt_outs` and filtered on every subsequent send.

## Architecture

```
send_mailer.py                    # entry shim
  → mailer.cli.main()             # argparse, subcommands
      → mailer.config              # env loading
      → mailer.targets             # checkpoint JSONL → recipients CSV
      → mailer.db                  # SQLite schema + helpers
      → mailer.bucket              # deterministic SHA-256 A/B/C assignment
      → mailer.tokens              # signed URL-safe tokens (itsdangerous)
      → mailer.render              # Jinja2 + per-recipient unsubscribe + UTM CTA
      → mailer.sender              # Postmark batch send, resumable, rate-capped
      → mailer.webhook             # Flask: opt-out, webhooks, dashboard, /api/conversion
```

### State tables (SQLite, single file at `/data/mailer.db` on Fly)

- `campaigns` — one row per campaign (name, subjects, template stems)
- `recipients` — per-campaign, unique by (campaign_id, email), holds variant
- `sends` — unique by recipient_id; resume skips anything already here
- `opens` — one row per Postmark open event
- `clicks` — one row per Postmark click event (link tracking on, HTML only)
- `bounces` — bounces + spam complaints
- `opt_outs` — global suppression list (unique by lowercased email)
- `conversions` — events fired from meditransfer.ch via `/api/conversion`

### Resume semantics

`mailer.db.pending_recipients` returns only recipients with **no `sends`
row** AND **no `opt_outs` match**. This means:

1. A crashed run resumes without re-sending.
2. An opt-out recorded mid-run stops future sends to that address.
3. Dry-runs also record rows (status `dry_run`); see Operations to clear.

## Fly deployment

Initial setup (one-time):
```
fly apps create meditransfer-mailer --org personal
fly volumes create mailer_data --region fra --size 1 --yes --app meditransfer-mailer
# Set secrets — POSTMARK_SERVER_TOKEN, MAILER_TOKEN_SECRET, POSTMARK_WEBHOOK_SECRET,
# MAILER_DASHBOARD_USER, MAILER_DASHBOARD_PASS, MAILER_CONVERSION_TOKEN
fly secrets import --app meditransfer-mailer < secrets.env  # then rm secrets.env
fly deploy --remote-only
```

Subsequent deploys:
```
cd _mailer && fly deploy --remote-only
```

The machine is `auto_stop_machines = "stop"` — it idles down when no
traffic; HTTP requests + `fly ssh console` auto-wake it.

## Environment variables

See `.env.example` for the complete list. Required for the CLI to start:

| Var | Purpose |
|---|---|
| `POSTMARK_SERVER_TOKEN` | server token from the MediTransfer Postmark server |
| `POSTMARK_FROM_EMAIL` | `hello@meditransfer.ch` |
| `POSTMARK_FROM_NAME` | `MediTransfer` |
| `POSTMARK_STREAM` | **must** be a **broadcast** stream for bulk outreach |
| `MAILER_BASE_URL` | deployed host (baked into every unsubscribe URL — don't change after a campaign starts sending) |
| `MAILER_TOKEN_SECRET` | signs unsubscribe tokens; rotating it breaks all previously-sent unsubscribe links |

Optional but recommended in production:

| Var | Purpose |
|---|---|
| `POSTMARK_WEBHOOK_SECRET` | Postmark POSTs `X-Postmark-Token: <this>`; if unset, the webhook accepts any POST |
| `MAILER_DASHBOARD_USER` / `MAILER_DASHBOARD_PASS` | Basic Auth on `/dashboard` + `/canvas`; if either is unset, both return 404 |
| `MAILER_CONVERSION_TOKEN` | Required `X-Conversion-Token` on `POST /api/conversion`; if unset, the route returns 404 |
| `MAILER_RATE_PER_MINUTE` | per-minute cap on outbound (default 300; Postmark hard cap is 600/min) |
| `MAILER_DAILY_CAP` | default `--limit` for `send` (default 500/day) |

## Postmark configuration

In Postmark, on the **broadcast** message stream:

1. **Webhooks** → add webhook
   - URL: `https://meditransfer-mailer.fly.dev/webhook/postmark`
   - Events: Delivery, Bounce, Spam Complaint, Open (Only post on first open),
     Link Click, Subscription Change
   - Custom HTTP Header: `X-Postmark-Token` = value of `POSTMARK_WEBHOOK_SECRET`
2. **Settings** → Open Tracking enabled (the API call sets `TrackOpens: true` per message anyway)
3. **Settings** → Link Tracking: HtmlOnly (also set per-message via `TrackLinks: HtmlOnly`)

## Testing

```bash
cd _mailer && ../_scrapers/venv/bin/python -m pytest tests/ -v
```

55 tests covering: A/B/C bucketing (determinism, uniformity, salt), token
sign/verify (roundtrip, tamper-rejection), template rendering (every
template, unsubscribe injection, UTM CTA injection, subject templating),
DB state (opt-out enforcement, resume semantics, stats including
clicks/conversions), targets building (dedup, filtering, bucket rules),
dashboard auth gate (404 when unconfigured, 401 with bad creds, 200 with
right creds), conversion endpoint (token auth, attribution paths, stats
roll-up).

## Things deliberately not done in v1

- No web UI for campaign creation — CLI only. Dashboard is read-only.
- No canton/profession UID map: `targets.py` heuristically extracts canton
  from content JSON strings. If segmentation reliability matters, replace
  `_extract_canton_and_profession` with explicit per-section UID lookups.
- No follow-up sequencing (send #2 / send #3) — design 04 is available
  but needs a new campaign row to use.
- No bounce-rate throttling: if the first 500 have 10% hard bounces, stop
  and investigate before continuing. Watch the dashboard.
- No conversion-event dedupe — the meditransfer.ch caller is responsible
  for idempotency (one POST per state transition per user).
