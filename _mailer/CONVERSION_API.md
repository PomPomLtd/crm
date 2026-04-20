# Conversion tracking handoff — meditransfer.ch integration

This document explains how to call the **mailer's conversion endpoint** from
the `meditransfer.ch` registration / billing flow so that signups, trial
starts, and payments show up per-campaign and per-A/B/C-variant in the
mailer dashboard.

The mailer is a separate service deployed at **`https://meditransfer-mailer.fly.dev`**.
It already tracks every cold-outreach email's open + click. Conversions
close the loop — *which variant drove the most paid signups?*

---

## Endpoint

```
POST https://meditransfer-mailer.fly.dev/api/conversion
Content-Type: application/json
X-Conversion-Token: <see below>
```

**Token**: ask the mailer operator (Sam) for the current
`MAILER_CONVERSION_TOKEN` — it is set on Fly via `fly secrets set` and is
**not stored in this repo**. Receive it through 1Password / Signal / a
secure channel, never email or chat history.

Store it as an env var on the meditransfer.ch backend (e.g.
`MAILER_CONVERSION_TOKEN`). Never commit it. Never expose it to the browser.

To rotate: the operator runs `fly secrets set MAILER_CONVERSION_TOKEN=<new>`
on the mailer side and shares the new value the same way. The endpoint
will refuse the old value the moment the new one is staged.

The endpoint returns 200 on success, 401 if the token is wrong, 404 if the
token isn't configured server-side. Always returns 200 even if attribution
fails (campaign not found, no email match) — the conversion is recorded
unlinked rather than dropped.

---

## Request body

```json
{
  "utm_campaign": "test-06",
  "utm_content": "03-stunden-zu-minuten",
  "email": "user@clinic.ch",
  "type": "signup",
  "value_cents": 4900
}
```

| Field | Required | Notes |
|---|---|---|
| `utm_campaign` | strongly recommended | The campaign name. Lift directly from the `utm_campaign` query param on the landing URL. |
| `utm_content` | recommended | The template stem (e.g. `01-der-brief`, `02-hero-cta`). Used as a fallback variant identifier when `email` is missing. |
| `email` | recommended | The new user's email. Enables per-recipient attribution: the mailer matches it to the row in `recipients` for the given campaign and pulls the assigned variant. |
| `type` | recommended | Free-form label. Suggested values: `signup`, `trial_started`, `paid`, `cancelled`. Fire one event per state transition. |
| `value_cents` | optional | Revenue in cents (CHF). Used for revenue-per-variant in the dashboard. |

Any extra fields are stored verbatim in the `raw_json` column for later
analysis.

---

## Response

```json
{
  "ok": true,
  "id": 42,
  "attributed": {
    "campaign_id": 1,
    "recipient_id": 17,
    "variant": "C"
  }
}
```

If `attributed.campaign_id` is `null`, the mailer didn't find a campaign
named `utm_campaign` — usually means the UTM was hand-typed or rewritten by
some intermediary. The conversion is still in the DB; it just isn't
linked to a campaign for stats purposes.

---

## Where the UTM params come from

Every email sent by the mailer has its CTA link decorated with:

```
https://meditransfer.ch/?code=WELCOME30
  &utm_source=meditransfer-mailer
  &utm_medium=email
  &utm_campaign=<campaign_name>      e.g. test-06
  &utm_content=<template_stem>       e.g. 03-stunden-zu-minuten
```

The user clicks → lands on meditransfer.ch with those query params present.

You need to **persist these params across the user's session** until they
either sign up, abandon, or pay. Standard pattern:

1. On landing, parse `utm_source`, `utm_campaign`, `utm_content`, `code` from
   the URL. (Also handy to grab `utm_medium`.)
2. Store them in a long-lived cookie (e.g. `mt_attrib`, JSON blob, 90 days)
   AND in the user's session.
3. When you're about to call the mailer's conversion endpoint, read them
   from the cookie/session and forward.

Cookie example (server-rendered):

```
Set-Cookie: mt_attrib={"utm_source":"meditransfer-mailer","utm_campaign":"test-06","utm_content":"03-stunden-zu-minuten","code":"WELCOME30"}; Max-Age=7776000; Path=/; SameSite=Lax; Secure; HttpOnly
```

If `utm_source` is anything other than `meditransfer-mailer`, don't fire to
this endpoint — it's not from us.

---

## When to fire

| User action | `type` | `value_cents` |
|---|---|---|
| Account created (no payment yet) | `"signup"` | omit |
| Trial activated | `"trial_started"` | omit |
| First successful charge | `"paid"` | the actual amount in cents |
| Subscription cancelled | `"cancelled"` | omit |

Fire **at most once per state transition per user** to keep the funnel
honest. Idempotency is your responsibility; the mailer doesn't dedupe.

The dashboard counts a recipient as "converted" once per (campaign,
recipient), regardless of how many event types you fire — but `value_cents`
is summed across all events for that recipient. So fire `signup` (no value)
+ `paid` (CHF 49.00) and the dashboard will show 1 conversion / CHF 49.00
of revenue.

---

## Reference implementations

### PHP / Craft (looks like the meditransfer.ch stack)

```php
function trackMailerConversion(string $type, ?int $valueCents = null): void
{
    $attrib = $_COOKIE['mt_attrib'] ?? null;
    if (!$attrib) return;
    $attrib = json_decode($attrib, true);
    if (($attrib['utm_source'] ?? '') !== 'meditransfer-mailer') return;

    $payload = [
        'utm_campaign' => $attrib['utm_campaign'] ?? null,
        'utm_content'  => $attrib['utm_content'] ?? null,
        'email'        => Craft::$app->user->identity->email ?? null,
        'type'         => $type,
    ];
    if ($valueCents !== null) {
        $payload['value_cents'] = $valueCents;
    }

    $ch = curl_init('https://meditransfer-mailer.fly.dev/api/conversion');
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 5,                    // don't block user-facing requests
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'X-Conversion-Token: ' . getenv('MAILER_CONVERSION_TOKEN'),
        ],
        CURLOPT_POSTFIELDS => json_encode($payload),
    ]);
    curl_exec($ch);                              // fire-and-forget
    curl_close($ch);
}

// At signup:
trackMailerConversion('signup');

// At successful charge:
trackMailerConversion('paid', valueCents: $invoice->amountInCents);
```

Best practice: wrap in a try/catch and run via a background queue
(deferred job). The mailer endpoint should never be on the user's critical
path — if it's slow or down, the signup must still complete.

### Node / TypeScript

```typescript
async function trackMailerConversion(opts: {
  type: string;
  email?: string;
  valueCents?: number;
  attrib: { utm_campaign?: string; utm_content?: string; utm_source?: string };
}): Promise<void> {
  if (opts.attrib.utm_source !== 'meditransfer-mailer') return;

  await fetch('https://meditransfer-mailer.fly.dev/api/conversion', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Conversion-Token': process.env.MAILER_CONVERSION_TOKEN!,
    },
    body: JSON.stringify({
      utm_campaign: opts.attrib.utm_campaign,
      utm_content: opts.attrib.utm_content,
      email: opts.email,
      type: opts.type,
      value_cents: opts.valueCents,
    }),
    signal: AbortSignal.timeout(5000),
  }).catch(err => console.warn('mailer conversion failed', err));
}
```

---

## Testing

Smoke-test against the live endpoint:

```
curl -X POST https://meditransfer-mailer.fly.dev/api/conversion \
  -H "Content-Type: application/json" \
  -H "X-Conversion-Token: $MAILER_CONVERSION_TOKEN" \
  -d '{
    "utm_campaign": "test-06",
    "utm_content": "01-der-brief",
    "email": "test+integration@yourdomain.ch",
    "type": "signup",
    "value_cents": 0
  }'
```

Expected: `200 OK` with `{"ok":true,...}`. The conversion will appear in
the dashboard immediately:

→ https://meditransfer-mailer.fly.dev/dashboard (Basic Auth required)

If `attributed.campaign_id` is `null`, double-check the campaign name —
campaign names are case-sensitive and must match exactly.

---

## Things to watch out for

- **Don't expose `MAILER_CONVERSION_TOKEN` in client-side code.** All calls
  must go through the meditransfer.ch backend.
- **Don't strip UTM params on the redirect chain.** If you proxy
  `?code=WELCOME30...` through anything (auth wall, country detector), make
  sure the params survive to the landing page.
- **Email is optional but powerful.** Without it, we can attribute to a
  campaign + variant but not to a specific recipient — so per-recipient
  detail in the dashboard stays empty.
- **Don't fire conversions for organic traffic.** The
  `utm_source=meditransfer-mailer` check guards against that.
- **The mailer endpoint is best-effort.** If it returns non-200, don't
  block the user. Log + retry in a background queue if you want
  reliability; otherwise, accept the rare miss.

---

## Schema (for reference)

The mailer stores conversions in this SQLite table:

```sql
CREATE TABLE conversions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     INTEGER REFERENCES campaigns(id),
    recipient_id    INTEGER REFERENCES recipients(id),
    variant         TEXT,            -- A / B / C
    utm_campaign    TEXT,
    utm_content     TEXT,
    email           TEXT,
    conversion_type TEXT,            -- signup / paid / etc.
    value_cents     INTEGER,
    received_at     TEXT NOT NULL,
    raw_json        TEXT             -- full payload, future-proof
);
```

Per-variant aggregates appear in the dashboard's variant cards (Converted
count + Conversion%). Recent conversions appear in a dedicated table on the
campaign drilldown page.

---

## Change history

- **2026-04-20** — initial endpoint + dashboard integration. Single shared
  bearer token. Future: per-environment tokens + replay protection.
