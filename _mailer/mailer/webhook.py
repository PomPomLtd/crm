"""Flask app exposing:

  GET  /                    — health check
  GET  /unsubscribe?t=...   — landing page with one-click confirm
  POST /unsubscribe         — One-Click List-Unsubscribe-Post target
  POST /webhook/postmark    — Postmark event webhook (opens, bounces, complaints)
  GET  /canvas              — preview harness: renders all 4 email templates
                              side-by-side against a fake recipient. Internal
                              use only (gated behind basic auth or an allow-list
                              in production).

The webhook secret (POSTMARK_WEBHOOK_SECRET) is compared against an
`X-Postmark-Token` header if present. Postmark itself does not sign webhook
payloads — the accepted practice is to use a long random path segment AND
optionally restrict by Postmark's published IPs.
"""

from __future__ import annotations

import hmac
import json
import logging
from typing import Any

from flask import Flask, Response, abort, jsonify, render_template_string, request

from . import db
from .config import Config, load_env
from .tokens import parse_unsubscribe_token
from .render import render as render_email, KNOWN_TEMPLATES

log = logging.getLogger("mailer.webhook")


UNSUB_LANDING_HTML = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<title>Abmeldung – Meditransfer</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body { font: 15px/1.55 -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
         margin: 0; padding: 48px 16px; background: #F8FAFC; color: #334155; }
  .card { max-width: 520px; margin: 0 auto; background: #fff; border-radius: 12px;
          padding: 36px; box-shadow: 0 1px 2px rgba(15,23,42,0.04); }
  h1 { margin: 0 0 12px; font-size: 22px; font-weight: 600; color: #0F172A; letter-spacing: -.2px; }
  p  { margin: 0 0 16px; }
  button { background:#165DFC; color:#fff; border:0; border-radius:999px;
           padding: 12px 24px; font-size:15px; font-weight:600; cursor:pointer; }
  .muted { color:#64748B; font-size: 13px; }
  .ok { color:#166534; font-weight:600; }
</style></head><body><div class="card">
{% if done %}
  <h1>Abgemeldet ✓</h1>
  <p class="ok">{{ email }} wurde aus unserer Versandliste entfernt.</p>
  <p class="muted">Sie erhalten keine weiteren E-Mails von Meditransfer. Bei Fragen: <a href="mailto:hello@meditransfer.ch">hello@meditransfer.ch</a>.</p>
{% elif error %}
  <h1>Ungültiger Link</h1>
  <p>Dieser Abmeldelink ist abgelaufen oder fehlerhaft.</p>
  <p class="muted">Bitte kontaktieren Sie uns direkt: <a href="mailto:hello@meditransfer.ch">hello@meditransfer.ch</a>.</p>
{% else %}
  <h1>Wirklich abmelden?</h1>
  <p>Sie sind dabei, <strong>{{ email }}</strong> aus der Meditransfer-Kontaktliste zu entfernen.</p>
  <form method="post" action="/unsubscribe">
    <input type="hidden" name="t" value="{{ token }}">
    <button type="submit">Abmelden</button>
  </form>
  <p class="muted" style="margin-top: 24px;">Pom Pom GmbH · Kalkbreitestrasse 6 · 8003 Zürich · hello@meditransfer.ch</p>
{% endif %}
</div></body></html>
"""


DASHBOARD_INDEX_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Mailer · campaigns</title>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  body { font: 14px/1.5 'Geist',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;
         margin: 0; padding: 32px; background: #F8FAFC; color: #334155; }
  h1 { margin: 0 0 4px; font-size: 24px; font-weight: 600; color: #0F172A; letter-spacing: -.3px; }
  .sub { color: #64748B; margin: 0 0 24px; font-size: 13px; }
  table { width: 100%; max-width: 1100px; border-collapse: collapse; background: #fff;
          border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(15,23,42,0.05); }
  th, td { padding: 12px 14px; text-align: left; border-bottom: 1px solid #F1F5F9; font-size: 13px; }
  th { background: #F8FAFC; font-weight: 600; color: #475569; font-size: 11px;
       letter-spacing: 0.6px; text-transform: uppercase; }
  tr:last-child td { border-bottom: 0; }
  tr:hover td { background: #F8FAFC; }
  td.num { text-align: right; font-variant-numeric: tabular-nums; color: #0F172A; }
  td.muted { color: #94A3B8; }
  a { color: #165DFC; text-decoration: none; font-weight: 500; }
  a:hover { text-decoration: underline; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 999px;
           font-size: 11px; font-weight: 500; background: #EFF4FF; color: #165DFC; }
  .empty { padding: 48px 0; text-align: center; color: #94A3B8; }
</style></head><body>
<h1>Campaigns</h1>
<p class="sub">{{ campaigns | length }} campaign{% if campaigns|length != 1 %}s{% endif %}.</p>
{% if not campaigns %}
  <div class="empty">No campaigns yet. Create one with <code>send_mailer.py campaign create</code>.</div>
{% else %}
<table>
  <thead><tr>
    <th>#</th><th>Name</th><th>Created</th><th>Templates (A/B/C)</th>
    <th class="num">Recipients</th><th class="num">Sent</th><th class="num">Opened</th><th class="num">Clicked</th><th class="num">Conv.</th><th class="num">Open%</th><th class="num">CTR</th><th class="num">Conv%</th>
  </tr></thead>
  <tbody>
  {% for c in campaigns %}
  <tr>
    <td class="muted">{{ c.id }}</td>
    <td><a href="/dashboard/c/{{ c.id }}">{{ c.name }}</a></td>
    <td class="muted">{{ c.created_at[:10] }}</td>
    <td class="muted" style="font-size:12px;">{{ c.template_a }} / {{ c.template_b }} / {{ c.template_c }}</td>
    <td class="num">{{ c.recipients }}</td>
    <td class="num">{{ c.sent }}</td>
    <td class="num">{{ c.opened }}</td>
    <td class="num">{{ c.clicked }}</td>
    <td class="num">{{ c.converted }}</td>
    <td class="num">{% if c.sent %}{{ "%.1f"|format(100.0 * c.opened / c.sent) }}%{% else %}–{% endif %}</td>
    <td class="num">{% if c.sent %}{{ "%.1f"|format(100.0 * c.clicked / c.sent) }}%{% else %}–{% endif %}</td>
    <td class="num">{% if c.sent %}{{ "%.1f"|format(100.0 * c.converted / c.sent) }}%{% else %}–{% endif %}</td>
  </tr>
  {% endfor %}
  </tbody>
</table>
{% endif %}
</body></html>
"""


DASHBOARD_CAMPAIGN_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{{ campaign.name }} · mailer</title>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  body { font: 14px/1.5 'Geist',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;
         margin: 0; padding: 32px; background: #F8FAFC; color: #334155; }
  .crumbs { font-size: 12px; color: #64748B; margin-bottom: 8px; }
  .crumbs a { color: #165DFC; text-decoration: none; }
  h1 { margin: 0 0 4px; font-size: 26px; font-weight: 600; color: #0F172A; letter-spacing: -.3px; }
  .sub { color: #64748B; margin: 0 0 28px; font-size: 13px; }
  h2 { margin: 32px 0 12px; font-size: 14px; font-weight: 600; color: #0F172A;
       letter-spacing: 0.6px; text-transform: uppercase; }
  .cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;
           max-width: 1100px; }
  .card { background: #fff; border-radius: 10px; padding: 20px;
          box-shadow: 0 1px 3px rgba(15,23,42,0.05); }
  .card .label { font-size: 11px; font-weight: 600; letter-spacing: 1.2px;
                 text-transform: uppercase; color: #165DFC; margin-bottom: 8px; }
  .card .template { font-size: 12px; color: #94A3B8; margin-bottom: 16px;
                    font-family: 'Geist Mono','Courier New',monospace; }
  .card .row { display: flex; justify-content: space-between; padding: 4px 0;
               font-size: 13px; }
  .card .row .k { color: #64748B; }
  .card .row .v { font-weight: 600; color: #0F172A; font-variant-numeric: tabular-nums; }
  .card .pct { background: #EFF4FF; padding: 2px 8px; border-radius: 999px;
               font-size: 11px; color: #165DFC; margin-left: 6px; }
  table { width: 100%; max-width: 1100px; border-collapse: collapse; background: #fff;
          border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(15,23,42,0.05); }
  th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #F1F5F9;
           font-size: 13px; }
  th { background: #F8FAFC; font-weight: 600; color: #475569; font-size: 11px;
       letter-spacing: 0.6px; text-transform: uppercase; }
  tr:last-child td { border-bottom: 0; }
  td.num { text-align: right; font-variant-numeric: tabular-nums; color: #0F172A; }
  td.muted { color: #94A3B8; }
  td.email { font-family: 'Geist Mono','Courier New',monospace; font-size: 12px; }
  td.url { font-family: 'Geist Mono','Courier New',monospace; font-size: 11px;
           color: #475569; max-width: 480px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .pill { display: inline-block; padding: 1px 8px; border-radius: 999px;
          font-size: 11px; font-weight: 600; }
  .pill.A { background: #EFF4FF; color: #165DFC; }
  .pill.B { background: #FDF4FF; color: #A21CAF; }
  .pill.C { background: #F0FDF4; color: #15803D; }
  .pill.sent { background: #F0FDF4; color: #15803D; }
  .pill.failed { background: #FEF2F2; color: #B91C1C; }
  .pill.dry_run { background: #FEF3C7; color: #92400E; }
  .pill.pending { background: #F1F5F9; color: #64748B; }
  .pill.opt { background: #FEF2F2; color: #B91C1C; }
  .pill.bounce { background: #FFEDD5; color: #C2410C; }
  .empty { padding: 48px 0; text-align: center; color: #94A3B8; }
</style></head><body>
<div class="crumbs"><a href="/dashboard">Campaigns</a> &rsaquo; {{ campaign.name }}</div>
<h1>{{ campaign.name }}</h1>
<p class="sub">Created {{ campaign.created_at }} &middot; {{ recipients|length }} recipient{% if recipients|length != 1 %}s{% endif %}.</p>

<div class="cards">
  {% for v in variants %}
  {% set s = stats.get(v, {}) %}
  {% set total = (s.get('total') or 0) | int %}
  {% set sent = (s.get('sent') or 0) | int %}
  {% set opened = (s.get('opened') or 0) | int %}
  {% set clicked = (s.get('clicked') or 0) | int %}
  {% set converted = (s.get('converted') or 0) | int %}
  {% set value = (s.get('conversion_value_cents') or 0) | int %}
  {% set bounced = (s.get('bounced') or 0) | int %}
  {% set unsub = (s.get('unsubscribed') or 0) | int %}
  {% set failed = (s.get('failed') or 0) | int %}
  <div class="card">
    <div class="label">Variant {{ v }}</div>
    <div class="template">{{ campaign['template_' ~ v.lower()] }}</div>
    <div class="row"><span class="k">Recipients</span><span class="v">{{ total }}</span></div>
    <div class="row"><span class="k">Sent</span><span class="v">{{ sent }}</span></div>
    <div class="row"><span class="k">Opened</span><span class="v">{{ opened }}{% if sent %}<span class="pct">{{ "%.1f"|format(100.0 * opened / sent) }}%</span>{% endif %}</span></div>
    <div class="row"><span class="k">Clicked</span><span class="v">{{ clicked }}{% if sent %}<span class="pct">{{ "%.1f"|format(100.0 * clicked / sent) }}%</span>{% endif %}</span></div>
    <div class="row"><span class="k">Converted</span><span class="v">{{ converted }}{% if sent %}<span class="pct">{{ "%.1f"|format(100.0 * converted / sent) }}%</span>{% endif %}</span></div>
    {% if value %}<div class="row"><span class="k">Revenue</span><span class="v">CHF {{ "%.2f"|format(value / 100.0) }}</span></div>{% endif %}
    <div class="row"><span class="k">Bounced</span><span class="v">{{ bounced }}</span></div>
    <div class="row"><span class="k">Unsubscribed</span><span class="v">{{ unsub }}</span></div>
    {% if failed %}<div class="row"><span class="k">Failed</span><span class="v">{{ failed }}</span></div>{% endif %}
  </div>
  {% endfor %}
</div>

<h2>Recent conversions</h2>
{% if not conversions_recent %}
  <div class="empty" style="background:#fff; border-radius:10px;">No conversions tracked yet.</div>
{% else %}
<table>
  <thead><tr><th>When</th><th>Variant</th><th>Email</th><th>Type</th><th class="num">Value</th><th>UTM content</th></tr></thead>
  <tbody>
  {% for c in conversions_recent %}
  <tr>
    <td class="muted" style="font-size:11px;">{{ c.received_at[:16].replace('T',' ') }}</td>
    <td>{% if c.variant %}<span class="pill {{ c.variant }}">{{ c.variant }}</span>{% else %}<span class="muted">–</span>{% endif %}</td>
    <td class="email">{{ c.email or '–' }}</td>
    <td>{{ c.conversion_type or '–' }}</td>
    <td class="num">{% if c.value_cents %}CHF {{ "%.2f"|format(c.value_cents / 100.0) }}{% else %}–{% endif %}</td>
    <td class="muted" style="font-size:11px;">{{ c.utm_content or '–' }}</td>
  </tr>
  {% endfor %}
  </tbody>
</table>
{% endif %}

<h2>Top clicked links</h2>
{% if not top_links %}
  <div class="empty" style="background:#fff; border-radius:10px;">No clicks yet.</div>
{% else %}
<table>
  <thead><tr><th>URL</th><th class="num">Unique clickers</th><th class="num">Total clicks</th></tr></thead>
  <tbody>
  {% for link in top_links %}
  <tr>
    <td class="url" title="{{ link.url }}"><a href="{{ link.url }}">{{ link.url }}</a></td>
    <td class="num">{{ link.unique_clickers }}</td>
    <td class="num">{{ link.total_clicks }}</td>
  </tr>
  {% endfor %}
  </tbody>
</table>
{% endif %}

<h2>Recipients</h2>
<table>
  <thead><tr>
    <th>Variant</th><th>Email</th><th>Section</th><th>Status</th>
    <th class="num">Sent</th><th class="num">Opens</th><th class="num">Clicks</th>
    <th class="num">First open</th><th>Last click URL</th><th>Flags</th>
  </tr></thead>
  <tbody>
  {% for r in recipients %}
  <tr>
    <td><span class="pill {{ r.variant }}">{{ r.variant }}</span></td>
    <td class="email">{{ r.email }}</td>
    <td class="muted">{{ r.section or '–' }}</td>
    <td>{% if r.status %}<span class="pill {{ r.status }}">{{ r.status }}</span>{% else %}<span class="pill pending">pending</span>{% endif %}</td>
    <td class="muted" style="font-size:11px;">{{ (r.sent_at or '')[:16].replace('T',' ') or '–' }}</td>
    <td class="num">{{ r.open_count or 0 }}</td>
    <td class="num">{{ r.click_count or 0 }}</td>
    <td class="muted" style="font-size:11px;">{{ (r.first_open or '')[:16].replace('T',' ') or '–' }}</td>
    <td class="url" title="{{ r.last_click_url or '' }}">{{ r.last_click_url or '–' }}</td>
    <td>
      {% if r.opted_out %}<span class="pill opt">unsub</span>{% endif %}
      {% if r.bounce_count and r.bounce_count > 0 %}<span class="pill bounce">bounce</span>{% endif %}
    </td>
  </tr>
  {% endfor %}
  </tbody>
</table>

</body></html>
"""


CANVAS_HTML = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<title>Meditransfer · Email Canvas</title>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  html,body { margin:0; padding:0; background:#f0eee9; font-family:'Geist',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif; }
  .intro { position:fixed; top:20px; left:20px; z-index:10; background:#fff; border-radius:10px; padding:14px 18px;
           box-shadow:0 4px 16px rgba(0,0,0,.08); max-width:320px; font-size:12px; line-height:1.5; color:#334155; }
  .intro h1 { margin:0 0 6px; font-size:14px; font-weight:600; color:#0F172A; }
  .frame-label { position:absolute; bottom:100%; left:0; padding-bottom:10px; font-size:12px; font-weight:500; color:rgba(60,50,40,.7); white-space:nowrap; }
  .frame-label .num { display:inline-block; width:22px; height:22px; line-height:22px; text-align:center; background:#0F172A; color:#fff; border-radius:6px; font-family:'Courier New',monospace; font-size:11px; margin-right:8px; vertical-align:middle; }
  .frame-label .sub { color:rgba(60,50,40,.5); margin-left:8px; font-weight:400; }
  .artboard { position:relative; flex-shrink:0; }
  .frame { background:#F8FAFC; border-radius:12px; box-shadow:0 1px 3px rgba(0,0,0,.08), 0 4px 20px rgba(0,0,0,.06); overflow:hidden; }
  iframe { border:0; display:block; width:640px; height:1360px; background:#F8FAFC; }
  .tag { display:inline-block; padding:2px 8px; border-radius:999px; font-size:10px; font-weight:600; letter-spacing:.4px; text-transform:uppercase; vertical-align:middle; margin-left:8px; }
  .tag.rec { background:#165DFC; color:#fff; }
  .tag.alt { background:#E2E8F0; color:#334155; }
</style></head><body>
<div class="intro">
  <h1>Meditransfer · Preview Canvas</h1>
  4 email templates rendered against a fake recipient. Variants A/B/C are picked
  from these at campaign-creation time.
</div>
<div style="padding: 140px 80px 80px;">
  <div style="display:flex; gap:80px; align-items:flex-start; width:max-content;">
    {% for item in items %}
    <div class="artboard">
      <div class="frame-label">
        <span class="num">{{ item.num }}</span>{{ item.label }}
        <span class="sub">{{ item.sub }}</span>
        <span class="tag {{ 'rec' if item.rec else 'alt' }}">{{ item.tag }}</span>
      </div>
      <div class="frame"><iframe src="/canvas/preview/{{ item.stem }}" title="{{ item.label }}"></iframe></div>
    </div>
    {% endfor %}
  </div>
</div>
</body></html>
"""


CANVAS_ITEMS = [
    {"stem": "01-der-brief", "num": "01", "label": "Der Brief",
     "sub": "Founder letter · plain-text feel", "tag": "Recommended for cold", "rec": True},
    {"stem": "02-hero-cta", "num": "02", "label": "Hero + CTA",
     "sub": "Classic branded, closest to homepage", "tag": "Brand awareness", "rec": False},
    {"stem": "03-stunden-zu-minuten", "num": "03", "label": "Stunden → Minuten",
     "sub": "Heute vs. mit Meditransfer · positive framing", "tag": "Benefits-forward", "rec": False},
    {"stem": "04-bento-benefits", "num": "04", "label": "Bento Benefits",
     "sub": "4-card grid · nDSG & Swiss angle", "tag": "Most visual", "rec": False},
]


PROTECTED_PREFIXES = ("/dashboard", "/canvas")


def _check_basic_auth(req, user: str, password: str) -> bool:
    auth = req.authorization
    if not auth or auth.type != "basic":
        return False
    return (
        hmac.compare_digest((auth.username or ""), user)
        and hmac.compare_digest((auth.password or ""), password)
    )


def create_app(config: Config) -> Flask:
    app = Flask(__name__)
    db.init_schema(config.db_path)

    @app.before_request
    def _guard_protected_routes():
        path = request.path or ""
        if not path.startswith(PROTECTED_PREFIXES):
            return None
        if not config.dashboard_user or not config.dashboard_pass:
            # Auth not configured → don't reveal that these routes exist.
            abort(404)
        if not _check_basic_auth(request, config.dashboard_user, config.dashboard_pass):
            return Response(
                "Authentication required.\n",
                401,
                {"WWW-Authenticate": 'Basic realm="meditransfer-mailer"'},
            )
        return None

    @app.route("/", methods=["GET"])
    def index() -> Response:
        return Response("Meditransfer mailer: ok\n", mimetype="text/plain")

    @app.route("/unsubscribe", methods=["GET"])
    def unsubscribe_get() -> Any:
        token = request.args.get("t", "")
        parsed = parse_unsubscribe_token(config.token_secret, token)
        if not parsed:
            return render_template_string(UNSUB_LANDING_HTML, error=True)
        email, _campaign_id = parsed
        return render_template_string(
            UNSUB_LANDING_HTML, token=token, email=email, done=False
        )

    @app.route("/unsubscribe", methods=["POST"])
    def unsubscribe_post() -> Any:
        token = request.form.get("t") or request.args.get("t", "")
        if not token and request.is_json:
            token = (request.get_json(silent=True) or {}).get("t", "")
        parsed = parse_unsubscribe_token(config.token_secret, token)
        if not parsed:
            if _is_one_click(request):
                return Response(status=400)
            return render_template_string(UNSUB_LANDING_HTML, error=True)

        email, campaign_id = parsed
        with db.connect(config.db_path) as conn:
            db.add_opt_out(conn, email=email, reason="user_unsubscribe", source="web")
        log.info("opt_out: %s via campaign=%s", email, campaign_id)

        if _is_one_click(request):
            return Response(status=200)
        return render_template_string(
            UNSUB_LANDING_HTML, email=email, done=True
        )

    @app.route("/api/conversion", methods=["POST"])
    def conversion_endpoint() -> Any:
        """Called by meditransfer.ch when a conversion (signup, payment, etc.) happens.

        Auth: X-Conversion-Token must match MAILER_CONVERSION_TOKEN.
        Body (JSON): {
          "utm_campaign": "test-06",        # campaign name (preferred)
          "utm_content": "01-der-brief",    # template stem (preferred)
          "email": "user@clinic.ch",        # optional but enables per-recipient attribution
          "type": "signup",                 # free-form: signup / trial_started / paid / etc.
          "value_cents": 4900               # optional revenue value in cents
        }

        Attribution priority:
          1. utm_campaign → campaigns.name → campaign_id (so we know the send)
          2. email + campaign_id → recipients row → recipient_id + variant
          3. utm_content as fallback variant identifier when email not given

        Always returns 200 even if attribution fails — the conversion is still
        recorded so we don't lose the data, just unlinked.
        """
        if not config.conversion_token:
            abort(404)
        supplied = request.headers.get("X-Conversion-Token", "")
        if not hmac.compare_digest(supplied, config.conversion_token):
            abort(401)

        payload = request.get_json(silent=True) or {}
        utm_campaign = (payload.get("utm_campaign") or "").strip() or None
        utm_content = (payload.get("utm_content") or "").strip() or None
        email = (payload.get("email") or "").strip().lower() or None
        conversion_type = (payload.get("type") or "").strip() or None
        value_cents = payload.get("value_cents")
        if value_cents is not None:
            try:
                value_cents = int(value_cents)
            except (TypeError, ValueError):
                value_cents = None

        with db.connect(config.db_path) as conn:
            campaign_id = None
            recipient_id = None
            variant = None

            if utm_campaign:
                camp = db.find_campaign_by_name(conn, utm_campaign)
                if camp:
                    campaign_id = int(camp["id"])

            if campaign_id and email:
                rec = db.find_recipient_for_conversion(conn, campaign_id=campaign_id, email=email)
                if rec:
                    recipient_id = int(rec["id"])
                    variant = rec["variant"]

            # Fallback: derive variant from utm_content if we didn't find a recipient
            if variant is None and utm_content and campaign_id:
                camp = conn.execute(
                    "SELECT template_a, template_b, template_c FROM campaigns WHERE id = ?",
                    (campaign_id,),
                ).fetchone()
                if camp:
                    if utm_content == camp["template_a"]: variant = "A"
                    elif utm_content == camp["template_b"]: variant = "B"
                    elif utm_content == camp["template_c"]: variant = "C"

            cid = db.record_conversion(
                conn,
                campaign_id=campaign_id,
                recipient_id=recipient_id,
                variant=variant,
                utm_campaign=utm_campaign,
                utm_content=utm_content,
                email=email,
                conversion_type=conversion_type,
                value_cents=value_cents,
                raw_json=json.dumps(payload, ensure_ascii=False),
            )

        return jsonify({
            "ok": True,
            "id": cid,
            "attributed": {
                "campaign_id": campaign_id,
                "recipient_id": recipient_id,
                "variant": variant,
            },
        })

    @app.route("/webhook/postmark", methods=["POST"])
    def postmark_webhook() -> Any:
        if config.postmark_webhook_secret:
            supplied = request.headers.get("X-Postmark-Token", "")
            if not hmac.compare_digest(supplied, config.postmark_webhook_secret):
                abort(401)

        payload = request.get_json(silent=True) or {}
        record_type = payload.get("RecordType", "")
        with db.connect(config.db_path) as conn:
            _handle_event(conn, record_type, payload)
        return jsonify({"ok": True})

    @app.route("/dashboard", methods=["GET"])
    def dashboard_index() -> Any:
        with db.connect(config.db_path) as conn:
            campaigns = conn.execute(
                """SELECT c.id, c.name, c.created_at, c.template_a, c.template_b, c.template_c,
                          (SELECT COUNT(*) FROM recipients r WHERE r.campaign_id = c.id) AS recipients,
                          (SELECT COUNT(*) FROM sends s WHERE s.campaign_id = c.id AND s.status = 'sent') AS sent,
                          (SELECT COUNT(DISTINCT s.id) FROM sends s
                             JOIN opens o ON o.send_id = s.id
                             WHERE s.campaign_id = c.id) AS opened,
                          (SELECT COUNT(DISTINCT s.id) FROM sends s
                             JOIN clicks ck ON ck.send_id = s.id
                             WHERE s.campaign_id = c.id) AS clicked,
                          (SELECT COUNT(*) FROM conversions cv WHERE cv.campaign_id = c.id) AS converted
                   FROM campaigns c
                   ORDER BY c.id DESC"""
            ).fetchall()
        return render_template_string(DASHBOARD_INDEX_HTML, campaigns=campaigns)

    @app.route("/dashboard/c/<int:campaign_id>", methods=["GET"])
    def dashboard_campaign(campaign_id: int) -> Any:
        with db.connect(config.db_path) as conn:
            campaign = conn.execute(
                "SELECT * FROM campaigns WHERE id = ?", (campaign_id,)
            ).fetchone()
            if campaign is None:
                abort(404)
            stats = db.campaign_stats(conn, campaign_id)
            recipients = conn.execute(
                """SELECT r.id, r.email, r.variant, r.section, r.canton, r.url,
                          s.status, s.sent_at, s.error,
                          (SELECT MIN(o.received_at) FROM opens o WHERE o.send_id = s.id) AS first_open,
                          (SELECT COUNT(*) FROM opens o WHERE o.send_id = s.id) AS open_count,
                          (SELECT COUNT(*) FROM clicks ck WHERE ck.send_id = s.id) AS click_count,
                          (SELECT MAX(ck.url) FROM clicks ck WHERE ck.send_id = s.id) AS last_click_url,
                          (SELECT COUNT(*) FROM bounces b WHERE b.send_id = s.id) AS bounce_count,
                          (SELECT 1 FROM opt_outs oo WHERE LOWER(oo.email) = LOWER(r.email)) AS opted_out
                   FROM recipients r
                   LEFT JOIN sends s ON s.recipient_id = r.id
                   WHERE r.campaign_id = ?
                   ORDER BY r.variant, r.email""",
                (campaign_id,),
            ).fetchall()
            conversions_recent = conn.execute(
                """SELECT received_at, variant, email, conversion_type, value_cents,
                          utm_content, recipient_id
                   FROM conversions
                   WHERE campaign_id = ?
                   ORDER BY received_at DESC
                   LIMIT 50""",
                (campaign_id,),
            ).fetchall()
            top_links = conn.execute(
                """SELECT ck.url, COUNT(DISTINCT s.recipient_id) AS unique_clickers, COUNT(*) AS total_clicks
                   FROM clicks ck
                   JOIN sends s ON s.id = ck.send_id
                   WHERE s.campaign_id = ?
                   GROUP BY ck.url
                   ORDER BY unique_clickers DESC, total_clicks DESC
                   LIMIT 20""",
                (campaign_id,),
            ).fetchall()
        return render_template_string(
            DASHBOARD_CAMPAIGN_HTML,
            campaign=campaign,
            stats=stats,
            recipients=recipients,
            top_links=top_links,
            conversions_recent=conversions_recent,
            variants=("A", "B", "C"),
        )

    @app.route("/canvas", methods=["GET"])
    def canvas() -> Any:
        return render_template_string(CANVAS_HTML, items=CANVAS_ITEMS)

    @app.route("/canvas/preview/<stem>", methods=["GET"])
    def canvas_preview(stem: str) -> Any:
        if stem not in KNOWN_TEMPLATES:
            abort(404)
        fake_recipient = {
            "email": "preview@example.ch",
            "title": "Praxis Muster",
            "url": "https://praxis-muster.ch",
            "canton": "ZH",
            "section": "clinics",
            "profession": "Innere Medizin",
        }
        rendered = render_email(
            template_name=stem,
            subject="Zuweisungen digital empfangen – Meditransfer",
            recipient=fake_recipient,
            campaign_id=0,
            base_url=config.base_url,
            token_secret=config.token_secret,
        )
        return Response(rendered.html, mimetype="text/html; charset=utf-8")

    return app


def _is_one_click(req) -> bool:
    """True if this looks like an RFC 8058 One-Click unsubscribe POST."""
    ct = (req.headers.get("Content-Type") or "").lower()
    body = req.get_data(as_text=True) or ""
    return "application/x-www-form-urlencoded" in ct and "List-Unsubscribe=One-Click" in body


def _handle_event(conn, record_type: str, payload: dict) -> None:
    """Route a Postmark webhook event into the right table."""
    message_id = payload.get("MessageID") or payload.get("ID") or ""
    email = (payload.get("Recipient") or payload.get("Email") or "").lower()
    raw = json.dumps(payload, ensure_ascii=False)

    send = db.send_by_message_id(conn, message_id) if message_id else None
    send_id = int(send["id"]) if send else None

    if record_type == "Open":
        if send_id is None:
            return
        ua = (payload.get("UserAgent") or "")
        ip = (payload.get("Geo") or {}).get("IP") or payload.get("IP") or ""
        platform = (payload.get("Platform") or (payload.get("Client") or {}).get("Family") or "")
        db.record_open(conn, send_id=send_id, user_agent=ua, ip=ip, platform=platform, raw_json=raw)
    elif record_type == "Click":
        if send_id is None:
            return
        ua = (payload.get("UserAgent") or "")
        ip = (payload.get("Geo") or {}).get("IP") or payload.get("IP") or ""
        url = payload.get("OriginalLink") or ""
        click_location = payload.get("ClickLocation") or ""
        db.record_click(conn, send_id=send_id, url=url, click_location=click_location,
                        user_agent=ua, ip=ip, raw_json=raw)
    elif record_type == "Bounce":
        bounce_type = payload.get("Type") or payload.get("TypeCode")
        inactive = bool(payload.get("Inactive"))
        db.record_bounce(conn, send_id=send_id, email=email, bounce_type=str(bounce_type) if bounce_type else None, inactive=inactive, raw_json=raw)
        if inactive and email:
            db.add_opt_out(conn, email=email, reason=f"bounce:{bounce_type}", source="postmark_webhook")
    elif record_type == "SpamComplaint":
        db.record_bounce(conn, send_id=send_id, email=email, bounce_type="SpamComplaint", inactive=True, raw_json=raw)
        if email:
            db.add_opt_out(conn, email=email, reason="spam_complaint", source="postmark_webhook")
    elif record_type == "SubscriptionChange":
        # Postmark's native subscription management — sync to our suppression
        suppress = bool(payload.get("SuppressSending"))
        if suppress and email:
            db.add_opt_out(conn, email=email, reason="postmark_subscription_change", source="postmark_webhook")
    # Deliveries + link-clicks: we don't track them in the MVP.


def run(host: str = "0.0.0.0", port: int = 8080) -> None:
    load_env()
    app = create_app(Config.from_env())
    app.run(host=host, port=port, debug=False)
