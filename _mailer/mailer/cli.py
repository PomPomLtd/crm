"""Command-line interface for the Pom Pom cold-outreach mailer.

Subcommands:
  targets build       — build a recipients CSV from the scraper checkpoint
  campaign create     — register a campaign + bucket its recipients A/B/C
  campaign list       — list campaigns
  render              — dry-run render one variant to stdout (html or txt)
  send                — send a batch (dry-run by default until --live)
  stats               — per-variant sent / opened / bounced / unsubscribed
  opt-outs list       — dump the suppression list
  opt-outs add        — manually add an email
  opt-outs remove     — manually remove an email
  webhook             — run the Flask webhook / unsubscribe server

All commands share --db which overrides MAILER_DB_PATH.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from . import db, render as rendermod, sender, targets, webhook
from .bucket import VARIANTS, assign_variant
from .config import MAILER_ROOT, REPO_ROOT, Config, load_env


DEFAULT_CHECKPOINT = REPO_ROOT / "_scrapers" / "results" / "clinic_emails_checkpoint.jsonl"
DEFAULT_RECIPIENTS_OUT = MAILER_ROOT / "out" / "recipients.csv"

DEFAULT_TEMPLATE_MAP = {
    "A": "01-der-brief",
    "B": "02-hero-cta",
    "C": "03-stunden-zu-minuten",
}
DEFAULT_SUBJECT_MAP = {
    "A": "Zuweisungen digital – ein kurzer Brief aus Zürich",
    "B": "Patientenüberweisungen einfach digital – 30 Tage kostenlos",
    "C": "Stunden → Minuten: Zuweisungen, die sich selbst sortieren",
}


def _setup_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )


# ---- targets ----

def cmd_targets_build(args: argparse.Namespace) -> int:
    checkpoint = Path(args.checkpoint).resolve()
    if not checkpoint.exists():
        print(f"Checkpoint not found: {checkpoint}", file=sys.stderr)
        return 2

    print(f"Reading checkpoint: {checkpoint}")
    sections = args.sections.split(",") if args.sections else None
    cantons = args.cantons.split(",") if args.cantons else None
    has_referral = None
    if args.has_referral == "yes":
        has_referral = True
    elif args.has_referral == "no":
        has_referral = False

    recipients = targets.build_recipients(
        checkpoint_path=checkpoint,
        repo_root=REPO_ROOT,
        sections=sections,
        cantons=cantons,
        profession_contains=args.profession_contains,
        has_referral=has_referral,
        bucket=args.bucket,
        enrich=not args.no_enrich,
    )

    out = Path(args.out).resolve()
    written = targets.write_recipients_csv(out, recipients)
    print(f"Wrote {written} recipients to {out}")

    # Print a short summary
    by_section: dict[str, int] = {}
    by_bucket: dict[str, int] = {}
    by_canton: dict[str, int] = {}
    for r in recipients:
        by_section[r.section] = by_section.get(r.section, 0) + 1
        by_bucket[r.bucket] = by_bucket.get(r.bucket, 0) + 1
        by_canton[r.canton or "?"] = by_canton.get(r.canton or "?", 0) + 1

    print(f"\nBy section:  {dict(sorted(by_section.items(), key=lambda kv: -kv[1]))}")
    print(f"By bucket:   {dict(sorted(by_bucket.items(), key=lambda kv: -kv[1]))}")
    top_cantons = dict(sorted(by_canton.items(), key=lambda kv: -kv[1])[:10])
    print(f"Top cantons: {top_cantons}")
    return 0


# ---- campaign ----

def cmd_campaign_create(args: argparse.Namespace) -> int:
    config = Config.from_env()
    db.init_schema(config.db_path)

    templates = {
        "A": args.template_a or DEFAULT_TEMPLATE_MAP["A"],
        "B": args.template_b or DEFAULT_TEMPLATE_MAP["B"],
        "C": args.template_c or DEFAULT_TEMPLATE_MAP["C"],
    }
    for v, name in templates.items():
        if name not in rendermod.KNOWN_TEMPLATES:
            print(f"Unknown template '{name}' for variant {v}. Known: {rendermod.KNOWN_TEMPLATES}", file=sys.stderr)
            return 2

    subjects = {
        "A": args.subject_a or DEFAULT_SUBJECT_MAP["A"],
        "B": args.subject_b or DEFAULT_SUBJECT_MAP["B"],
        "C": args.subject_c or DEFAULT_SUBJECT_MAP["C"],
    }

    if args.emails:
        rows = [
            {
                "email": e.strip().lower(),
                "entry_id": "",
                "section": "test",
                "title": "",
                "url": "",
                "bucket": "priority",
                "has_referral": "no",
                "canton": "",
                "profession": "",
            }
            for e in args.emails.split(",")
            if e.strip()
        ]
        print(f"Using {len(rows)} inline test email(s) from --emails")
    else:
        recipients_csv = Path(args.recipients).resolve()
        if not recipients_csv.exists():
            print(f"Recipients CSV not found: {recipients_csv}", file=sys.stderr)
            return 2
        rows = targets.read_recipients_csv(recipients_csv)
        print(f"Loaded {len(rows)} recipients from {recipients_csv}")

    with db.connect(config.db_path) as conn:
        existing = db.get_campaign(conn, args.name)
        if existing:
            print(f"Campaign '{args.name}' already exists (id={existing['id']}). Use a different --name or delete the DB row.", file=sys.stderr)
            return 2

        campaign_id = db.create_campaign(
            conn,
            name=args.name,
            from_email=config.postmark_from_email,
            from_name=config.postmark_from_name,
            subject_a=subjects["A"],
            subject_b=subjects["B"],
            subject_c=subjects["C"],
            notes=args.notes,
        )
        conn.execute(
            "UPDATE campaigns SET template_a=?, template_b=?, template_c=? WHERE id=?",
            (templates["A"], templates["B"], templates["C"], campaign_id),
        )

        counts = {"A": 0, "B": 0, "C": 0, "opted_out": 0, "added": 0}
        for row in rows:
            email = (row.get("email") or "").strip().lower()
            if not email:
                continue
            if db.is_opted_out(conn, email):
                counts["opted_out"] += 1
                continue
            variant = assign_variant(email, salt=args.name)
            has_ref = (row.get("has_referral") or "").strip().lower() == "yes"
            db.upsert_recipient(
                conn,
                campaign_id=campaign_id,
                email=email,
                variant=variant,
                entry_id=int(row["entry_id"]) if row.get("entry_id") else None,
                section=row.get("section") or None,
                canton=(row.get("canton") or "") or None,
                profession=(row.get("profession") or "") or None,
                has_referral=has_ref,
                title=row.get("title") or None,
                url=row.get("url") or None,
                bucket=row.get("bucket") or None,
            )
            counts[variant] += 1
            counts["added"] += 1

        print(f"Campaign '{args.name}' (id={campaign_id}) created.")
        print(f"  Templates: {templates}")
        print(f"  Variants:  A={counts['A']}  B={counts['B']}  C={counts['C']}")
        print(f"  Skipped (opted out): {counts['opted_out']}")
        print(f"  Total added: {counts['added']}")
    return 0


def cmd_campaign_list(args: argparse.Namespace) -> int:
    config = Config.from_env()
    db.init_schema(config.db_path)
    with db.connect(config.db_path) as conn:
        rows = conn.execute(
            "SELECT id, name, status, created_at, template_a, template_b, template_c "
            "FROM campaigns ORDER BY id"
        ).fetchall()
        if not rows:
            print("No campaigns.")
            return 0
        for r in rows:
            print(f"  #{r['id']:>3}  {r['name']:<24}  {r['status']:<8}  "
                  f"A={r['template_a']} B={r['template_b']} C={r['template_c']}  "
                  f"{r['created_at']}")
    return 0


# ---- render (dry-run preview) ----

def cmd_render(args: argparse.Namespace) -> int:
    config = Config.from_env()
    db.init_schema(config.db_path)
    with db.connect(config.db_path) as conn:
        campaign = db.get_campaign(conn, args.campaign)
        if not campaign:
            print(f"Unknown campaign: {args.campaign}", file=sys.stderr)
            return 2

        if args.email:
            rec = conn.execute(
                "SELECT * FROM recipients WHERE campaign_id=? AND LOWER(email)=LOWER(?)",
                (campaign["id"], args.email),
            ).fetchone()
            if not rec:
                print(f"No recipient '{args.email}' in campaign '{args.campaign}'", file=sys.stderr)
                return 2
            variant = rec["variant"]
            rec_ctx = dict(rec)
        else:
            variant = args.variant or "A"
            rec_ctx = {
                "email": "preview@example.ch",
                "title": "Praxis Muster",
                "url": "https://praxis-muster.ch",
                "canton": "ZH",
                "section": "clinics",
                "profession": "Innere Medizin",
            }

        template_name = {
            "A": campaign["template_a"],
            "B": campaign["template_b"],
            "C": campaign["template_c"],
        }[variant]
        subject = {
            "A": campaign["subject_a"],
            "B": campaign["subject_b"],
            "C": campaign["subject_c"],
        }[variant]

    rendered = rendermod.render(
        template_name=template_name,
        subject=subject,
        recipient=rec_ctx,
        campaign_id=int(campaign["id"]),
        campaign_name=campaign["name"],
        base_url=config.base_url,
        token_secret=config.token_secret,
    )
    print(f"# Variant: {variant}   Template: {template_name}", file=sys.stderr)
    print(f"# Subject: {rendered.subject}", file=sys.stderr)
    print(f"# Unsubscribe: {rendered.unsubscribe_url}", file=sys.stderr)
    print(file=sys.stderr)
    if args.format == "txt":
        print(rendered.text)
    else:
        print(rendered.html)
    return 0


# ---- send ----

def cmd_send(args: argparse.Namespace) -> int:
    config = Config.from_env()
    db.init_schema(config.db_path)
    with db.connect(config.db_path) as conn:
        row = db.get_campaign(conn, args.campaign)
        if not row:
            print(f"Unknown campaign: {args.campaign}", file=sys.stderr)
            return 2

    campaign = sender.CampaignSpec(
        id=int(row["id"]),
        name=row["name"],
        from_email=row["from_email"],
        from_name=row["from_name"],
        reply_to=config.sender_reply_to or None,
        subjects={"A": row["subject_a"], "B": row["subject_b"], "C": row["subject_c"]},
        templates={"A": row["template_a"], "B": row["template_b"], "C": row["template_c"]},
    )

    dry = not args.live
    if dry:
        print("*** DRY RUN ***  (add --live to actually send)")

    stats = sender.send_campaign(
        config,
        campaign,
        limit=args.limit,
        dry_run=dry,
        progress=lambda m: print(m),
    )
    print(f"\nSummary: {json.dumps(stats)}")
    return 0


# ---- stats ----

def cmd_stats(args: argparse.Namespace) -> int:
    config = Config.from_env()
    db.init_schema(config.db_path)
    with db.connect(config.db_path) as conn:
        campaign = db.get_campaign(conn, args.campaign)
        if not campaign:
            print(f"Unknown campaign: {args.campaign}", file=sys.stderr)
            return 2
        stats = db.campaign_stats(conn, int(campaign["id"]))

    print(f"Campaign '{args.campaign}' (id={campaign['id']})")
    print(f"  templates: A={campaign['template_a']}  B={campaign['template_b']}  C={campaign['template_c']}\n")
    header = f"{'variant':<8} {'total':>6} {'sent':>6} {'fail':>5} {'open':>5} {'click':>6} {'bnce':>5} {'unsub':>5}  open%  CTR"
    print(header)
    print("-" * len(header))
    for variant in VARIANTS:
        s = stats.get(variant, {})
        total = int(s.get("total", 0) or 0)
        sent = int(s.get("sent", 0) or 0)
        failed = int(s.get("failed", 0) or 0)
        opened = int(s.get("opened", 0) or 0)
        clicked = int(s.get("clicked", 0) or 0)
        bounced = int(s.get("bounced", 0) or 0)
        unsub = int(s.get("unsubscribed", 0) or 0)
        open_rate = (opened / sent * 100.0) if sent else 0.0
        ctr = (clicked / sent * 100.0) if sent else 0.0
        print(f"{variant:<8} {total:>6} {sent:>6} {failed:>5} {opened:>5} {clicked:>6} {bounced:>5} {unsub:>5}  {open_rate:5.1f}%  {ctr:5.1f}%")
    return 0


# ---- opt-outs ----

def cmd_opt_outs_list(args: argparse.Namespace) -> int:
    config = Config.from_env()
    db.init_schema(config.db_path)
    with db.connect(config.db_path) as conn:
        rows = db.list_opt_outs(conn)
    if not rows:
        print("No opt-outs.")
        return 0
    for r in rows:
        print(f"  {r['created_at']}  {r['email']:<40}  {r['reason']:<24}  {r['source']}")
    return 0


def cmd_opt_outs_add(args: argparse.Namespace) -> int:
    config = Config.from_env()
    db.init_schema(config.db_path)
    with db.connect(config.db_path) as conn:
        db.add_opt_out(conn, email=args.email, reason=args.reason or "manual", source="cli")
    print(f"Added {args.email} to opt-outs.")
    return 0


def cmd_opt_outs_remove(args: argparse.Namespace) -> int:
    config = Config.from_env()
    db.init_schema(config.db_path)
    with db.connect(config.db_path) as conn:
        removed = db.remove_opt_out(conn, args.email)
    print(f"Removed {args.email}" if removed else f"{args.email} was not in opt-outs.")
    return 0


# ---- webhook ----

def cmd_webhook(args: argparse.Namespace) -> int:
    webhook.run(host=args.host, port=args.port)
    return 0


# ---- argparse wiring ----

def _apply_db_override(args: argparse.Namespace) -> None:
    if getattr(args, "db", None):
        import os
        os.environ["MAILER_DB_PATH"] = args.db


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="send_mailer.py",
        description="Pom Pom cold-outreach mailer for Swiss clinics.",
    )
    p.add_argument("--db", help="Override MAILER_DB_PATH for this invocation.")
    sub = p.add_subparsers(dest="cmd", required=True)

    # targets build
    p_targets = sub.add_parser("targets").add_subparsers(dest="subcmd", required=True)
    p_tb = p_targets.add_parser("build", help="Build recipients CSV from scraper checkpoint")
    p_tb.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    p_tb.add_argument("-o", "--out", default=str(DEFAULT_RECIPIENTS_OUT))
    p_tb.add_argument("--sections", help="Comma list, e.g. clinics,medicalCenters,hospitals")
    p_tb.add_argument("--cantons", help="Comma list of 2-letter canton codes, e.g. ZH,BE,GE")
    p_tb.add_argument("--profession-contains", help="Substring match on profession")
    p_tb.add_argument("--has-referral", choices=["yes", "no", "either"], default="either")
    p_tb.add_argument("--bucket", choices=list(targets.BUCKET_CHOICES), default="priority")
    p_tb.add_argument("--no-enrich", action="store_true",
                      help="Skip Craft DB enrichment (canton/profession will be blank)")
    p_tb.set_defaults(func=cmd_targets_build)

    # campaign create / list
    p_camp = sub.add_parser("campaign").add_subparsers(dest="subcmd", required=True)

    p_cc = p_camp.add_parser("create", help="Register a campaign + assign A/B/C variants")
    p_cc.add_argument("--name", required=True)
    p_cc.add_argument("--recipients", default=str(DEFAULT_RECIPIENTS_OUT))
    p_cc.add_argument("--emails", help="Comma-separated test emails (bypasses --recipients CSV)")
    p_cc.add_argument("--template-a", help=f"Default: {DEFAULT_TEMPLATE_MAP['A']}")
    p_cc.add_argument("--template-b", help=f"Default: {DEFAULT_TEMPLATE_MAP['B']}")
    p_cc.add_argument("--template-c", help=f"Default: {DEFAULT_TEMPLATE_MAP['C']}")
    p_cc.add_argument("--subject-a")
    p_cc.add_argument("--subject-b")
    p_cc.add_argument("--subject-c")
    p_cc.add_argument("--notes")
    p_cc.set_defaults(func=cmd_campaign_create)

    p_cl = p_camp.add_parser("list", help="List campaigns")
    p_cl.set_defaults(func=cmd_campaign_list)

    # render
    p_r = sub.add_parser("render", help="Dry-run render one message")
    p_r.add_argument("--campaign", required=True)
    p_r.add_argument("--email", help="Render against a real recipient in this campaign.")
    p_r.add_argument("--variant", choices=list(VARIANTS), help="Pick a variant for the fake preview recipient.")
    p_r.add_argument("--format", choices=["html", "txt"], default="html")
    p_r.set_defaults(func=cmd_render)

    # send
    p_s = sub.add_parser("send", help="Send (dry-run by default; add --live to actually send)")
    p_s.add_argument("--campaign", required=True)
    p_s.add_argument("--limit", type=int, help="Max recipients this run (default: MAILER_DAILY_CAP)")
    p_s.add_argument("--live", action="store_true", help="Actually send via Postmark")
    p_s.set_defaults(func=cmd_send)

    # stats
    p_st = sub.add_parser("stats", help="Show per-variant stats for a campaign")
    p_st.add_argument("--campaign", required=True)
    p_st.set_defaults(func=cmd_stats)

    # opt-outs
    p_oo = sub.add_parser("opt-outs").add_subparsers(dest="subcmd", required=True)
    p_ool = p_oo.add_parser("list")
    p_ool.set_defaults(func=cmd_opt_outs_list)
    p_ooa = p_oo.add_parser("add")
    p_ooa.add_argument("email")
    p_ooa.add_argument("--reason")
    p_ooa.set_defaults(func=cmd_opt_outs_add)
    p_oor = p_oo.add_parser("remove")
    p_oor.add_argument("email")
    p_oor.set_defaults(func=cmd_opt_outs_remove)

    # webhook
    p_w = sub.add_parser("webhook", help="Run Flask webhook/unsubscribe server")
    p_w.add_argument("--host", default="127.0.0.1")
    p_w.add_argument("--port", type=int, default=8080)
    p_w.set_defaults(func=cmd_webhook)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    _setup_logging()
    load_env()
    parser = build_parser()
    args = parser.parse_args(argv)
    _apply_db_override(args)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
