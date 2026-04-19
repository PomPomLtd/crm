"""Unit tests for clinic_emails.referral.

Fixtures cover the full DE/FR/IT/EN target languages and each detection
method (form, PDF, doc, dedicated email, fax).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clinic_emails.referral import (  # noqa: E402
    aggregate,
    detect_referral_signals,
    score_referral_links,
)


# ---------------------------------------------------------------------------
# score_referral_links
# ---------------------------------------------------------------------------


BASE = "https://www.example-clinic.ch/"


def test_score_referral_links_german():
    html = """
    <ul>
      <li><a href="/zuweiser/">Für Zuweisende Ärzte</a></li>
      <li><a href="/ueberweisung/formular">Überweisungsformular</a></li>
      <li><a href="/team/">Team</a></li>
    </ul>
    """
    links = score_referral_links(html, BASE, limit=5)
    urls = [u for u, _ in links]
    assert "https://www.example-clinic.ch/zuweiser" in urls
    assert "https://www.example-clinic.ch/ueberweisung/formular" in urls
    assert all("/team" not in u for u in urls)


def test_score_referral_links_french():
    html = """
    <a href="/medecins-referents/">Médecins référents</a>
    <a href="/contact/">Contact</a>
    <a href="/envoi-de-patient/">Envoi de patient</a>
    """
    links = score_referral_links(html, BASE, limit=5)
    urls = [u for u, _ in links]
    assert any("/medecins-referents" in u for u in urls)
    assert any("/envoi-de-patient" in u for u in urls)


def test_score_referral_links_italian():
    html = '<a href="/medici-invianti/">Medici invianti</a>'
    links = score_referral_links(html, BASE, limit=5)
    assert links and "medici-invianti" in links[0][0]


def test_score_referral_links_english():
    html = '<a href="/refer-a-patient/">Refer a Patient</a>'
    links = score_referral_links(html, BASE, limit=5)
    assert links and "refer-a-patient" in links[0][0]


def test_score_referral_links_skips_external_and_assets():
    html = """
    <a href="https://other-domain.ch/zuweiser">External Zuweiser</a>
    <a href="/zuweiser/foo.pdf">PDF link</a>
    <a href="/zuweiser/">Internal Zuweiser</a>
    """
    links = score_referral_links(html, BASE, limit=5)
    urls = [u for u, _ in links]
    # external rejected
    assert all("other-domain" not in u for u in urls)
    # PDF link rejected (we want HTML pages, not docs)
    assert not any(u.endswith(".pdf") for u in urls)
    # internal kept
    assert any("/zuweiser" in u for u in urls)


# ---------------------------------------------------------------------------
# detect_referral_signals
# ---------------------------------------------------------------------------


def test_detect_returns_empty_for_unrelated_page():
    html = "<html><body><h1>Welcome</h1><p>Just a homepage.</p></body></html>"
    assert detect_referral_signals(html, BASE) == {}


def test_detect_text_only_page_de():
    html = """
    <h1>Für zuweisende Ärzte</h1>
    <p>Bitte kontaktieren Sie unser Sekretariat für die Patientenanmeldung.</p>
    """
    r = detect_referral_signals(html, BASE + "zuweiser/")
    assert r["page_url"] == BASE + "zuweiser/"
    assert "page-only" in r["evidence"]
    assert any("zuweis" in s.lower() for s in r["text_signals"])


def test_detect_form_de():
    html = """
    <h1>Zuweisung</h1>
    <form action="/submit" method="post">
      <label>Patientenname</label><input name="patient_name">
      <label>Diagnose</label><textarea name="diagnose"></textarea>
    </form>
    """
    r = detect_referral_signals(html, BASE + "zuweisung")
    assert r["has_form"] is True
    assert "form" in r["evidence"]


def test_detect_form_french_field_names():
    html = """
    <p>Demande de consultation</p>
    <form><input name="patient"><input name="diagnostic"></form>
    """
    r = detect_referral_signals(html, BASE + "demande/")
    assert r["has_form"] is True


def test_detect_pdf_doc_german():
    html = """
    <h2>Überweisung</h2>
    <a href="/docs/Ueberweisungsformular.pdf">Überweisungsformular (PDF)</a>
    <a href="/docs/Anmeldung.docx">Anmeldeformular Word</a>
    <a href="/docs/random.pdf">Random PDF</a>
    """
    r = detect_referral_signals(html, BASE + "ueberweisung/")
    docs = {d["url"]: d for d in r["documents"]}
    assert any("Ueberweisungsformular.pdf" in u for u in docs)
    assert any("Anmeldung.docx" in u for u in docs)
    types = {d["type"] for d in r["documents"]}
    assert "pdf" in types
    assert "docx" in types
    assert "pdf" in r["evidence"]
    assert "doc" in r["evidence"]


def test_detect_referral_email():
    html = """
    <p>Pour les médecins référents:</p>
    <p>Email: zuweiser@clinic.ch</p>
    """
    r = detect_referral_signals(html, BASE + "referent/")
    assert "zuweiser@clinic.ch" in r["emails"]
    assert "email" in r["evidence"]


def test_detect_fax_number():
    html = """
    <h1>Zuweisung</h1>
    <p>Telefax: +41 44 123 45 67 — Anmeldung per Fax möglich.</p>
    """
    r = detect_referral_signals(html, BASE + "zuweisung/")
    assert r["faxes"], "expected at least one fax"
    assert "fax" in r["evidence"]


def test_detect_pdf_without_referral_keyword_skipped_on_unrelated_page():
    # A random PDF on a non-referral page shouldn't trigger detection
    html = '<a href="/docs/jahresbericht.pdf">Jahresbericht 2024</a>'
    r = detect_referral_signals(html, BASE)
    assert r == {}


def test_detect_pdf_passes_through_on_referral_page_even_without_keyword():
    # If the page itself is clearly a referral page, generic PDFs get listed
    # so the user can manually check what they are.
    html = """
    <h1>Zuweisende Ärzte</h1>
    <p>Information für Zuweiser.</p>
    <a href="/info.pdf">Informationsblatt</a>
    """
    r = detect_referral_signals(html, BASE + "zuweiser/")
    assert any("info.pdf" in d["url"] for d in r["documents"])


# ---------------------------------------------------------------------------
# aggregate
# ---------------------------------------------------------------------------


def test_aggregate_empty():
    assert aggregate([]) == {"found": False}
    assert aggregate([{}]) == {"found": False}


def test_aggregate_combines_pages_and_dedupes_docs():
    p1 = {
        "page_url": "https://x.ch/zuweiser/",
        "text_signals": ["zuweiser"],
        "has_form": False,
        "documents": [{"url": "https://x.ch/forms/a.pdf", "anchor": "Form A", "type": "pdf"}],
        "emails": ["zuweiser@x.ch"],
        "faxes": [],
        "evidence": ["pdf", "email"],
    }
    p2 = {
        "page_url": "https://x.ch/contact/",
        "text_signals": ["zuweisung"],
        "has_form": True,
        "documents": [
            {"url": "https://x.ch/forms/a.pdf", "anchor": "Form A", "type": "pdf"},
            {"url": "https://x.ch/forms/b.docx", "anchor": "Form B", "type": "docx"},
        ],
        "emails": ["zuweisung@x.ch"],
        "faxes": ["+41 44 999 88 77"],
        "evidence": ["form", "pdf", "doc", "email", "fax"],
    }
    agg = aggregate([p1, p2])
    assert agg["found"] is True
    assert agg["has_form"] is True
    # Form > pdf > doc > email > fax > page-only ordering
    assert agg["methods"] == ["form", "pdf", "doc", "email", "fax"]
    # Documents deduped by URL
    assert len(agg["documents"]) == 2
    assert sorted(agg["emails"]) == ["zuweiser@x.ch", "zuweisung@x.ch"]
    assert "+41 44 999 88 77" in agg["faxes"]
    assert "https://x.ch/zuweiser/" in agg["pages"]
    assert "https://x.ch/contact/" in agg["pages"]
