"""Template rendering.

Each template stem (e.g. "01-der-brief") has two files:
  - {stem}.html  — the Postmark-safe HTML body (tables, VML buttons, inline CSS)
  - {stem}.txt   — plain-text alternative (required for deliverability)

A campaign stores three template stems — one per A/B/C variant. We render
the one matching each recipient's assigned variant. The unsubscribe URL is
a signed, per-recipient token so links can't be forged to opt others out.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional
from urllib.parse import quote, urlencode

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from .tokens import make_unsubscribe_token

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

KNOWN_TEMPLATES: tuple[str, ...] = (
    "01-der-brief",
    "02-hero-cta",
    "03-stunden-zu-minuten",
)


@dataclass(frozen=True)
class Rendered:
    subject: str
    html: str
    text: str
    unsubscribe_url: str


def build_env(templates_dir: Optional[Path] = None) -> Environment:
    loader_dir = templates_dir or TEMPLATES_DIR
    return Environment(
        loader=FileSystemLoader(str(loader_dir)),
        autoescape=select_autoescape(["html", "htm"]),
        undefined=StrictUndefined,
        trim_blocks=False,
        lstrip_blocks=False,
    )


def unsubscribe_url(
    *, base_url: str, token_secret: str, email: str, campaign_id: int
) -> str:
    token = make_unsubscribe_token(
        token_secret, email=email, campaign_id=campaign_id
    )
    return f"{base_url.rstrip('/')}/unsubscribe?t={quote(token)}"


CTA_BASE = "https://meditransfer.ch/?code=WELCOME30"


def cta_url_for(*, campaign_name: str, template_name: str) -> str:
    """CTA link with UTM params so meditransfer.ch analytics can attribute
    clicks to (campaign, variant). utm_source identifies the channel,
    utm_campaign the send, utm_content the email variant."""
    params = urlencode({
        "utm_source": "meditransfer-mailer",
        "utm_medium": "email",
        "utm_campaign": campaign_name,
        "utm_content": template_name,
    })
    sep = "&" if "?" in CTA_BASE else "?"
    return f"{CTA_BASE}{sep}{params}"


def render(
    *,
    template_name: str,
    subject: str,
    recipient: Mapping[str, Any],
    campaign_id: int,
    base_url: str,
    token_secret: str,
    campaign_name: str = "preview",
    env: Optional[Environment] = None,
) -> Rendered:
    env = env or build_env()
    unsub = unsubscribe_url(
        base_url=base_url,
        token_secret=token_secret,
        email=recipient["email"],
        campaign_id=campaign_id,
    )
    cta = cta_url_for(campaign_name=campaign_name, template_name=template_name)
    ctx = {
        "recipient": dict(recipient),
        "subject": subject,
        "unsubscribe_url": unsub,
        "cta_url": cta,
    }
    html = env.get_template(f"{template_name}.html").render(**ctx)
    text = env.get_template(f"{template_name}.txt").render(**ctx)
    subject_rendered = env.from_string(subject).render(**ctx)
    return Rendered(
        subject=subject_rendered, html=html, text=text, unsubscribe_url=unsub
    )
