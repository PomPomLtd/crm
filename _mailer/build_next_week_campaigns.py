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


def collapse_one_per_domain(records: Iterable[dict]) -> Dict[str, dict]:
    """Collapse to one-per-domain. Priority bucket wins over general/other.
    Within priority, TOP-tier local-parts win (sekretariat/zuweiser/…).
    First-occurrence tiebreak."""
    best: Dict[str, dict] = {}
    bucket_rank = {'priority': 0, 'general': 1, 'other': 2}
    for r in records:
        dom = r['email'].split('@', 1)[1]
        key = (bucket_rank[r['bucket']],
               top_tier_rank(r['email'].split('@', 1)[0]) if r['bucket'] == 'priority' else 999)
        cur = best.get(dom)
        if cur is None or key < cur['_key']:
            r2 = dict(r)
            r2['_key'] = key
            best[dom] = r2
    for r in best.values():
        r.pop('_key', None)
    return best


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

    # Build master pool — one-per-domain from the reclassified checkpoint.
    all_records = list(iter_pool())
    print(f'Checkpoint yielded {len(all_records)} (entry, email) records.')
    by_domain = collapse_one_per_domain(all_records)
    print(f'One-per-domain pool: {len(by_domain)} unique domains.')

    # Fresh pool = domains not yet contacted.
    fresh = [r for d, r in by_domain.items() if d not in sent_domains]
    upgrades = [r for d, r in by_domain.items() if d in sent_domains and r['email'] not in sent_emails]
    print(f'  fresh (new domain):       {len(fresh)}')
    print(f'  upgrade (diff email, same domain as prior send): {len(upgrades)}')

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

    hospitals_priority = sorted(
        (r for r in fresh
         if r['section'] == 'hospitals' and r['bucket'] == 'priority'),
        key=_pri_sort_key)
    small_priority = sorted(
        (r for r in fresh
         if r['section'] in ('groupPractices', 'medClinics', 'medicalCenters', 'clinics')
         and r['bucket'] == 'priority'
         and r['email'] not in {x['email'] for x in hospitals_priority}),
        key=_pri_sort_key)
    # Take all hospitals first (only ~130 anyway; 62 of those are the
    # unsent-20260423 remainder), then fill with small sections.
    day1 = hospitals_priority + small_priority
    day1 = day1[:300]
    for r in day1:
        used_emails.add(r['email'])
    write_csv(OUT_DIR / 'day1-20260424-fri.csv', day1)
    summary(day1, 'day1-20260424-fri')

    # --- Day 2 (Mon 04-27) ---
    # Conservative Monday: fresh priority from small sections + clinics.
    # Cap at 200 (not 250) to leave ~100 fresh priority in the pool for
    # Tuesday's bigger batch.
    small_priority_rest = sorted(
        (r for r in fresh
         if r['section'] in ('groupPractices', 'medClinics', 'medicalCenters', 'clinics')
         and r['bucket'] == 'priority'
         and r['email'] not in used_emails),
        key=_pri_sort_key)
    day2 = small_priority_rest[:200]
    for r in day2:
        used_emails.add(r['email'])
    write_csv(OUT_DIR / 'day2-20260427-mon.csv', day2)
    summary(day2, 'day2-20260427-mon')

    # --- Day 3 (Tue 04-28) ---
    # Week 2 starts. Target 250 — priority leftovers + all top-tier upgrades
    # + pad from other+has-referral=yes to 250.  Leaves most of the
    # other+referral pool for Day 4.
    remaining_priority = sorted(
        (r for r in fresh
         if r['bucket'] == 'priority'
         and r['email'] not in used_emails),
        key=_pri_sort_key)
    day3_upgrades = [
        r for r in upgrades
        if r['bucket'] == 'priority'
        and top_tier_rank(r['email'].split('@', 1)[0]) < 999
        and r['email'] not in used_emails
    ]
    other_ref_pool = sorted(
        (r for r in fresh
         if r['bucket'] == 'other' and r['has_referral'] == 'yes'
         and r['email'] not in used_emails),
        key=lambda r: (r['canton'], r['email']))
    day3_base = remaining_priority + day3_upgrades
    pad_needed = max(0, 250 - len(day3_base))
    day3 = day3_base + other_ref_pool[:pad_needed]
    day3 = day3[:250]
    for r in day3:
        used_emails.add(r['email'])
    write_csv(OUT_DIR / 'day3-20260428-tue.csv', day3)
    summary(day3, 'day3-20260428-tue')

    # --- Day 4 (Wed 04-29) ---
    # "Other + referral" primary day. Target 200. Takes remaining other+ref,
    # then tops up from other no-referral if needed.
    other_ref_remainder = sorted(
        (r for r in fresh
         if r['bucket'] == 'other' and r['has_referral'] == 'yes'
         and r['email'] not in used_emails),
        key=lambda r: (r['canton'], r['email']))
    other_no_ref_fallback = sorted(
        (r for r in fresh
         if r['bucket'] == 'other' and r['has_referral'] == 'no'
         and r['email'] not in used_emails),
        key=lambda r: (r['canton'], r['email']))
    day4 = other_ref_remainder + other_no_ref_fallback[: max(0, 200 - len(other_ref_remainder))]
    day4 = day4[:200]
    for r in day4:
        used_emails.add(r['email'])
    write_csv(OUT_DIR / 'day4-20260429-wed.csv', day4)
    summary(day4, 'day4-20260429-wed')

    # --- Day 5 (Thu 04-30) ---
    # Week 2 end — CONDITIONAL on Wed metrics holding. Target 200.
    # "Other" no-referral remainder + fresh general. If Wed
    # spam/bounce/unsub ticks up, skip this day entirely.
    other_no_ref = sorted(
        (r for r in fresh
         if r['bucket'] in ('other', 'general') and r['has_referral'] == 'no'
         and r['email'] not in used_emails),
        key=lambda r: (r['canton'], r['email']))
    day5 = other_no_ref[:200]
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
