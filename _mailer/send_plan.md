# MediTransfer cold-outreach send plan

Living document. Update as sends go out. All volumes are from the Fly-hosted mailer (`meditransfer-mailer.fly.dev`, Postmark broadcast stream, authenticated domain `meditransfer.ch`).

---

## Current state (last updated 2026-04-23)

**Sent so far: 1,554 unique emails across 5 campaigns**, all from the `_mailer/mailer/templates/` A/B/C split:

| Campaign | Sent | Segment |
|---|---|---|
| `smalldach-referral-20260421` | 300 | groupPractices+medClinics+medicalCenters, DACH, has_referral=yes, priority bucket, one-per-domain. Day 1 (~300 initial sample). |
| `smalldach-referral-20260421-b` | 143 | Remainder of the same pool after same-day dedup. |
| `mid-dach-referral-20260422` | 77 | Adds `clinics` section to the above filter. Dedup against day 1 left only 77 new. |
| `mid-dach-broad-20260422` | 936 | Drops `has_referral=yes` (broader pool). Pool fully sent. |
| `hospitals-dach-20260423` | 97 of 159 | Hospitals, has_referral=yes, priority, one-per-domain. 62 pending → rolls into Fri 04-24. |

**Global opt-outs: 106**.

**Observed metrics on sends 1–2 (n=920):**
- Delivered rate: 99.7% (bounces 0.3%) — excellent
- Open rate: ~31% (still likely 5–10% scanner-inflated; reality ≈ 25%)
- **Real CTR (scanner-filtered): ~0.2%** (1 human click across all 443 sends measured in detail)
- Unsubscribe rate: ~5% first 48h then stabilising lower — in the high-normal range for cold B2B to a scraped list

**Fresh inventory (2026-04-23 post-enrichment re-crawl):** ~1,300 DACH+FR domains never contacted, after purging 1,318 stale-URL checkpoint entries and reclassifying the full checkpoint (`+1,860` sekretariat/zuweiser promotions, `-4,634` noise addresses). See `_mailer/out/next-week/*.csv` for the prepared campaign files.

---

## Guardrails (enforced by mailer, verified weekly)

| Signal | Watch | Halt |
|---|---|---|
| Spam-complaint rate (via Postmark webhook) | **> 0.05%** → pause 48h and investigate | **> 0.1%** → full halt; pivot strategy |
| Hard bounce rate | **> 1%** → review list-hygiene filter | **> 3%** → halt and rebuild segment |
| Unsubscribe rate | **> 5% sustained** → rethink copy/targeting | **> 8%** → halt |
| Volume increase day-over-day | Max **+20%** per day (even if metrics are perfect) | — |

**Why these numbers** — grounded in 2026 Gmail/Microsoft/Yahoo bulk-sender enforcement which is now actively triggering suspensions. Gmail's published ceiling is 0.3% complaint rate; the 0.1% / 0.05% numbers above are the "safe" and "aspirational" buffers that sustained cold operators target. Sources: see [References](#references) at the end.

**Postmark broadcast stream guidance**: for a server's **first** bulk send, Postmark asks senders to stick to **20k messages/hour for the first 12 hours**. Our `MAILER_RATE_PER_MINUTE=300` cap (= 18k/hour) already sits under that. We're nowhere near rate-limited.

**Gmail.com recipients**: Google now explicitly discourages cold B2B to `@gmail` without double-opt-in. The scraper collected ~5,000 `gmail.com` priority emails — keep them **off the list** for the foreseeable future. This is already easy to enforce: the current priority-bucket filter naturally skews away from them, and we can add a blocklist filter if we ever need to.

**HIN network (`*@hin.ch`)**: Swiss clinical secure-email network — our truest product-fit audience. Each HIN address is a specific person, not a shared mailbox, so **treat them as distinct recipients** (no domain-level dedup). Ramp cautiously with opt-outs aggressively honored; watch complaint rate per-batch because HIN users are domain-savvy and a complaint there carries more weight than `info@praxis.ch`.

---

## Ramp plan

Week ordinals count from day 1 of real cold sending = 2026-04-21.

| Week | Cap | Triggers to earn the bump |
|---|---|---|
| Week 1 (2026-04-21 → 2026-04-25) | **500/day** | Clean bounce (<1%), complaint <0.05%, unsub rate stabilising |
| Week 2 (2026-04-28 → 2026-05-02) | **1,000–1,500/day** | Same signals held through week 1 |
| Week 3 (2026-05-05 → 2026-05-09) | **2,500–3,500/day** | Same signals held through week 2; Postmaster Tools shows "high" or "medium" domain reputation |
| Week 4+ steady-state | **5,000/day ceiling** | Gmail postmaster reputation holds "high". Above this volume you need to coordinate with Postmark support. |

Weekdays only (Tue/Wed/Thu strongly preferred for Swiss clinic B2B). No Monday or Friday afternoon sends, no weekend sends. Stagger intra-day rather than blasting at 09:00 (our `MAILER_RATE_PER_MINUTE=300` already smooths it; for very large sends, split into 2–3 `send --live --limit N` invocations 1–2 hours apart).

Per user feedback (2026-04-22, saved in memory `feedback_mailer_confirm_before_send`): **every real `--live` send requires explicit per-batch user confirmation**, regardless of ramp plan.

---

## Next recipients (segment pipeline)

In send order. Each new segment is **one axis shift** from the previous send (one-axis-per-day rule).

### Week of 2026-04-24 → 2026-04-30 (prepared 2026-04-23)

Five CSVs, pre-built under `_mailer/out/next-week/` (gitignored like the rest of `_mailer/out/`; a copy lives in the dated backup dir `~/Documents/src-files/_DBS/pompom-crm-20260423/`). Each was dedup'd against the 1,554 already-sent emails and against every earlier day in the week (zero inter-day overlap; see `_mailer/build_next_week_campaigns.py` for the logic).

**Key unlock (2026-04-23 rebuild)**: HIN addresses (`*@hin.ch`) are NOT deduped by domain. Each HIN inbox is a specific person on Switzerland's clinical secure-email network — `sekretariat.x@hin.ch` and `dr.meier@hin.ch` are distinct recipients even though they share the domain. This unlocks 3,738 fresh HIN addresses.

| Day | CSV | Sends | Campaign name | Axis |
|---|---|---:|---|---|
| Fri 2026-04-24 | `day1-20260424-fri.csv` | 315 | `fresh-priority-20260424` | Priority (hospitals-ref finish + small non-HIN) + 84 HIN TOP-tier (sekretariat/zuweiser). |
| Mon 2026-04-27 | `day2-20260427-mon.csv` | 400 | `fresh-priority-mon-20260427` | Light Monday: 200 non-HIN priority + 200 HIN. |
| Tue 2026-04-28 | `day3-20260428-tue.csv` | 800 | `priority-hin-upgrades-20260428` | Non-HIN priority remainder + 54 top-tier upgrades (same-domain new-inbox axis) + 650 HIN. Week-2 ramp starts. |
| Wed 2026-04-29 | `day4-20260429-wed.csv` | 1,000 | `hin-other-20260429` | Peak day: 800 HIN + 200 non-HIN `other + has-referral=yes` (first send to non-prefix-matched practice inboxes). |
| Thu 2026-04-30 | `day5-20260430-thu.csv` | 1,200 | `hin-bulk-20260430` | HIN bulk (900) + `other` no-referral + fresh general (300). **CONDITIONAL** on Wed metrics holding: spam <0.05%, bounce <1%, unsub <5%. Skip if Wed looks bad. |
| **Total** | | **3,715** | | |

Caps land within the Week-2 policy ceiling (1,000–1,500/day). HIN is ~26%→81% of daily volume, ramping up as the non-HIN priority pool depletes. Pool remaining after this week: 1,104 fresh HIN + 257 other + 34 upgrades = ~1,400 for the following week, plus whatever new URL enrichment finds.

**Deferred to a later week:**
- **Sender-name A/B test** (memory `project_mailer_send_strategy`'s "send 2") — deferred until we have a uniform 2,000+ cohort to split cleanly.
- **Subject-line A/B test** ("send 3") — runs after the sender-name winner is known.
- **Romandie (VD, GE, NE, JU, parts of FR)** and **Ticino (TI)** — blocked on FR/IT template translation. The scraper has this data ready on the reclassified checkpoint (Romandie/Ticino run was cancelled mid-flight 2026-04-23; we have 914 partially-crawled addresses sitting in the checkpoint for whenever templates land).

See `_mailer/SEGMENTS.md` for historical filter invocations and the naming convention.

---

## Sender-identity / copy tests (planned, not yet run)

From the strategy memory (`project_mailer_send_strategy`):

- **Send 2 (next week)**: sender-name A/B test. Current is `Samuel Beatty · MediTransfer`; test against `MediTransfer` alone (corporate feel) or `Samuel · MediTransfer` (first-name-only, warmer). Expected open-rate delta: 10–20% in cold B2B — larger than subject wording effect.
- **Send 3 (week 3)**: subject-line A/B on the winning template. By then we know which of the 3 templates earned the most real engagement.

Run these BEFORE scaling past 2,500/day so the winner is locked in before we commit to volume.

---

## Kill switches

If any of these fire mid-send:

- Abort the `send --live` Ctrl-C is safe; the mailer records each attempt in `sends` before the next one fires, so a resume picks up where it stopped.
- Pause the machine: `fly machine stop e28692e3b99338 -a meditransfer-mailer`
- Mark a recipient opted-out so they're globally blocked from everything: `python send_mailer.py opt-outs add <email> --reason <why>` (on Fly)
- Bulk pause: set `MAILER_DAILY_CAP=0` in `fly.toml` and redeploy.

---

## References

Pulled 2026-04-22 to ground the numbers above.

- [Google / Yahoo / Microsoft bulk-sender guidelines explainer](https://www.allegrow.co/knowledge-base/google-bulk-sender-guidelines) — current 0.3% spam-complaint threshold, 2% bounce threshold enforcement as of May 2025, plus Microsoft's 5,000+/day authentication requirement.
- [Gmail postmaster complaint-rate cap, 2026](https://coldreach.ai/blog/gmail-spam-rules) — 0.1% warning, 0.3% hard cap, 7-day remediation window.
- [Postmark office hours recap — broadcast-stream rate guidance](https://postmarkapp.com/blog/postmark-office-hours) — "stick to 20k/hour for the first 12 hours of your first bulk send".
- [Postmark servers FAQ](https://postmarkapp.com/support/article/1137-servers-faq) — per-server rate-limit posture and 429 response.
- [B2B cold-email deliverability benchmarks, 2026](https://instantly.ai/blog/how-to-achieve-90-cold-email-deliverability-in-2025/?lng=en) — practical thresholds (1 complaint per 2,000 sends = safe-zone target).
- [Domain warm-up 2026 playbook](https://prospeo.io/s/domain-warm-up-for-cold-email) — 20%/day max volume increase rule.
- [Cold email inbox limit Google vs Microsoft, 2026](https://litemail.ai/blog/cold-email-inbox-limit-per-day-google-vs-microsoft-2026) — per-mailbox limits (different class from our authenticated Postmark broadcast setup but useful sanity check).
