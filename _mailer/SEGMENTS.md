# Mailer segments

Named, reproducible cohorts for the MediTransfer cold-outreach mailer. Each entry is a copy-pasteable `targets build` invocation and a campaign-name convention.

**Convention:** campaign name = `{segment-name}-{YYYYMMDD}`. The dashboard tracks stats per campaign, so filtering by campaign-name prefix gives per-segment historical comparison.

---

## `smalldach-referral` — send 1 (first cold-outreach batch)

The three smallest-customer sections, with a detected referral intake, German-speaking cantons, priority inboxes only, one recipient per domain.

```bash
python send_mailer.py targets build \
  --sections groupPractices,medClinics,medicalCenters \
  --has-referral yes \
  --bucket priority \
  --cantons ZH,BE,AG,LU,SG,BS,BL,SO,TG,SH,SZ,ZG,GR,AR,AI,OW,NW,UR,GL,FR \
  --one-per-domain \
  -o out/smalldach-referral-raw.csv
```

**Rationale:**
- `groupPractices,medClinics,medicalCenters` — small practices only. `hospitals` excluded (chain duplication + wrong first audience). `clinics` excluded (contains both small specialty sites and large-chain branches that can't be filtered by section alone).
- `has-referral=yes` — the scraper detected a referral intake (form / pdf / fax / email / doc / page-only). The templates' premise ("Zuweisungen kommen per Fax, E-Mail, Telefon und Word") is demonstrably true for these practices.
- `bucket=priority` — `info@` / `kontakt@` / `sekretariat@` prefixes plus all `*@hin.ch`. Lowest backlash risk, highest reply likelihood for cold B2B.
- 19 German-speaking cantons — Romandie (VD, GE, NE, JU, parts of FR) and Ticino (TI) excluded because the templates are DE-only.
- `--one-per-domain` — collapses `info@x.ch` + `kontakt@x.ch` + `sekretariat@x.ch` down to one address per domain. Priority addresses always win over general/other because of the bucket-iteration order; first-occurrence wins among priority.

Campaign name: `smalldach-referral-YYYYMMDD`

---

## `smalldach-referral-tier2` — send 1b (follow-up)

Same filter as send 1, minus the recipients already covered. Reuse for follow-up waves or to round out send 1 past its daily cap.

```bash
# 1. Build the full pool
python send_mailer.py targets build \
  --sections groupPractices,medClinics,medicalCenters \
  --has-referral yes --bucket priority --one-per-domain \
  --cantons ZH,BE,AG,LU,SG,BS,BL,SO,TG,SH,SZ,ZG,GR,AR,AI,OW,NW,UR,GL,FR \
  -o out/smalldach-referral-full.csv

# 2. Subtract already-sent emails (pull from the Fly DB)
fly ssh console -a meditransfer-mailer -C "sh -lc 'cd /app && \
  sqlite3 /data/mailer.db \"SELECT LOWER(email) FROM sends JOIN recipients \
  ON sends.recipient_id=recipients.id WHERE sends.status=\\\"sent\\\";\"' " \
  > out/already-sent.txt

# 3. csv-difference → tier2 file (awk or python one-liner)
```

Campaign name: `smalldach-referral-tier2-YYYYMMDD`

---

## `mid-dach` — add the `clinics` section

Once send 1 is proven, broaden to small-to-mid practices by adding `clinics` (which mixes small specialty clinics and larger private-clinic branches).

```bash
python send_mailer.py targets build \
  --sections groupPractices,medClinics,medicalCenters,clinics \
  --has-referral yes --bucket priority --one-per-domain \
  --cantons ZH,BE,AG,LU,SG,BS,BL,SO,TG,SH,SZ,ZG,GR,AR,AI,OW,NW,UR,GL,FR \
  -o out/mid-dach-raw.csv
```

Campaign name: `mid-dach-YYYYMMDD`

---

## `hospitals-dach` — large institutions (deferred)

Big chains: Hirslanden, USZ, Insel, KSGR, etc. Highest per-domain email count (8.8× average duplication). `--one-per-domain` is **essential** here to avoid blasting the same inbox repeatedly.

Best sent only after we have clear reply-rate data from smaller segments, and ideally after a Romandie/Ticino copy variant exists (several chains are nationwide).

```bash
python send_mailer.py targets build \
  --sections hospitals \
  --has-referral yes --bucket priority --one-per-domain \
  --cantons ZH,BE,AG,LU,SG,BS,BL,SO,TG,SH,SZ,ZG,GR,AR,AI,OW,NW,UR,GL,FR \
  -o out/hospitals-dach-raw.csv
```

Campaign name: `hospitals-dach-YYYYMMDD`

---

## `top-tier-upgrade` — same-domain, different-inbox axis (2026-04-24+)

Emails at domains we've **already contacted** where the scraper's tier-system now exposes a top-tier address (sekretariat@, zuweiser@, empfang@) that wasn't in the priority bucket on the first pass. Ethically this is a new recipient (different inbox); operationally it's a way to reach the referral coordinator after we first reached the generic `info@`. Use cautiously — the two inboxes may forward to the same person at small practices.

Not a standalone `targets build` invocation — it needs cross-referencing against the Fly sends table. See `_mailer/build_next_week_campaigns.py` for the implementation.

---

## `other-ref` — lower-confidence inbox prefix, referral-detected

Mailboxes that don't match any priority prefix (info / sekretariat / contact / etc.) but sit on a practice site where the scraper detected a referral section. Examples: `team@praxis-x.ch`, `praxis.meier@x.ch`, `kontaktformular@x.ch`. The referral-section signal on the same site gives us confidence this is a real practice inbox.

```bash
python send_mailer.py targets build \
  --checkpoint ../_scrapers/results/clinic_emails_checkpoint.jsonl.reclassified.jsonl \
  --sections groupPractices,medClinics,medicalCenters,clinics,hospitals \
  --has-referral yes --bucket all --one-per-domain \
  --cantons ZH,BE,AG,LU,SG,BS,BL,SO,TG,SH,SZ,ZG,GR,AR,AI,OW,NW,UR,GL,FR \
  -o out/other-ref-raw.csv
# ↑ includes priority (use that for earlier sends); filter to bucket=other
#   for this specific axis.
```

Campaign name: `other-ref-YYYYMMDD`

---

## Sampling to a fixed size

`targets build` has no size cap — filters produce whatever they produce. To sample to an exact size with a reproducible seed:

```python
import csv, random
random.seed(42)  # stable — same sample on re-run
with open("out/SEGMENT-raw.csv") as f:
    rows = list(csv.reader(f))
header, body = rows[0], rows[1:]
sample = random.sample(body, min(300, len(body)))
with open("out/SEGMENT-300.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(header); w.writerows(sample)
```

The sampled CSV should be committed (or at minimum stored on the Fly mounted volume under `/data/recipients/`) so the exact cohort is recoverable.
