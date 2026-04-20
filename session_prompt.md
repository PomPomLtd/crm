# Session: Build the Pom Pom cold-outreach mailer

## What we're building

A system to send B2B cold-outreach emails to the ~10,000–15,000 Swiss clinics
we've scraped contact data for. Requirements:

1. **Postmark** is the sending provider.
2. **Open tracking** (Postmark's native "open tracking" feature — we care about
   who opened, not just aggregates).
3. **Three templates — A, B, C — for A/B/C split testing.** Each recipient
   gets exactly one; we need to measure open-rate by variant.
4. **Batch sending** with a sane rate cap.
5. **Segmentation** at send time: filter recipients by **canton**, **clinic
   section** (medicalCenters / clinics / groupPractices / medClinics / hospitals),
   **Fachgebiet (profession / specialty)**, and whether the clinic has a referral
   section.
6. **Resumable** and **stop-safe** — this is meaningful outbound volume.
7. **Compliant** with Swiss UWG Art. 3(1)(o) — every email must have a working
   unsubscribe link + clear sender ID. Honour opt-outs.

## Tech decision — up to you, but here's my read

The previous in-tree Craft plugin (`_meditransfer-mailer`, a CP mailer) was
deliberately removed for a clean rebuild. The user explicitly said "write a
custom app OR use Craft — whatever you think makes the most sense" and asked
me to check Craft plugin docs before recommending.

### Options I vetted

**A. [craftcms/campaign (Putyourlightson)](https://putyourlightson.com/plugins/campaign)** —
Craft-native mailer plugin. $199 Lite / $299 Pro upfront. Has segmentation
(Pro), Postmark integration with bounce webhooks, open/click tracking. **No
native A/B testing** — you'd create 3 separate campaigns and randomly assign
contacts, which is awkward. Also adds Postmark's unsubscribe link on top of
any you add (double-unsubscribe footer unless you contact Postmark support).

**B. Custom Python app** — lean, reads our CSV + queries Craft DB directly,
talks to Postmark's API. ~500 LOC. Runs in the existing `_scrapers/venv`.
No plugin cost. A/B/C bucket is trivial. Full control over unsubscribe flow.

**C. Listmonk** (open-source self-hosted) — more than we need; deploy + manage.

### My lean: Option B (custom Python app).

Reasons: scraper output is already Python-accessible, A/B/C testing is trivial
to implement vs. hacked around in Campaign, we avoid the $299 licence and
double-unsubscribe footer problem, and the feature set is narrow enough that
a custom build is cheaper to maintain than reconfiguring a plugin. The Craft
DB remains the source of truth for segmentation — we just read it.

**Validate this with the user before writing code.** If they push back toward
Craft, craftcms/campaign is the right answer; don't argue.

## Current state of the world

### What's already done and committed

- **Clinic email scraper** at `_scrapers/clinic_emails/` — just finished an
  overnight run on ~18,046 clinic entries. Projected ~9,800+ unique emails,
  ~4,900 unique priority, plus referral-section characterization (form / PDF /
  DOC / email / fax / page-only). **Read `_scrapers/clinic_emails/README.md`
  first** — it documents the entire data pipeline.
- **Craft CMS 5.9.20** — recently patched (43 CVEs fixed). Healthcare-provider
  entries live in sections 2–6 (`medicalCenters`, `clinics`, `groupPractices`,
  `medClinics`, `hospitals`). Section 1 (`crmDocs`) is solo doctors — the user
  has explicitly excluded that group.
- **No mailer plugin installed.** The previous MediTransfer Mailer was removed.
  `plugins/` is empty.

### Data sources you can use

1. **The scraper CSV** — `_scrapers/results/clinic_emails_<ts>.csv`, one row
   per DB entry with `priority_emails`, `general_emails`, `other_emails`,
   plus referral metadata. Note: many DB entries point to the same URL
   (chain sites) — **dedupe by email address before sending.**
2. **Craft DB, directly via `ddev mysql`** — for segmentation metadata
   (canton, section, profession). The relevant tables: `entries`, `sections`,
   `elements_sites.content` (content is JSON, keys are field-layout-element
   UIDs — see `_scrapers/clinic_emails/entries.py` for the query pattern).
   Fields: canton lives in a specific UID per entry type; profession too.
   Query carefully — the content JSON uses UIDs, not handles. For each
   content value, type can be `"url"`, a plain string (address/canton/profession),
   `true/false` (bool fields like `zuweisung`), etc.

### Project conventions (from `CLAUDE.md`)

- All PHP/Craft commands go through DDEV: `ddev craft …`, `ddev composer …`,
  `ddev mysql …`.
- Python scripts run under `_scrapers/venv` (already set up).
- No AI-attribution in commit messages (user's rule).

## What the new system needs (concrete checklist)

### Functional

- [ ] A target list: dedupe scraper emails, drop bounces/opt-outs, attach
      each to a Craft entry so we have canton/section/profession/referral.
- [ ] Three HTML email templates (A / B / C). User will provide content;
      you provide the rendering + templating mechanism.
- [ ] A "campaign" concept: a set of recipients + template(s) + send schedule
      + UTM tags / variant assignment.
- [ ] Random A/B/C assignment per recipient, recorded alongside the send.
- [ ] Segmentation at send-time by: canton (ZH/BE/GE/…), section (clinics /
      hospitals / …), profession (exact string or contains-match),
      has_referral (bool), email-bucket (priority only? include general?).
- [ ] Batch sender with per-minute cap (Postmark default = 10 req/s
      per server token; safe cap ≈300/minute).
- [ ] Postmark open-tracking enabled on all outbound. Store open events
      either via Postmark webhook or via periodic API polls.
- [ ] Public-URL unsubscribe endpoint returning 200 + recording the opt-out.
      Deduped against future sends forever.
- [ ] List-Unsubscribe + List-Unsubscribe-Post headers for one-click.
- [ ] Bounce webhook handling — hard bounces auto-add to suppression list.
- [ ] Every email contains: sender identification (Pom Pom GmbH address),
      unsubscribe link, plain-text alternative.

### Non-functional

- [ ] Resumable sending — if the process dies mid-batch, resuming does not
      re-send to already-delivered addresses.
- [ ] Dry-run mode that produces rendered previews without sending.
- [ ] A small CLI or admin view for previewing, starting, and monitoring
      a campaign.
- [ ] Per-variant stats: sent / delivered / opened / bounced / unsubscribed.
- [ ] Configuration via env vars (Postmark server token, from-address,
      public base URL for unsubscribe).

### Compliance (Switzerland)

- Swiss **UWG Art. 3(1)(o)** restricts unsolicited bulk email. B2B outreach
  to publicly listed business addresses is defensible IF each email is
  clearly identified + has a working opt-out.
- **nDSG / revFADP** (Sept 2023): processing publicly available business
  contact info for legitimate B2B is permitted.
- Email footer MUST include: Pom Pom GmbH legal address, an unsubscribe
  link, and (ideally) a plain-text sentence explaining why they received it.

## Open questions for the user (ask before building)

1. Where should the Postmark webhook endpoint live? Options:
   - DDEV-exposed PHP route at `https://crm.ddev.site/…` (local-only, needs
     tunnel for Postmark callbacks).
   - Deployed Flask service (Fly.io / Railway / DigitalOcean App — cheap).
   - Cloud function (AWS Lambda / Vercel).
2. Preferred language — **Python** (matches the scrapers) or **Node/TS** or
   **PHP inside Craft**?
3. Does an admin UI matter, or is a CLI + a tiny status page enough for v1?
4. Where should tracking state live? Sqlite file, a Craft DB table, or a
   separate Postgres?
5. Is there a "From" sender address already configured in Postmark, or do
   we need to set that up first (including domain verification — DKIM + SPF)?
6. Campaign cadence: one blast, or time-staggered (say, 500/day)? The latter
   is much safer for deliverability on a fresh sender reputation.

## First 90 minutes of the session

1. Read `_scrapers/clinic_emails/README.md` end-to-end.
2. Skim `CLAUDE.md` for project conventions.
3. Peek at one actual CSV row (`_scrapers/results/clinic_emails_*.csv`) to
   understand the data shape.
4. Ask the user the open questions above. Don't write code until they're
   answered or explicitly deferred.
5. Recommend an architecture. Keep it tight — one or two diagrams in prose.
6. On approval, scaffold: project structure, env vars, Postmark SDK import,
   first "render and print" dry-run command.

## Don'ts

- Don't re-add the MediTransfer Mailer plugin or re-import code from it.
  The user deliberately cleared it for a fresh start.
- Don't commit secrets (Postmark token goes in `.env`, which is gitignored).
- Don't blast a test email to the real scraped list. Test with a user-provided
  "safe-list" first (their own inboxes + colleagues).
- Don't build a web UI before the sending core works. CLI first.

## Useful files to read early

- `CLAUDE.md` — project-level instructions
- `_scrapers/clinic_emails/README.md` — scraper docs (the data you're mailing)
- `_scrapers/clinic_emails/entries.py` — example of reading the Craft DB via
  `ddev mysql` with JSON content extraction
- `/Users/sgis/.claude/CLAUDE.md` — user-level preferences
- Anthropic docs on Postmark API: https://postmarkapp.com/developer

Good luck.
