"""Unit tests for clinic_emails.extractors.

Fixtures reproduce every obfuscation pattern we saw during the 80-site
reconnaissance. Run via:

    cd _scrapers && source venv/bin/activate && python -m pytest tests/ -v
"""

from __future__ import annotations

import os
import sys

# Make sibling package importable without installing.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clinic_emails.extractors import (  # noqa: E402
    classify,
    clean_email,
    decode_cloudflare_cfemail,
    deobfuscate,
    extract_emails,
)


# ---------------------------------------------------------------------------
# clean_email
# ---------------------------------------------------------------------------


def test_clean_email_basic():
    assert clean_email("info@clinic.ch") == "info@clinic.ch"
    assert clean_email("  INFO@Clinic.CH  ") == "info@clinic.ch"


def test_clean_email_strips_leading_digits():
    # Observed in old scraper runs: "05info@..." from poorly-extracted phone prefixes
    assert clean_email("05info@clinic.ch") == "info@clinic.ch"


def test_clean_email_strips_percent20_prefix():
    # Hirslanden site: mailto:%20klinik-birshof@hirslanden.ch
    assert clean_email("%20klinik-birshof@hirslanden.ch") == "klinik-birshof@hirslanden.ch"


def test_clean_email_strips_trailing_backslash():
    # handchirurgie-seefeld@hin.ch\  (JS-escaped)
    assert clean_email("handchirurgie-seefeld@hin.ch\\") == "handchirurgie-seefeld@hin.ch"


def test_clean_email_unescapes_html_entities():
    # praxismuehleberg.ch mailto uses decimal entities
    entity_form = "p&#114;&#97;xismuehlebe&#114;g&#64;hi&#110;.ch"
    assert clean_email(entity_form) == "praxismuehleberg@hin.ch"


def test_clean_email_handles_hex_entities():
    hex_form = "info&#x40;clinic&#x2e;ch"
    assert clean_email(hex_form) == "info@clinic.ch"


def test_clean_email_rejects_image_filenames():
    # Lindenhof: "db0779e1-3e16c5a5@560w.jpg"
    assert clean_email("db0779e1-3e16c5a5@560w.jpg") == ""
    assert clean_email("hero@2x.webp") == ""
    assert clean_email("pic@1120w2x.jpg") == ""


def test_clean_email_rejects_wix_sentry_noise():
    # Wix sites emit sentry IDs that look like emails
    assert clean_email("605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com") == ""
    assert clean_email("abc@sentry.wixpress.com") == ""
    assert clean_email("xyz@sentry.io") == ""


def test_clean_email_rejects_bogus_tld():
    assert clean_email("info@orthopaedie.shnur") == ""
    assert clean_email("foo@bar") == ""
    assert clean_email("not-an-email") == ""


def test_clean_email_rejects_placeholder():
    assert clean_email("name@example.com") == ""
    assert clean_email("your@domain.ch") == ""


def test_clean_email_defuses_concatenated_domain():
    # "...chwww.clinic.ch" style concatenation
    assert clean_email("info@clinic.chwww.clinic.ch") == "info@clinic.ch"


# ---------------------------------------------------------------------------
# decode_cloudflare_cfemail
# ---------------------------------------------------------------------------


def _cf_encode(email: str, key: int = 0x55) -> str:
    return f"{key:02x}" + "".join(f"{ord(c) ^ key:02x}" for c in email)


def test_cloudflare_cfemail_decode_roundtrip():
    for email, key in [("info@example.ch", 0x42), ("dr.schmidt@hin.ch", 0x7e)]:
        encoded = _cf_encode(email, key)
        assert decode_cloudflare_cfemail(encoded) == email


def test_cloudflare_cfemail_rejects_garbage():
    assert decode_cloudflare_cfemail("") is None
    assert decode_cloudflare_cfemail("zzz") is None
    assert decode_cloudflare_cfemail("01") is None  # too short


# ---------------------------------------------------------------------------
# deobfuscate
# ---------------------------------------------------------------------------


def test_deobfuscate_at_brackets():
    # Seen on sro.ch, psychologie-laxdal.ch, valaishospital.ch
    text = "Kontaktieren Sie uns: psychiatrie(at)sro.ch"
    result = deobfuscate(text)
    assert "psychiatrie@sro.ch" in result


def test_deobfuscate_dot_brackets():
    text = "info[at]example[dot]ch"
    result = deobfuscate(text)
    assert "info@example.ch" in result


def test_deobfuscate_html_entities():
    text = "mail&#64;example&#46;ch and hex&#x40;example&#x2e;ch"
    result = deobfuscate(text)
    assert "mail@example.ch" in result
    assert "hex@example.ch" in result


# ---------------------------------------------------------------------------
# extract_emails — end-to-end on HTML fragments
# ---------------------------------------------------------------------------


def test_extract_emails_mailto_link():
    html = '<a href="mailto:info@clinic.ch">Kontakt</a>'
    assert extract_emails(html) == {"info@clinic.ch"}


def test_extract_emails_mailto_with_entities():
    # Real example from praxismuehleberg.ch
    html = (
        '<a href="mailto:&#112;r&#97;xis&#109;&#117;ehl&#101;&#98;erg'
        '&#64;h&#105;&#110;&#46;&#99;h">Email</a>'
    )
    assert "praxismuehleberg@hin.ch" in extract_emails(html)


def test_extract_emails_mailto_url_encoded_space():
    # Hirslanden site: mailto:%20klinik-birshof@hirslanden.ch
    html = '<a href="mailto:%20klinik-birshof@hirslanden.ch">Contact</a>'
    result = extract_emails(html)
    assert "klinik-birshof@hirslanden.ch" in result


def test_extract_emails_plain_text():
    html = "<p>Anmeldung per E-Mail: reception@cliniquevalere.ch</p>"
    assert extract_emails(html) == {"reception@cliniquevalere.ch"}


def test_extract_emails_cloudflare_cfemail():
    encoded = _cf_encode("dr.schmidt@hin.ch", 0x42)
    html = f'<a class="__cf_email__" data-cfemail="{encoded}">[email&#160;protected]</a>'
    assert "dr.schmidt@hin.ch" in extract_emails(html)


def test_extract_emails_at_brackets_text():
    html = "<p>Kontakt: psychiatrie(at)sro.ch</p>"
    assert "psychiatrie@sro.ch" in extract_emails(html)


def test_extract_emails_data_email_attr():
    html = '<span data-email="hidden@clinic.ch">Email</span>'
    assert "hidden@clinic.ch" in extract_emails(html)


def test_extract_emails_data_mailto_attr():
    html = '<button data-mailto="contact@hospital.ch">Mail</button>'
    assert "contact@hospital.ch" in extract_emails(html)


def test_extract_emails_wp_eeb_decodeuri():
    # decodeURIComponent("info%40hin.ch") -> info@hin.ch
    html = (
        '<script>document.getElementById("eeb").innerHTML = '
        'decodeURIComponent("info%40hin.ch");</script>'
    )
    assert "info@hin.ch" in extract_emails(html)


def test_extract_emails_decryptx_known():
    # zio.ch network: known ciphertext -> decoded email
    html = 'DeCryptX("3p0p0a311{0u3h1s2k2e2j3C0z1j0o1/3f3k");'
    assert "mpa.zuerich@zio.ch" in extract_emails(html)


def test_extract_emails_decryptx_unknown_is_skipped():
    html = 'DeCryptX("RANDOM_UNKNOWN_BLOB");'
    assert extract_emails(html) == set()


def test_extract_emails_filters_image_lookalikes():
    # Lindenhof + Wix Sentry both appear here — neither should make it through
    html = """
    <div>
        <img src="db0779e1-3e16c5a5@560w.jpg" alt="photo">
        <script>window._sentry = "605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com";</script>
        <a href="mailto:real@clinic.ch">Email</a>
    </div>
    """
    assert extract_emails(html) == {"real@clinic.ch"}


def test_extract_emails_dedupes_case_insensitively():
    html = '<a href="mailto:INFO@Clinic.CH">1</a><a href="mailto:info@clinic.ch">2</a>'
    assert extract_emails(html) == {"info@clinic.ch"}


def test_extract_emails_handles_empty_and_broken_html():
    assert extract_emails("") == set()
    assert extract_emails("<html><body>no email here</body></html>") == set()


# ---------------------------------------------------------------------------
# classify
# ---------------------------------------------------------------------------


def test_classify_priority_prefixes():
    # Removed `it@` — no longer priority (2026-04-23 audit). IT helpdesk is
    # the wrong audience for Meditransfer.
    emails = {
        "info@clinic.ch",
        "kontakt@clinic.ch",
        "sekretariat@clinic.ch",
        "reception@hospital.ch",
    }
    result = classify(emails)
    for e in emails:
        assert e in result["priority"]


def test_classify_hin_domain_is_priority():
    # Every hin.ch address belongs to a Swiss registered clinic/doctor
    emails = {"praxis.schmidt@hin.ch", "dr.meier@hin.ch"}
    result = classify(emails)
    assert "praxis.schmidt@hin.ch" in result["priority"]
    assert "dr.meier@hin.ch" in result["priority"]


def test_classify_doctor_prefix_is_general():
    emails = {"dr.patrick@gmx.ch", "doc@random.com"}
    result = classify(emails)
    assert "dr.patrick@gmx.ch" in result["general"]
    assert "doc@random.com" in result["general"]


def test_classify_other_bucket_catches_rest():
    emails = {"webmaster@foo.ch", "random.person@bar.ch"}
    result = classify(emails)
    assert "webmaster@foo.ch" in result["other"]
    assert "random.person@bar.ch" in result["other"]


def test_classify_sorted_within_buckets():
    emails = {"zz@foo.ch", "aa@foo.ch", "mm@foo.ch"}
    result = classify(emails)
    # Priority bucket is tier-then-alpha, but general + other are plain alpha.
    # Since all three emails land in `other`, sort-order there is alphabetical.
    assert result["other"] == ["aa@foo.ch", "mm@foo.ch", "zz@foo.ch"]


# ---------------------------------------------------------------------------
# 2026-04-23 quality upgrade — new filters and tier system
# ---------------------------------------------------------------------------


def test_classify_sekretariat_compound():
    """Compound prefixes like `sekretariatsdienste@` land in priority, not other.

    Covers 333 real addresses that the old exact-match classify() lost:
    `sekretariatsdienste@claraspital.ch`, `sekretariaturologie@h-och.ch`,
    `sekretariatradio@spitalmaennedorf.ch`, etc."""
    r = classify({"sekretariatsdienste@claraspital.ch"})
    assert "sekretariatsdienste@claraspital.ch" in r["priority"]

    r = classify({"secretariatdirection@ghol.ch"})
    assert "secretariatdirection@ghol.ch" in r["priority"]

    r = classify({"sekretariaturologie@h-och.ch"})
    assert "sekretariaturologie@h-och.ch" in r["priority"]


def test_classify_zuweiser_is_priority():
    """Referral-coordinator mailboxes are the highest-value Meditransfer target."""
    r = classify({"zuweiser@clinic.ch", "zuweiserbrief@hospital.ch"})
    assert "zuweiser@clinic.ch" in r["priority"]
    assert "zuweiserbrief@hospital.ch" in r["priority"]


def test_classify_tier_orders_sekretariat_before_info():
    """When both info@ and sekretariat@ exist at the same practice,
    sekretariat@ must sort first in the priority list — the mailer picks
    the first priority address, so tier order decides the chosen inbox."""
    r = classify({"info@clinic.ch", "sekretariat@clinic.ch"})
    assert r["priority"][0] == "sekretariat@clinic.ch"
    assert r["priority"][1] == "info@clinic.ch"


def test_classify_hin_outranks_info_and_general():
    """HIN addresses outrank everything else."""
    r = classify({"info@clinic.ch", "sekretariat@clinic.ch", "dr.meier@hin.ch"})
    assert r["priority"][0] == "dr.meier@hin.ch"


def test_classify_demotes_it_and_support_out_of_priority():
    """IT helpdesk, support, edv, tech, admin, buchhaltung are no longer
    priority — they're the wrong audience for Meditransfer cold outreach."""
    r = classify({"it@clinic.ch", "support@clinic.ch", "edv@clinic.ch",
                  "buchhaltung@clinic.ch", "admin@clinic.ch"})
    assert r["priority"] == []
    # They still get recorded somewhere (general or other), just not priority
    rest = r["general"] + r["other"]
    assert "it@clinic.ch" in rest


def test_clean_email_drops_agency_domain():
    """Web-agency / webdesign shop domains get dropped — we don't want to
    cold-email the agency that made the clinic's website."""
    assert clean_email("hello@yoo.digital") == ""
    assert clean_email("simone@organica.agency") == ""
    assert clean_email("info@webdesign-stern5.ch") == ""
    assert clean_email("kontakt@werbeagentur-mueller.de") == ""
    assert clean_email("digital@lane-digital.ch") == ""
    assert clean_email("hello@wepractice.ch") == ""


def test_clean_email_drops_media_garbage_username():
    """CSS `url(...)` fragments that happened to parse as emails are noise."""
    assert clean_email("media--c981039f--query@anything.ch") == ""
    assert clean_email("media--deadbeef--query@x.ch") == ""


def test_clean_email_drops_sentry_ingest_domain():
    """Sentry telemetry DSNs leaked into the page source."""
    assert clean_email("foo@o1039559.ingest.sentry.io") == ""
    assert clean_email("bar@o37417.ingest.sentry.io") == ""
    assert clean_email("x@sentry.service.msio.cloud") == ""


def test_clean_email_drops_template_sample_addresses():
    """CMS theme / office template sample placeholders."""
    assert clean_email("max.mustermann@muster.com") == ""
    assert clean_email("peter.muster@musterfirma.com") == ""
    assert clean_email("marilyn.barbone@fotolia.com") == ""
    assert clean_email("info@beispiel.de") == ""


def test_clean_email_drops_activemind_legal():
    """DPO-as-a-service address caught from impressum/datenschutz pages."""
    assert clean_email("hirslanden@activemind.legal") == ""


def test_extract_emails_rot13_decoder():
    """ROT13-obfuscated mailtos (a clienia.ch anti-scraping trick) get
    recovered by the decoder #10. The TLDs .pu / .pbz / .qr are ROT13 of
    .ch / .com / .de and are the fingerprint."""
    html = '<a>Kontakt: <span>gevntr.fpuybrffyv@pyvravn.pu</span></a>'
    result = extract_emails(html)
    assert "triage.schloessli@clienia.ch" in result


def test_classify_third_party_legal_only_drop():
    """When entry_domain is the practice's domain and an email's source is
    only /impressum or /datenschutz AND the email's domain differs, drop it
    (catches webmaster@agency credits, dpo.ch@affidea DPO services)."""
    emails = {"webmaster@third-party-agency.ch", "info@clinic.ch"}
    sources = {
        "webmaster@third-party-agency.ch": "https://clinic.ch/impressum",
        "info@clinic.ch": "https://clinic.ch/kontakt",
    }
    r = classify(emails, entry_domain="clinic.ch", sources=sources)
    assert "webmaster@third-party-agency.ch" not in r["priority"]
    assert "webmaster@third-party-agency.ch" not in r["general"]
    assert "webmaster@third-party-agency.ch" not in r["other"]
    assert "info@clinic.ch" in r["priority"]


def test_classify_third_party_on_non_legal_page_is_kept():
    """Same third-party domain but sourced from a regular page (team/kontakt)
    is NOT dropped — we only apply the filter when the email ONLY appears
    on legal/privacy pages."""
    emails = {"webmaster@third-party.ch"}
    sources = {"webmaster@third-party.ch": "https://clinic.ch/team"}
    r = classify(emails, entry_domain="clinic.ch", sources=sources)
    # Still shows up somewhere (general/other). Point is: not dropped.
    assert any(
        "webmaster@third-party.ch" in r[bucket]
        for bucket in ("priority", "general", "other")
    )


def test_classify_same_domain_legal_page_address_is_kept():
    """Third-party filter does NOT fire when email's domain matches the
    practice's own domain (datenschutz@clinic.ch is THEIR legitimate DPO
    mailbox, keep it)."""
    emails = {"datenschutz@clinic.ch"}
    sources = {"datenschutz@clinic.ch": "https://clinic.ch/datenschutz"}
    r = classify(emails, entry_domain="clinic.ch", sources=sources)
    assert any(
        "datenschutz@clinic.ch" in r[bucket]
        for bucket in ("priority", "general", "other")
    )


def test_classify_back_compat_without_source_args():
    """Old callers that don't pass entry_domain/sources keyword args still work."""
    r = classify({"info@clinic.ch", "sekretariat@clinic.ch"})
    assert r["priority"][0] == "sekretariat@clinic.ch"  # tier still applies
