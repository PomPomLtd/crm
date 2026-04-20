"""Signed, URL-safe tokens for unsubscribe + tracking links.

We sign (email, campaign_id) with the app's MAILER_TOKEN_SECRET so an
unsubscribe URL can't be forged to opt somebody else out. Tokens don't
expire — an unsubscribe link in a cold-outreach email must keep working
forever (UWG compliance).
"""

from __future__ import annotations

from itsdangerous import BadSignature, URLSafeSerializer
from typing import Optional, Tuple


def _serializer(secret: str) -> URLSafeSerializer:
    return URLSafeSerializer(secret, salt="pompom-mailer-v1")


def make_unsubscribe_token(secret: str, *, email: str, campaign_id: int) -> str:
    return _serializer(secret).dumps({"e": email.lower(), "c": campaign_id})


def parse_unsubscribe_token(
    secret: str, token: str
) -> Optional[Tuple[str, int]]:
    """Returns (email, campaign_id) or None if the token is invalid."""
    try:
        payload = _serializer(secret).loads(token)
    except BadSignature:
        return None
    email = payload.get("e")
    campaign_id = payload.get("c")
    if not isinstance(email, str) or not isinstance(campaign_id, int):
        return None
    return email, campaign_id
