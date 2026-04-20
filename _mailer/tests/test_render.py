import pytest

from mailer.render import KNOWN_TEMPLATES, render


BASE_URL = "https://mailer.example.ch"
SECRET = "test-secret"

RECIPIENT = {
    "email": "dr.muster@example.ch",
    "title": "Praxis Muster",
    "url": "https://praxis-muster.ch",
    "canton": "ZH",
    "section": "clinics",
    "profession": "Innere Medizin",
}


@pytest.mark.parametrize("template_name", KNOWN_TEMPLATES)
def test_each_known_template_renders(template_name: str):
    r = render(
        template_name=template_name,
        subject="Testbetreff",
        recipient=RECIPIENT,
        campaign_id=42,
        base_url=BASE_URL,
        token_secret=SECRET,
    )
    assert r.html.startswith("<!DOCTYPE html")
    assert len(r.text) > 100
    assert r.subject == "Testbetreff"


@pytest.mark.parametrize("template_name", KNOWN_TEMPLATES)
def test_unsubscribe_url_injected(template_name: str):
    r = render(
        template_name=template_name,
        subject="s",
        recipient=RECIPIENT,
        campaign_id=1,
        base_url=BASE_URL,
        token_secret=SECRET,
    )
    assert r.unsubscribe_url.startswith(BASE_URL + "/unsubscribe?t=")
    assert r.unsubscribe_url in r.html
    assert r.unsubscribe_url in r.text
    assert "{{" not in r.html
    assert "{{" not in r.text


def test_unsubscribe_url_is_unique_per_recipient():
    a = render(
        template_name="01-der-brief", subject="s",
        recipient={"email": "a@x.ch"}, campaign_id=1,
        base_url=BASE_URL, token_secret=SECRET,
    )
    b = render(
        template_name="01-der-brief", subject="s",
        recipient={"email": "b@x.ch"}, campaign_id=1,
        base_url=BASE_URL, token_secret=SECRET,
    )
    assert a.unsubscribe_url != b.unsubscribe_url


def test_subject_templating():
    r = render(
        template_name="01-der-brief",
        subject="Hallo {{ recipient.title }}",
        recipient=RECIPIENT,
        campaign_id=1,
        base_url=BASE_URL,
        token_secret=SECRET,
    )
    assert r.subject == "Hallo Praxis Muster"
