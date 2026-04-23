"""One-shot builder for the Fri 04-24 → Thu 04-30 send plan.

Reads:
- Reclassified scraper checkpoint
- Already-sent emails list (exported from Fly)

Writes five campaign CSVs under `_mailer/out/next-week/`, one per send day.
Each day's CSV is dedup'd against all prior days + the Fly sends history,
so no recipient is ever queued twice.

Run once, review the CSVs, then each day's send copies the CSV into the Fly
volume and creates the campaign. See `_mailer/send_plan.md` for the ops
walkthrough.
"""
from __future__ import annotations

import csv
import json
import os
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Set

ROOT = Path(__file__).resolve().parent.parent
CHECKPOINT = ROOT / "_scrapers" / "results" / "clinic_emails_checkpoint.jsonl.reclassified.jsonl"
ENTRIES = ROOT / "_scrapers" / "results" / "clinic_entries.json"
SENT_LIST = Path("/tmp/already-sent-emails.txt")
OUT_DIR = ROOT / "_mailer" / "out" / "next-week"

DACH_FR = {'ZH','BE','AG','LU','SG','BS','BL','SO','TG','SH','SZ','ZG','GR','AR','AI','OW','NW','UR','GL','FR'}

# Top-tier priority prefixes (must match extractors.py)
TOP_PREFIXES = (
    'sekretariat','secretariat','secretary','segreteria','empfang',
    'reception','accueil','ricezione','mpa','anmeldung','termin',
    'termine','zuweiser','zuweisung','referral','referring',
    'medecin-referent','triage',
)

FIELDS = ['email','entry_id','section','title','url','bucket','has_referral','canton','profession']


def top_tier_rank(local: str) -> int:
    for i, p in enumerate(TOP_PREFIXES):
        if local == p or local.startswith(p + '.') or local.startswith(p + '-') \
           or local.startswith(p + '_') or local.startswith(p):
            return i
    return 999


def load_sent() -> tuple[Set[str], Set[str]]:
    emails: Set[str] = set()
    domains: Set[str] = set()
    with SENT_LIST.open() as f:
        for line in f:
            e = line.strip().lower()
            if e:
                emails.add(e)
                if '@' in e:
                    domains.add(e.split('@', 1)[1])
    return emails, domains


def load_entries_idx() -> Dict[int, dict]:
    with ENTRIES.open() as f:
        return {int(e['id']): e for e in json.load(f)}


def iter_pool():
    """Yield normalized (entry, bucket, email) records from the reclassified
    checkpoint. One record per email, all buckets."""
    entries_idx = load_entries_idx()
    with CHECKPOINT.open() as f:
        for line in f:
            rec = json.loads(line)
            eid = rec.get('entry_id')
            if eid is None:
                continue
            ent = entries_idx.get(int(eid))
            if not ent:
                continue
            canton = (ent.get('canton') or '').upper()
            if canton not in DACH_FR:
                continue
            section = rec.get('section', '')
            if section not in ('groupPractices', 'medClinics', 'medicalCenters', 'clinics', 'hospitals'):
                continue
            ems = rec.get('emails') or {}
            has_ref = 'yes' if (rec.get('referral') or {}).get('found') else 'no'
            for bucket in ('priority', 'general', 'other'):
                for e in (ems.get(bucket) or []):
                    e = e.lower().strip()
                    if '@' not in e:
                        continue
                    yield {
                        'email': e,
                        'entry_id': eid,
                        'section': section,
                        'title': ent.get('title', ''),
                        'url': ent.get('url', ''),
                        'bucket': bucket,
                        'has_referral': has_ref,
                        'canton': canton,
                        'profession': '',
                    }


HIN_DOMAIN = 'hin.ch'


def collapse_one_per_domain(records: Iterable[dict]) -> List[dict]:
    """Collapse to one-per-domain EXCEPT hin.ch.

    Non-HIN: keep one recipient per practice domain (priority bucket wins
    over general/other; within priority, TOP-tier local-parts win).

    HIN (`*@hin.ch`): keep every address. Each HIN address is a specific
    person on Switzerland's clinical secure-email network — they happen to
    share a domain but are distinct recipients.
    """
    best: Dict[str, dict] = {}
    hin_all: List[dict] = []
    hin_seen: Set[str] = set()
    bucket_rank = {'priority': 0, 'general': 1, 'other': 2}
    for r in records:
        dom = r['email'].split('@', 1)[1]
        if dom == HIN_DOMAIN:
            # Dedup HIN by exact email (same address might appear under
            # multiple Craft entry duplicates — collapse those only).
            if r['email'] in hin_seen:
                continue
            hin_seen.add(r['email'])
            hin_all.append(dict(r))
            continue
        key = (bucket_rank[r['bucket']],
               top_tier_rank(r['email'].split('@', 1)[0]) if r['bucket'] == 'priority' else 999)
        cur = best.get(dom)
        if cur is None or key < cur['_key']:
            r2 = dict(r)
            r2['_key'] = key
            best[dom] = r2
    for r in best.values():
        r.pop('_key', None)
    return list(best.values()) + hin_all


def write_csv(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in FIELDS})


def summary(rows: List[dict], name: str) -> None:
    sec = Counter(r['section'] for r in rows)
    buc = Counter(r['bucket'] for r in rows)
    ref = Counter(r.get('has_referral', '') for r in rows)
    can = Counter(r.get('canton', '') for r in rows)
    print(f'\n--- {name} ({len(rows)}) ---')
    print(f'  section:  {dict(sec.most_common())}')
    print(f'  bucket:   {dict(buc.most_common())}')
    print(f'  referral: {dict(ref.most_common())}')
    print(f'  cantons:  {dict(can.most_common(8))}')


def main():
    sent_emails, sent_domains = load_sent()
    print(f'Loaded {len(sent_emails)} already-sent emails / {len(sent_domains)} domains.')

    # Build master pool — one-per-domain from the reclassified checkpoint
    # (except hin.ch, which keeps every distinct address).
    all_records = list(iter_pool())
    print(f'Checkpoint yielded {len(all_records)} (entry, email) records.')
    pool = collapse_one_per_domain(all_records)
    non_hin = [r for r in pool if r['email'].split('@', 1)[1] != HIN_DOMAIN]
    hin = [r for r in pool if r['email'].split('@', 1)[1] == HIN_DOMAIN]
    print(f'Pool: {len(non_hin)} non-HIN domains + {len(hin)} HIN addresses = {len(pool)} total.')

    # Fresh = email not yet sent.
    #   - non-HIN: also dedup by-domain against sent_domains (don't re-contact
    #     a practice at a different mailbox this week)
    #   - HIN: only dedup by exact email (each HIN inbox is a distinct person)
    fresh_non_hin = [r for r in non_hin
                     if r['email'].split('@', 1)[1] not in sent_domains]
    fresh_hin = [r for r in hin if r['email'] not in sent_emails]
    upgrades = [r for r in non_hin
                if r['email'].split('@', 1)[1] in sent_domains
                and r['email'] not in sent_emails]
    fresh = fresh_non_hin + fresh_hin
    print(f'  fresh non-HIN (new domain):            {len(fresh_non_hin)}')
    print(f'  fresh HIN (new inbox on clinical net): {len(fresh_hin)}')
    print(f'  upgrade (diff email, same non-HIN domain as prior send): {len(upgrades)}')

    # A given day accumulates emails into `used_emails` so the next day
    # can't resurface them.
    used_emails: Set[str] = set()

    # --- Day 1 (Fri 04-24) ---
    # Finish hospitals-dach-20260423 remainder + fresh priority (referral
    # preferred but not required, since the referral-yes pool is smaller
    # than planned).  Target 300.
    def _pri_sort_key(r):
        # has_referral=yes first, then by canton (ZH/BE/AG dense first for
        # consistent template fit), then by email for stability.
        return (0 if r['has_referral'] == 'yes' else 1,
                r['canton'], r['email'])

    # Helper: HIN addresses are all priority bucket. Separate for clearer
    # audience slicing.
    def is_hin(r):
        return r['email'].split('@', 1)[1] == HIN_DOMAIN

    # --- Day 1 (Fri 04-24) — cap 500 ---
    # Finish hospitals-dach-20260423 remainder (62) + fresh non-HIN priority
    # (referral-preferred) + first tranche of HIN TOP-tier (sekretariat /
    # zuweiser / empfang).
    hospitals_priority = sorted(
        (r for r in fresh
         if r['section'] == 'hospitals' and r['bucket'] == 'priority'
         and not is_hin(r)),
        key=_pri_sort_key)
    small_priority = sorted(
        (r for r in fresh
         if r['section'] in ('groupPractices', 'medClinics', 'medicalCenters', 'clinics')
         and r['bucket'] == 'priority' and not is_hin(r)),
        key=_pri_sort_key)
    hin_top = sorted(
        (r for r in fresh
         if is_hin(r)
         and top_tier_rank(r['email'].split('@', 1)[0]) < 999),
        key=lambda r: (r['canton'], r['email']))
    day1 = hospitals_priority + small_priority[:200] + hin_top[:150]
    day1 = day1[:500]
    for r in day1:
        used_emails.add(r['email'])
    write_csv(OUT_DIR / 'day1-20260424-fri.csv', day1)
    summary(day1, 'day1-20260424-fri')

    # --- Day 2 (Mon 04-27) — cap 400 ---
    # Light Monday. Remaining fresh non-HIN priority + more HIN TOP-tier.
    small_priority_rest = sorted(
        (r for r in fresh
         if r['section'] in ('groupPractices', 'medClinics', 'medicalCenters', 'clinics')
         and r['bucket'] == 'priority' and not is_hin(r)
         and r['email'] not in used_emails),
        key=_pri_sort_key)
    hin_top_rest = sorted(
        (r for r in fresh
         if is_hin(r)
         and top_tier_rank(r['email'].split('@', 1)[0]) < 999
         and r['email'] not in used_emails),
        key=lambda r: (r['canton'], r['email']))
    # Mix: up to 200 non-HIN, then HIN to fill 400.
    day2 = small_priority_rest[:200]
    remaining = 400 - len(day2)
    day2 = day2 + hin_top_rest[:remaining]
    if len(day2) < 400:
        # Pull any remaining HIN to hit 400.
        hin_rest = sorted(
            (r for r in fresh
             if is_hin(r) and r['email'] not in used_emails
             and r['email'] not in {x['email'] for x in day2}),
            key=lambda r: (r['canton'], r['email']))
        day2 = day2 + hin_rest[: 400 - len(day2)]
    day2 = day2[:400]
    for r in day2:
        used_emails.add(r['email'])
    write_csv(OUT_DIR / 'day2-20260427-mon.csv', day2)
    summary(day2, 'day2-20260427-mon')

    # --- Day 3 (Tue 04-28) — cap 800 ---
    # Week 2 ramp. Remaining non-HIN priority + all top-tier upgrades + HIN.
    remaining_priority = sorted(
        (r for r in fresh
         if r['bucket'] == 'priority' and not is_hin(r)
         and r['email'] not in used_emails),
        key=_pri_sort_key)
    day3_upgrades = [
        r for r in upgrades
        if r['bucket'] == 'priority'
        and top_tier_rank(r['email'].split('@', 1)[0]) < 999
        and r['email'] not in used_emails
    ]
    hin_for_day3 = sorted(
        (r for r in fresh
         if is_hin(r) and r['email'] not in used_emails),
        key=lambda r: (r['canton'], r['email']))
    day3_base = remaining_priority + day3_upgrades
    remaining = max(0, 800 - len(day3_base))
    day3 = day3_base + hin_for_day3[:remaining]
    day3 = day3[:800]
    for r in day3:
        used_emails.add(r['email'])
    write_csv(OUT_DIR / 'day3-20260428-tue.csv', day3)
    summary(day3, 'day3-20260428-tue')

    # --- Day 4 (Wed 04-29) — cap 1000 ---
    # Peak HIN day. Bulk HIN + introduce "other + referral" non-HIN axis.
    hin_for_day4 = sorted(
        (r for r in fresh
         if is_hin(r) and r['email'] not in used_emails),
        key=lambda r: (r['canton'], r['email']))
    other_ref = sorted(
        (r for r in fresh
         if not is_hin(r) and r['bucket'] == 'other'
         and r['has_referral'] == 'yes'
         and r['email'] not in used_emails),
        key=lambda r: (r['canton'], r['email']))
    day4 = hin_for_day4[:800] + other_ref[:200]
    day4 = day4[:1000]
    for r in day4:
        used_emails.add(r['email'])
    write_csv(OUT_DIR / 'day4-20260429-wed.csv', day4)
    summary(day4, 'day4-20260429-wed')

    # --- Day 5 (Thu 04-30) — cap 1200 (CONDITIONAL on Wed metrics) ---
    # HIN remainder + other no-referral + fresh general.
    hin_for_day5 = sorted(
        (r for r in fresh
         if is_hin(r) and r['email'] not in used_emails),
        key=lambda r: (r['canton'], r['email']))
    other_rest = sorted(
        (r for r in fresh
         if not is_hin(r) and r['bucket'] in ('other', 'general')
         and r['email'] not in used_emails),
        key=lambda r: (r['canton'], r['email']))
    day5 = hin_for_day5[:900] + other_rest[:300]
    day5 = day5[:1200]
    for r in day5:
        used_emails.add(r['email'])
    write_csv(OUT_DIR / 'day5-20260430-thu.csv', day5)
    summary(day5, 'day5-20260430-thu')

    # Totals
    total = sum(len(x) for x in (day1, day2, day3, day4, day5))
    remaining_priority = sum(1 for r in fresh if r['bucket'] == 'priority' and r['email'] not in used_emails)
    remaining_other = sum(1 for r in fresh if r['bucket'] == 'other' and r['email'] not in used_emails)
    remaining_upgrades = sum(1 for r in upgrades if r['email'] not in used_emails)
    print(f'\n=== TOTAL next week: {total} sends ===')
    print(f'Inventory left over (future weeks):')
    print(f'  fresh priority: {remaining_priority}')
    print(f'  fresh other:    {remaining_other}')
    print(f'  upgrades:       {remaining_upgrades}')


if __name__ == '__main__':
    main()
