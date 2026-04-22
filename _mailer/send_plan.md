# MediTransfer cold-outreach send plan

Living document. Update as sends go out. All volumes are from the Fly-hosted mailer (`meditransfer-mailer.fly.dev`, Postmark broadcast stream, authenticated domain `meditransfer.ch`).

---

## Current state (last updated 2026-04-22, end of day 2)

**Sent so far: 920 total across 4 campaigns**, all from the `_mailer/mailer/templates/` A/B/C split:

| Campaign | Sent | Segment |
|---|---|---|
| `smalldach-referral-20260421` | 300 | groupPractices+medClinics+medicalCenters, DACH, has_referral=yes, priority bucket, one-per-domain. Day 1 (~300 initial sample). |
| `smalldach-referral-20260421-b` | 143 | Remainder of the same pool after same-day dedup. |
| `mid-dach-referral-20260422` | 77 | Adds `clinics` section to the above filter. Dedup against day 1 left only 77 new. |
| `mid-dach-broad-20260422` | 400 of 936 pending | Drops `has_referral=yes` (broader pool). 536 still pending in this campaign. |

**Global opt-outs: 66** (auto-added from bounces + unsubscribes + 4 manually-added HIN-redirect cases).

**Observed metrics on sends 1 (day 1, n=443):**
- Delivered rate: 99.7% (bounces 0.3%) — excellent
- Open rate: ~31% (still likely 5–10% scanner-inflated; reality ≈ 25%)
- **Real CTR (scanner-filtered): ~0.2%** (1 human click across all 443 sends)
- Unsubscribe rate: ~5% first 48h then stabilising lower — in the high-normal range for cold B2B to a scraped list

**Segments exhausted:** `smalldach-referral` (both halves) — the entire `groupPractices + medClinics + medicalCenters × DACH × has_referral=yes × priority × one-per-domain` pool has been contacted.

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

**HIN network (`*@hin.ch`)**: These are the Swiss clinical secure-email network addresses — our truest product-fit audience. **Never cold-send to HIN.** They were explicitly given for clinical correspondence, not marketing. Keep them for warm, one-to-one outreach only.

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

1. **`mid-dach-broad-20260422` (536 remaining)** — Thursday 2026-04-23: send another 400–500 from the existing `mid-dach-broad` pool. No change to the filter; just draining the remainder.
2. **`mid-dach-broad-priority-general`** — next axis shift: add the `general` bucket (doctor personal addresses like `dr.meier@praxis.ch`) to the existing DACH × small-sections × has-referral-agnostic filter. Expected new pool: ~1,000–2,000 after cross-campaign dedup. Send size: per ramp cap.
3. **`hospitals-dach`** — deferred until we have clear signal from the smaller-practice cohorts. Chain sites (Hirslanden, USZ, Insel, KSGR) dominate this section; `--one-per-domain` is **mandatory** to avoid blasting the same inbox.
4. **Romandie (VD, GE, NE, JU, parts of FR)** — blocked on a French translation of the 3 templates. Same story for Ticino (TI) + Italian.

Segments 2 and 3 are documented in `_mailer/SEGMENTS.md` with copy-pasteable CLI invocations.

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
