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
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        fontFamily: { sans: ['Geist','-apple-system','Segoe UI','Helvetica','Arial','sans-serif'] },
        colors: {
          brand: { DEFAULT: '#165DFC', light: '#EFF4FF', dark: '#0A47C7' },
          slate: { 950: '#0F172A' },
        },
      },
    },
  };
</script>
<style>
  body { font-family: 'Geist', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; }
  .kpi-value { font-variant-numeric: tabular-nums; }
</style>
</head><body class="bg-slate-50 text-slate-700 min-h-screen">

<header class="max-w-7xl mx-auto px-4 sm:px-8 pt-8 pb-4">
  <h1 class="text-2xl font-semibold text-slate-950 tracking-tight">Campaigns</h1>
  <p class="text-slate-500 text-sm mt-1">
    {{ summary.campaigns }} visible campaign{% if summary.campaigns != 1 %}s{% endif %}
    &middot; test &amp; preview campaigns hidden
  </p>
</header>

<!-- All-time KPI strip -->
<section class="max-w-7xl mx-auto px-4 sm:px-8 pb-4">
  <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
    {% set open_rate = (100.0 * summary.opened / summary.sent) if summary.sent else 0 %}
    {% set ctr      = (100.0 * summary.clicked / summary.sent) if summary.sent else 0 %}
    <div class="bg-white rounded-xl p-4 shadow-sm ring-1 ring-slate-200/60">
      <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">Total sent</div>
      <div class="kpi-value text-3xl font-semibold text-slate-950 mt-1">{{ summary.sent }}</div>
    </div>
    <div class="bg-white rounded-xl p-4 shadow-sm ring-1 ring-slate-200/60">
      <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">Delivered</div>
      <div class="kpi-value text-3xl font-semibold text-slate-950 mt-1">{{ summary.delivered }}</div>
      <div class="text-[11px] text-slate-500 mt-0.5">
        {% if summary.sent %}{{ "%.1f"|format(100.0 * summary.delivered / summary.sent) }}% of sent{% else %}–{% endif %}
      </div>
    </div>
    <div class="bg-white rounded-xl p-4 shadow-sm ring-1 ring-slate-200/60">
      <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">Open rate</div>
      <div class="kpi-value text-3xl font-semibold text-brand mt-1">{{ "%.1f"|format(open_rate) }}%</div>
      <div class="text-[11px] text-slate-500 mt-0.5">{{ summary.opened }} opens</div>
    </div>
    <div class="bg-white rounded-xl p-4 shadow-sm ring-1 ring-slate-200/60">
      <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">Real CTR</div>
      <div class="kpi-value text-3xl font-semibold text-brand mt-1">{{ "%.1f"|format(ctr) }}%</div>
      <div class="text-[11px] text-slate-500 mt-0.5">{{ summary.clicked }} human clicks</div>
    </div>
    <div class="bg-white rounded-xl p-4 shadow-sm ring-1 ring-slate-200/60 col-span-2 sm:col-span-1">
      <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">Opt-outs</div>
      <div class="kpi-value text-3xl font-semibold text-slate-950 mt-1">{{ summary.opt_outs }}</div>
      <div class="text-[11px] text-slate-500 mt-0.5">global suppressions</div>
    </div>
  </div>
</section>

<!-- Campaign cards -->
<section class="max-w-7xl mx-auto px-4 sm:px-8 pb-12">
  {% if not campaigns %}
    <div class="bg-white rounded-xl p-12 text-center text-slate-400 shadow-sm ring-1 ring-slate-200/60">
      No campaigns yet. Create one with
      <code class="font-mono text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded">send_mailer.py campaign create</code>.
    </div>
  {% else %}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    {% for c in campaigns %}
      {% set open_rate = (100.0 * c.opened / c.sent) if c.sent else 0 %}
      {% set ctr       = (100.0 * c.clicked / c.sent) if c.sent else 0 %}
      <a href="/dashboard/c/{{ c.id }}" class="block bg-white rounded-xl p-5 shadow-sm ring-1 ring-slate-200/60 hover:ring-brand/30 hover:shadow-md transition">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0 flex-1">
            <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-brand">Campaign #{{ c.id }}</div>
            <div class="text-base font-semibold text-slate-950 mt-0.5 truncate">{{ c.name }}</div>
            <div class="text-[11px] text-slate-400 mt-0.5">{{ c.created_at[:10] }}</div>
          </div>
          <div class="flex flex-col items-end gap-1 shrink-0">
            <span class="inline-flex items-center gap-1 text-[10px] font-mono text-slate-500">
              <span class="inline-block w-2 h-2 rounded-full bg-brand"></span>{{ c.template_a }}
            </span>
            <span class="inline-flex items-center gap-1 text-[10px] font-mono text-slate-500">
              <span class="inline-block w-2 h-2 rounded-full bg-fuchsia-500"></span>{{ c.template_b }}
            </span>
            <span class="inline-flex items-center gap-1 text-[10px] font-mono text-slate-500">
              <span class="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>{{ c.template_c }}
            </span>
          </div>
        </div>

        <div class="grid grid-cols-3 gap-3 mt-5">
          <div>
            <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">Sent</div>
            <div class="kpi-value text-xl font-semibold text-slate-950 mt-0.5">{{ c.sent }}</div>
          </div>
          <div>
            <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">Open</div>
            <div class="kpi-value text-xl font-semibold text-slate-950 mt-0.5">{{ "%.0f"|format(open_rate) }}%</div>
          </div>
          <div>
            <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">CTR</div>
            <div class="kpi-value text-xl font-semibold text-slate-950 mt-0.5">{{ "%.1f"|format(ctr) }}%</div>
          </div>
        </div>

        <div class="mt-4 h-10">
          <canvas data-sparkline='{{ c.sparkline | tojson }}' class="w-full h-full"></canvas>
        </div>
        <div class="text-[10px] text-slate-400 mt-1">Opens · last 7 days</div>
      </a>
    {% endfor %}
    </div>
  {% endif %}
</section>

<script>
  // Render sparkline on each campaign card
  document.querySelectorAll('canvas[data-sparkline]').forEach(el => {
    const data = JSON.parse(el.dataset.sparkline || '[]');
    new Chart(el, {
      type: 'line',
      data: {
        labels: data.map((_, i) => i),
        datasets: [{
          data,
          borderColor: '#165DFC',
          backgroundColor: 'rgba(22, 93, 252, 0.08)',
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0.35,
          fill: true,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        scales: {
          x: { display: false },
          y: { display: false, beginAtZero: true },
        },
        animation: false,
      },
    });
  });
</script>

</body></html>
"""


DASHBOARD_CAMPAIGN_HTML = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>{{ campaign.name }} · mailer</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js"></script>
<script>
  tailwind.config = {
    theme: { extend: {
      fontFamily: {
        sans: ['Geist','-apple-system','Segoe UI','Helvetica','Arial','sans-serif'],
        mono: ['Geist Mono','Courier New','monospace'],
      },
      colors: {
        brand: { DEFAULT: '#165DFC', light: '#EFF4FF', dark: '#0A47C7' },
      },
    }},
  };
</script>
<style>
  body { font-family: 'Geist', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; }
  .kpi-value { font-variant-numeric: tabular-nums; }
  [x-cloak] { display: none !important; }
  .chart-wrap { position: relative; }
</style>
</head>
<body class="bg-slate-50 text-slate-700 min-h-screen" x-data="{ tab: 'overview', variantFilter: 'all' }">

<!-- Breadcrumb + title -->
<header class="max-w-7xl mx-auto px-4 sm:px-8 pt-8 pb-4">
  <div class="text-xs text-slate-500 mb-2">
    <a href="/dashboard" class="text-brand hover:underline">Campaigns</a>
    <span class="mx-1.5 text-slate-300">&rsaquo;</span>
    <span class="text-slate-500">{{ campaign.name }}</span>
  </div>
  <h1 class="text-2xl md:text-3xl font-semibold text-slate-950 tracking-tight break-words">{{ campaign.name }}</h1>
  <p class="text-slate-500 text-sm mt-1">
    Created {{ campaign.created_at[:16].replace('T',' ') }} &middot; {{ recipients|length }} recipient{% if recipients|length != 1 %}s{% endif %}
    {% if campaign.notes %}<br><span class="italic text-slate-400">{{ campaign.notes }}</span>{% endif %}
  </p>
</header>

<!-- Hero KPIs -->
<section class="max-w-7xl mx-auto px-4 sm:px-8 pb-3">
  {% set tot_sent = funnel.sent %}
  {% set tot_delivered = funnel.delivered %}
  {% set tot_opened = funnel.opened %}
  {% set tot_clicked = funnel.clicked %}
  {% set tot_converted = funnel.converted %}
  {% set tot_bounced = tot_sent - tot_delivered %}
  {% set bounce_rate = (100.0 * tot_bounced / tot_sent) if tot_sent else 0 %}
  {% set unsub_total = 0 %}
  {% for v in variants %}{% set unsub_total = unsub_total + (stats.get(v, {}).get('unsubscribed') or 0) | int %}{% endfor %}
  {% set unsub_rate = (100.0 * unsub_total / tot_sent) if tot_sent else 0 %}
  <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
    <div class="bg-white rounded-xl p-4 shadow-sm ring-1 ring-slate-200/60">
      <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">Sent</div>
      <div class="kpi-value text-2xl sm:text-3xl font-semibold text-slate-950 mt-1">{{ tot_sent }}</div>
    </div>
    <div class="bg-white rounded-xl p-4 shadow-sm ring-1 ring-slate-200/60">
      <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">Delivered</div>
      <div class="kpi-value text-2xl sm:text-3xl font-semibold text-slate-950 mt-1">{{ tot_delivered }}</div>
      <div class="text-[11px] text-slate-500 mt-0.5">{% if tot_sent %}{{ "%.1f"|format(100.0 * tot_delivered / tot_sent) }}%{% else %}–{% endif %}</div>
    </div>
    <div class="bg-white rounded-xl p-4 shadow-sm ring-1 ring-slate-200/60">
      <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">Opened</div>
      <div class="kpi-value text-2xl sm:text-3xl font-semibold text-brand mt-1">{{ "%.1f"|format((100.0 * tot_opened / tot_sent) if tot_sent else 0) }}%</div>
      <div class="text-[11px] text-slate-500 mt-0.5">{{ tot_opened }} opens</div>
    </div>
    <div class="bg-white rounded-xl p-4 shadow-sm ring-1 ring-slate-200/60">
      <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">Clicked</div>
      <div class="kpi-value text-2xl sm:text-3xl font-semibold text-brand mt-1">{{ "%.1f"|format((100.0 * tot_clicked / tot_sent) if tot_sent else 0) }}%</div>
      <div class="text-[11px] text-slate-500 mt-0.5">{{ tot_clicked }} human</div>
    </div>
    <div class="bg-white rounded-xl p-4 shadow-sm ring-1 ring-slate-200/60">
      <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">Converted</div>
      <div class="kpi-value text-2xl sm:text-3xl font-semibold text-emerald-600 mt-1">{{ tot_converted }}</div>
      <div class="text-[11px] text-slate-500 mt-0.5">{% if tot_sent %}{{ "%.1f"|format(100.0 * tot_converted / tot_sent) }}%{% else %}–{% endif %}</div>
    </div>
    <div class="bg-white rounded-xl p-4 shadow-sm ring-1 ring-slate-200/60">
      <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">Unsub</div>
      {% set unsub_colour = 'text-slate-950' if unsub_rate < 3 else ('text-amber-600' if unsub_rate < 5 else 'text-rose-600') %}
      <div class="kpi-value text-2xl sm:text-3xl font-semibold {{ unsub_colour }} mt-1">{{ "%.1f"|format(unsub_rate) }}%</div>
      <div class="text-[11px] text-slate-500 mt-0.5">{{ unsub_total }} opt-outs</div>
    </div>
    <div class="bg-white rounded-xl p-4 shadow-sm ring-1 ring-slate-200/60">
      <div class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">Bounced</div>
      {% set bounce_colour = 'text-slate-950' if bounce_rate < 3 else ('text-amber-600' if bounce_rate < 5 else 'text-rose-600') %}
      <div class="kpi-value text-2xl sm:text-3xl font-semibold {{ bounce_colour }} mt-1">{{ "%.1f"|format(bounce_rate) }}%</div>
      <div class="text-[11px] text-slate-500 mt-0.5">{{ tot_bounced }} of {{ tot_sent }}</div>
    </div>
  </div>
</section>

<!-- Scanner noise callout -->
{% set scanner_total = 0 %}
{% for v in variants %}{% set scanner_total = scanner_total + (stats.get(v, {}).get('clicked_scanner') or 0) | int %}{% endfor %}
{% if scanner_total %}
<section class="max-w-7xl mx-auto px-4 sm:px-8 pb-3">
  <div class="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5 text-xs text-amber-900 flex items-start gap-2">
    <span class="font-semibold">⚠</span>
    <span>Filtered <strong>{{ scanner_total }}</strong> scanner clicks (corporate email security gateways — Proofpoint, MS Defender, Mimecast — walk every link in incoming mail). Real CTR above excludes these.</span>
  </div>
</section>
{% endif %}

<!-- Tabs -->
<nav class="max-w-7xl mx-auto px-4 sm:px-8 border-b border-slate-200 mt-2">
  <div class="flex gap-0 text-sm -mb-px">
    <button @click="tab = 'overview'" :class="tab === 'overview' ? 'text-brand border-brand' : 'text-slate-500 border-transparent hover:text-slate-900'" class="py-3 px-4 border-b-2 font-medium transition cursor-pointer">Overview</button>
    <button @click="tab = 'events'" :class="tab === 'events' ? 'text-brand border-brand' : 'text-slate-500 border-transparent hover:text-slate-900'" class="py-3 px-4 border-b-2 font-medium transition cursor-pointer">Events</button>
    <button @click="tab = 'recipients'" :class="tab === 'recipients' ? 'text-brand border-brand' : 'text-slate-500 border-transparent hover:text-slate-900'" class="py-3 px-4 border-b-2 font-medium transition cursor-pointer">Recipients</button>
  </div>
</nav>

<!-- OVERVIEW TAB -->
<section x-show="tab === 'overview'" x-cloak class="max-w-7xl mx-auto px-4 sm:px-8 py-6 space-y-5">

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
    <!-- Funnel -->
    <div class="bg-white rounded-xl p-5 shadow-sm ring-1 ring-slate-200/60">
      <h2 class="text-[11px] font-semibold tracking-[0.1em] uppercase text-slate-500">Funnel</h2>
      <p class="text-xs text-slate-400 mt-0.5 mb-4">From send to conversion · scanner clicks excluded.</p>
      <div class="chart-wrap" style="height:220px;"><canvas id="funnel-chart"></canvas></div>
    </div>
    <!-- Variant comparison -->
    <div class="bg-white rounded-xl p-5 shadow-sm ring-1 ring-slate-200/60">
      <h2 class="text-[11px] font-semibold tracking-[0.1em] uppercase text-slate-500">Variant comparison</h2>
      <p class="text-xs text-slate-400 mt-0.5 mb-4">Open %, CTR, Unsub %, Bounce % by template.</p>
      <div class="chart-wrap" style="height:220px;"><canvas id="variant-chart"></canvas></div>
    </div>
  </div>

  <!-- Per-variant cards -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    {% for v in variants %}
      {% set s = stats.get(v, {}) %}
      {% set total = (s.get('total') or 0) | int %}
      {% set sent = (s.get('sent') or 0) | int %}
      {% set opened = (s.get('opened') or 0) | int %}
      {% set clicked = (s.get('clicked') or 0) | int %}
      {% set clicked_scanner = (s.get('clicked_scanner') or 0) | int %}
      {% set converted = (s.get('converted') or 0) | int %}
      {% set value = (s.get('conversion_value_cents') or 0) | int %}
      {% set bounced = (s.get('bounced') or 0) | int %}
      {% set unsub = (s.get('unsubscribed') or 0) | int %}
      {% set failed = (s.get('failed') or 0) | int %}
      {% set dot = 'bg-brand' if v == 'A' else ('bg-fuchsia-500' if v == 'B' else 'bg-emerald-500') %}
      <div class="bg-white rounded-xl p-5 shadow-sm ring-1 ring-slate-200/60">
        <div class="flex items-center gap-2">
          <span class="inline-block w-2.5 h-2.5 rounded-full {{ dot }}"></span>
          <span class="text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-400">Variant {{ v }}</span>
        </div>
        <div class="font-mono text-xs text-slate-400 mt-1 break-all">{{ campaign['template_' ~ v.lower()] }}</div>
        <dl class="mt-4 divide-y divide-slate-100 text-sm">
          <div class="flex justify-between py-1.5"><dt class="text-slate-500">Recipients</dt><dd class="font-semibold text-slate-950 kpi-value">{{ total }}</dd></div>
          <div class="flex justify-between py-1.5"><dt class="text-slate-500">Sent</dt><dd class="font-semibold text-slate-950 kpi-value">{{ sent }}</dd></div>
          <div class="flex justify-between py-1.5 items-center"><dt class="text-slate-500">Opened</dt><dd class="font-semibold text-slate-950 kpi-value">{{ opened }}{% if sent %} <span class="text-[10px] font-medium text-brand bg-brand-light px-2 py-0.5 rounded-full ml-1">{{ "%.1f"|format(100.0 * opened / sent) }}%</span>{% endif %}</dd></div>
          <div class="flex justify-between py-1.5 items-center"><dt class="text-slate-500">Clicked</dt><dd class="font-semibold text-slate-950 kpi-value">{{ clicked }}{% if sent %} <span class="text-[10px] font-medium text-brand bg-brand-light px-2 py-0.5 rounded-full ml-1">{{ "%.1f"|format(100.0 * clicked / sent) }}%</span>{% endif %}</dd></div>
          {% if clicked_scanner %}<div class="flex justify-between py-1.5 items-center"><dt class="text-slate-400">Scanner clicks</dt><dd class="font-medium text-slate-400 kpi-value">{{ clicked_scanner }} <span class="text-[10px] font-medium text-amber-800 bg-amber-100 px-2 py-0.5 rounded-full ml-1">filtered</span></dd></div>{% endif %}
          <div class="flex justify-between py-1.5 items-center"><dt class="text-slate-500">Converted</dt><dd class="font-semibold text-slate-950 kpi-value">{{ converted }}{% if sent %} <span class="text-[10px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full ml-1">{{ "%.1f"|format(100.0 * converted / sent) }}%</span>{% endif %}</dd></div>
          {% if value %}<div class="flex justify-between py-1.5"><dt class="text-slate-500">Revenue</dt><dd class="font-semibold text-slate-950 kpi-value">CHF {{ "%.2f"|format(value / 100.0) }}</dd></div>{% endif %}
          <div class="flex justify-between py-1.5"><dt class="text-slate-500">Bounced</dt><dd class="font-semibold text-slate-950 kpi-value">{{ bounced }}</dd></div>
          <div class="flex justify-between py-1.5"><dt class="text-slate-500">Unsubscribed</dt><dd class="font-semibold text-slate-950 kpi-value">{{ unsub }}</dd></div>
          {% if failed %}<div class="flex justify-between py-1.5"><dt class="text-slate-500">Failed</dt><dd class="font-semibold text-rose-600 kpi-value">{{ failed }}</dd></div>{% endif %}
        </dl>
      </div>
    {% endfor %}
  </div>

</section>

<!-- EVENTS TAB -->
<section x-show="tab === 'events'" x-cloak class="max-w-7xl mx-auto px-4 sm:px-8 py-6 space-y-5">

  <!-- Timeline -->
  <div class="bg-white rounded-xl p-5 shadow-sm ring-1 ring-slate-200/60">
    <h2 class="text-[11px] font-semibold tracking-[0.1em] uppercase text-slate-500">Engagement timeline</h2>
    <p class="text-xs text-slate-400 mt-0.5 mb-4">Opens and human clicks per hour since the first send.</p>
    <div class="chart-wrap" style="height:260px;"><canvas id="timeline-chart"></canvas></div>
  </div>

  <!-- Top clicked links -->
  <div class="bg-white rounded-xl p-5 shadow-sm ring-1 ring-slate-200/60">
    <h2 class="text-[11px] font-semibold tracking-[0.1em] uppercase text-slate-500">Top clicked links</h2>
    <p class="text-xs text-slate-400 mt-0.5 mb-4">Footer links and scanner-flagged recipients excluded.</p>
    {% if not top_links %}
      <div class="text-sm text-slate-400 py-4">No human clicks yet.</div>
    {% else %}
      {% set max_clicks = top_links[0].total_clicks or 1 %}
      <div class="space-y-2">
      {% for link in top_links %}
        <div>
          <div class="flex items-center justify-between gap-3 text-xs">
            <a href="{{ link.url }}" class="font-mono text-slate-600 hover:text-brand truncate" title="{{ link.url }}">{{ link.url }}</a>
            <div class="text-slate-500 whitespace-nowrap shrink-0">
              <span class="font-semibold text-slate-950 kpi-value">{{ link.unique_clickers }}</span> clickers
              <span class="mx-1.5 text-slate-300">·</span>
              <span class="kpi-value">{{ link.total_clicks }}</span> clicks
            </div>
          </div>
          <div class="mt-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div class="h-full bg-brand rounded-full" style="width: {{ (100.0 * link.total_clicks / max_clicks) | round(1) }}%"></div>
          </div>
        </div>
      {% endfor %}
      </div>
    {% endif %}
  </div>

  <!-- Recent conversions -->
  <div class="bg-white rounded-xl shadow-sm ring-1 ring-slate-200/60 overflow-hidden">
    <div class="px-5 py-4 border-b border-slate-100">
      <h2 class="text-[11px] font-semibold tracking-[0.1em] uppercase text-slate-500">Recent conversions</h2>
    </div>
    {% if not conversions_recent %}
      <div class="p-8 text-center text-sm text-slate-400">No conversions tracked yet.</div>
    {% else %}
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-slate-50/80 text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-500">
          <tr>
            <th class="text-left px-5 py-3">When</th>
            <th class="text-left px-5 py-3">Variant</th>
            <th class="text-left px-5 py-3">Email</th>
            <th class="text-left px-5 py-3">Type</th>
            <th class="text-right px-5 py-3">Value</th>
            <th class="text-left px-5 py-3">UTM content</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          {% for c in conversions_recent %}
          <tr>
            <td class="px-5 py-3 text-xs text-slate-400 whitespace-nowrap">{{ c.received_at[:16].replace('T',' ') }}</td>
            <td class="px-5 py-3">{% if c.variant %}{% set dot = 'bg-brand' if c.variant == 'A' else ('bg-fuchsia-500' if c.variant == 'B' else 'bg-emerald-500') %}<span class="inline-flex items-center gap-1.5"><span class="inline-block w-2 h-2 rounded-full {{ dot }}"></span>{{ c.variant }}</span>{% else %}<span class="text-slate-300">–</span>{% endif %}</td>
            <td class="px-5 py-3 font-mono text-xs">{{ c.email or '–' }}</td>
            <td class="px-5 py-3 text-xs">{{ c.conversion_type or '–' }}</td>
            <td class="px-5 py-3 text-right kpi-value whitespace-nowrap">{% if c.value_cents %}CHF {{ "%.2f"|format(c.value_cents / 100.0) }}{% else %}<span class="text-slate-300">–</span>{% endif %}</td>
            <td class="px-5 py-3 text-xs text-slate-400 font-mono">{{ c.utm_content or '–' }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% endif %}
  </div>

</section>

<!-- RECIPIENTS TAB -->
<section x-show="tab === 'recipients'" x-cloak class="max-w-7xl mx-auto px-4 sm:px-8 py-6">
  <div class="bg-white rounded-xl shadow-sm ring-1 ring-slate-200/60 overflow-hidden">
    <div class="px-5 py-4 border-b border-slate-100 flex flex-wrap items-center gap-3">
      <h2 class="text-[11px] font-semibold tracking-[0.1em] uppercase text-slate-500">Recipients</h2>
      <div class="flex gap-1 ml-auto text-xs">
        <button @click="variantFilter='all'" :class="variantFilter==='all' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'" class="px-3 py-1 rounded-full font-medium transition cursor-pointer">All</button>
        <button @click="variantFilter='A'" :class="variantFilter==='A' ? 'bg-brand text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'" class="px-3 py-1 rounded-full font-medium transition cursor-pointer">A</button>
        <button @click="variantFilter='B'" :class="variantFilter==='B' ? 'bg-fuchsia-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'" class="px-3 py-1 rounded-full font-medium transition cursor-pointer">B</button>
        <button @click="variantFilter='C'" :class="variantFilter==='C' ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'" class="px-3 py-1 rounded-full font-medium transition cursor-pointer">C</button>
      </div>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-slate-50/80 text-[10px] font-semibold tracking-[0.1em] uppercase text-slate-500">
          <tr>
            <th class="text-left px-5 py-3">Variant</th>
            <th class="text-left px-5 py-3">Email</th>
            <th class="text-left px-5 py-3">Section</th>
            <th class="text-left px-5 py-3">Status</th>
            <th class="text-left px-5 py-3 whitespace-nowrap">Sent</th>
            <th class="text-right px-5 py-3">Opens</th>
            <th class="text-right px-5 py-3">Clicks</th>
            <th class="text-left px-5 py-3 whitespace-nowrap">First open</th>
            <th class="text-left px-5 py-3">Flags</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          {% for r in recipients %}
          {% set dot = 'bg-brand' if r.variant == 'A' else ('bg-fuchsia-500' if r.variant == 'B' else 'bg-emerald-500') %}
          <tr x-show="variantFilter==='all' || variantFilter==='{{ r.variant }}'">
            <td class="px-5 py-3"><span class="inline-flex items-center gap-1.5 text-xs font-medium"><span class="inline-block w-2 h-2 rounded-full {{ dot }}"></span>{{ r.variant }}</span></td>
            <td class="px-5 py-3 font-mono text-xs">{{ r.email }}</td>
            <td class="px-5 py-3 text-xs text-slate-500">{{ r.section or '–' }}</td>
            <td class="px-5 py-3 text-xs">
              {% if r.status == 'sent' %}<span class="bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full text-[11px] font-medium">sent</span>
              {% elif r.status == 'failed' %}<span class="bg-rose-50 text-rose-700 px-2 py-0.5 rounded-full text-[11px] font-medium">failed</span>
              {% elif r.status == 'dry_run' %}<span class="bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full text-[11px] font-medium">dry</span>
              {% else %}<span class="bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full text-[11px] font-medium">pending</span>{% endif %}
            </td>
            <td class="px-5 py-3 text-xs text-slate-400 whitespace-nowrap">{{ (r.sent_at or '')[:16].replace('T',' ') or '–' }}</td>
            <td class="px-5 py-3 text-right kpi-value">{{ r.open_count or 0 }}</td>
            <td class="px-5 py-3 text-right kpi-value">{{ r.click_count or 0 }}</td>
            <td class="px-5 py-3 text-xs text-slate-400 whitespace-nowrap">{{ (r.first_open or '')[:16].replace('T',' ') or '–' }}</td>
            <td class="px-5 py-3 text-xs">
              {% if r.opted_out %}<span class="bg-rose-50 text-rose-700 px-2 py-0.5 rounded-full text-[11px] font-medium">unsub</span>{% endif %}
              {% if r.bounce_count and r.bounce_count > 0 %}<span class="bg-orange-50 text-orange-700 px-2 py-0.5 rounded-full text-[11px] font-medium ml-1">bounce</span>{% endif %}
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</section>

<!-- Chart.js initialisation -->
<script>
  const chartData = {
    funnel: {{ funnel | tojson }},
    stats: {{ stats | tojson }},
    timeseries: {{ timeseries | tojson }},
  };

  const GRID = 'rgba(148,163,184,0.15)';
  const AXIS = '#64748B';
  const LABEL_FONT = { family: "Geist, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif", size: 11 };

  // ---- Funnel (horizontal bar) ----
  const fc = document.getElementById('funnel-chart');
  if (fc) {
    const f = chartData.funnel;
    const total = f.sent || 1;
    new Chart(fc, {
      type: 'bar',
      data: {
        labels: ['Sent', 'Delivered', 'Opened', 'Clicked', 'Converted'],
        datasets: [{
          data: [f.sent, f.delivered, f.opened, f.clicked, f.converted],
          backgroundColor: ['#0F172A','#165DFC','#3B82F6','#60A5FA','#10B981'],
          borderRadius: 6,
          maxBarThickness: 30,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => `${ctx.parsed.x} (${((ctx.parsed.x/total)*100).toFixed(1)}% of sent)`,
            },
          },
        },
        scales: {
          x: { grid: { color: GRID, drawBorder: false }, ticks: { color: AXIS, font: LABEL_FONT }, beginAtZero: true },
          y: { grid: { display: false, drawBorder: false }, ticks: { color: '#0F172A', font: { ...LABEL_FONT, weight: 500 }}},
        },
      },
    });
  }

  // ---- Variant comparison (grouped bar) ----
  const vc = document.getElementById('variant-chart');
  if (vc) {
    const pct = (s, key) => (s && s.sent ? +(100 * (s[key] || 0) / s.sent).toFixed(1) : 0);
    const A = chartData.stats.A || {};
    const B = chartData.stats.B || {};
    const C = chartData.stats.C || {};
    new Chart(vc, {
      type: 'bar',
      data: {
        labels: ['Open %', 'CTR %', 'Unsub %', 'Bounce %'],
        datasets: [
          { label: 'A · ' + '{{ campaign.template_a }}', data: [pct(A,'opened'), pct(A,'clicked'), pct(A,'unsubscribed'), pct(A,'bounced')],
            backgroundColor: '#165DFC', borderRadius: 4, maxBarThickness: 28 },
          { label: 'B · ' + '{{ campaign.template_b }}', data: [pct(B,'opened'), pct(B,'clicked'), pct(B,'unsubscribed'), pct(B,'bounced')],
            backgroundColor: '#A21CAF', borderRadius: 4, maxBarThickness: 28 },
          { label: 'C · ' + '{{ campaign.template_c }}', data: [pct(C,'opened'), pct(C,'clicked'), pct(C,'unsubscribed'), pct(C,'bounced')],
            backgroundColor: '#10B981', borderRadius: 4, maxBarThickness: 28 },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: '#475569', font: LABEL_FONT, padding: 10, boxWidth: 10, boxHeight: 10 }},
          tooltip: { callbacks: { label: ctx => `${ctx.dataset.label.split(' · ')[0]}: ${ctx.parsed.y}%` }},
        },
        scales: {
          x: { grid: { display: false, drawBorder: false }, ticks: { color: AXIS, font: LABEL_FONT }},
          y: { grid: { color: GRID, drawBorder: false }, ticks: { color: AXIS, font: LABEL_FONT, callback: v => v + '%' }, beginAtZero: true },
        },
      },
    });
  }

  // ---- Timeline (line) ----
  const tc = document.getElementById('timeline-chart');
  if (tc) {
    const ts = chartData.timeseries;
    if (ts.length === 0) {
      tc.parentElement.innerHTML = '<div class="text-sm text-slate-400 py-8 text-center">No events yet.</div>';
    } else {
      const labels = ts.map(r => {
        // r.t = "YYYY-MM-DDTHH" → show "MMM DD · HH:00"
        const [date, h] = r.t.split('T');
        const d = new Date(date + 'T' + h + ':00:00');
        return d.toLocaleString('en-GB', { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' });
      });
      new Chart(tc, {
        type: 'line',
        data: {
          labels,
          datasets: [
            { label: 'Opens', data: ts.map(r => r.opens), borderColor: '#165DFC',
              backgroundColor: 'rgba(22,93,252,0.08)', fill: true, tension: 0.3, pointRadius: 2, pointHoverRadius: 4 },
            { label: 'Clicks (human)', data: ts.map(r => r.clicks), borderColor: '#10B981',
              backgroundColor: 'rgba(16,185,129,0.08)', fill: true, tension: 0.3, pointRadius: 2, pointHoverRadius: 4 },
          ],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { position: 'bottom', labels: { color: '#475569', font: LABEL_FONT, padding: 10, boxWidth: 10, boxHeight: 10 }},
          },
          scales: {
            x: { grid: { display: false, drawBorder: false }, ticks: { color: AXIS, font: LABEL_FONT, maxTicksLimit: 8 }},
            y: { grid: { color: GRID, drawBorder: false }, ticks: { color: AXIS, font: LABEL_FONT, precision: 0 }, beginAtZero: true },
          },
        },
      });
    }
  }
</script>

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
    {"stem": "03-stunden-zu-minuten", "num": "03", "label": "Vorher / Nachher",
     "sub": "Heute vs. mit Meditransfer · positive framing", "tag": "Benefits-forward", "rec": False},
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
            rows = conn.execute(
                f"""SELECT c.id, c.name, c.created_at, c.template_a, c.template_b, c.template_c,
                          (SELECT COUNT(*) FROM recipients r WHERE r.campaign_id = c.id) AS recipients,
                          (SELECT COUNT(*) FROM sends s WHERE s.campaign_id = c.id AND s.status = 'sent') AS sent,
                          (SELECT COUNT(DISTINCT s.id) FROM sends s
                             JOIN opens o ON o.send_id = s.id
                             WHERE s.campaign_id = c.id) AS opened,
                          (SELECT COUNT(DISTINCT s.id) FROM sends s
                             JOIN clicks ck ON ck.send_id = s.id
                             WHERE s.campaign_id = c.id
                               AND NOT {db._scanner_fingerprint_sql('s.id')}) AS clicked,
                          (SELECT COUNT(*) FROM conversions cv WHERE cv.campaign_id = c.id) AS converted
                   FROM campaigns c
                   WHERE c.name NOT LIKE 'mailgun-preview-%'
                     AND c.name NOT LIKE 'testsend-%'
                   ORDER BY c.id DESC"""
            ).fetchall()
            summary = db.index_summary(conn)
            campaigns = []
            for r in rows:
                d = dict(r)
                d["sparkline"] = db.campaign_sparkline(conn, d["id"], days=7)
                campaigns.append(d)
        return render_template_string(
            DASHBOARD_INDEX_HTML,
            campaigns=campaigns,
            summary=summary,
        )

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
                f"""SELECT ck.url, COUNT(DISTINCT s.recipient_id) AS unique_clickers, COUNT(*) AS total_clicks
                   FROM clicks ck
                   JOIN sends s ON s.id = ck.send_id
                   WHERE s.campaign_id = ?
                     AND ck.url NOT LIKE '%meditransfer.ch/impressum%'
                     AND ck.url NOT LIKE '%meditransfer.ch/datenschutz%'
                     AND NOT {db._scanner_fingerprint_sql('s.id')}
                   GROUP BY ck.url
                   ORDER BY unique_clickers DESC, total_clicks DESC
                   LIMIT 20""",
                (campaign_id,),
            ).fetchall()
            funnel = db.funnel_counts(conn, campaign_id)
            timeseries = db.events_timeseries(conn, campaign_id)
        return render_template_string(
            DASHBOARD_CAMPAIGN_HTML,
            campaign=dict(campaign),
            stats=stats,
            funnel=funnel,
            timeseries=timeseries,
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
