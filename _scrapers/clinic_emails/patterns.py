"""Constants — hints, noise filters, priority buckets, known mappings.

Kept separate from code so the CLI and tests can reference them without pulling
in requests / BeautifulSoup.
"""

from __future__ import annotations

# --- DB input ---

TARGET_SECTIONS = (2, 3, 4, 5, 6)
SECTION_HANDLES = {
    2: "medicalCenters",
    3: "clinics",
    4: "groupPractices",
    5: "medClinics",
    6: "hospitals",
}

# Hostnames we never treat as a practice URL. If an entry has ONLY these,
# we skip it (no website to crawl).
NON_PRACTICE_HOSTS = (
    "onedoc.ch",
    "google.ch",
    "google.com",
    "google.de",
    "google.fr",
    "google.it",
    "comparis.ch",
    "doktor.ch",
    "local.ch",
    "search.ch",
    "linkedin.com",  # LinkedIn company pages have no extractable practice email
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "youtube.com",
)

# --- Contact-page discovery ---

# (hint, weight) — kontakt/contact/impressum outweigh datenschutz/privacy since
# those are legal-copy pages that rarely have a specific practice email.
CONTACT_HINT_WEIGHTS = {
    # strong signals
    "kontakt": 3, "contact": 3, "contatti": 3, "contacto": 3,
    "impressum": 3, "imprint": 3, "mentions-legales": 3, "mentions_legales": 3,
    "note-legali": 3, "legal-notice": 3,
    "team": 3, "equipe": 3, "équipe": 3, "il-team": 3, "notre-equipe": 3,
    "unser-team": 3, "das-team": 3, "praxis-team": 3, "our-team": 3, "staff": 3,
    # medium
    "ueber-uns": 2, "über-uns": 2, "uberuns": 2, "ueberuns": 2,
    "about": 2, "about-us": 2, "chi-siamo": 2, "chisiamo": 2,
    "a-propos": 2, "apropos": 2,
    "anfahrt": 2, "sprechstunde": 2,
    "nous-contacter": 2,
    # weaker (datenschutz often has generic privacy email only)
    "datenschutz": 1, "privacy": 1, "datenschutzerklaerung": 1,
    "legal": 1, "cgu": 1,
}

# --- Referral-section discovery (DE / FR / IT / EN) ---
#
# Many Swiss clinics publish a dedicated "Zuweiser" / "Médecins référents" /
# "Medici invianti" / "Referring Physicians" section explaining how other
# practitioners can refer patients. We piggyback on the email crawl to
# detect and characterize these (form? PDF? email? fax?).

# Path/link-text hints for finding the referral page itself.
REFERRAL_HINT_WEIGHTS = {
    # German
    "zuweis": 4,           # zuweiser, zuweisung, zuweisende
    "uberweis": 4, "überweis": 4,
    "einweis": 3,          # einweisung, einweiser
    "fuer-zuweis": 4, "für-zuweis": 4,
    "fuer-aerzte": 3, "für-aerzte": 3, "fuer-ärzte": 3, "für-ärzte": 3,
    "fachpersonen": 2, "fachpersonal": 2,
    "patientenanmeldung": 3,
    # French
    "referent": 4, "référent": 4,
    "referents": 4, "référents": 4,
    "addresseur": 3, "adresseur": 3,
    "envoi-de-patient": 3,
    "demande-de-consultation": 3,
    "pour-medecin": 3, "pour-médecin": 3,
    "professionnels-sante": 2, "professionnels-de-sante": 2,
    # Italian
    "rinvio": 3,
    "medici-invianti": 4,
    "invio-pazient": 3,
    "richiesta-consulto": 3,
    "professionisti-sanitari": 2,
    # English
    "referral": 4,
    "referrer": 4,
    "refer-a-patient": 4, "refer_a_patient": 4,
    "referring-physician": 4,
    "for-physicians": 3, "for-providers": 3,
    "healthcare-professionals": 2,
}

# Filename hints for downloadable referral forms (matched against href + anchor).
REFERRAL_DOC_HINTS = (
    # German
    "zuweis", "uberweis", "überweis", "einweis",
    "anmeld", "patientenanmeldung", "anmeldeformular",
    # French
    "referent", "référent", "addresseur", "orientation",
    "demande-consult", "fiche-patient",
    # Italian
    "richiesta", "modulo-rinvio", "modulo-invio",
    # English
    "referral", "referring", "request-form", "patient-referral",
)

DOC_EXTENSIONS = (".pdf", ".doc", ".docx", ".rtf", ".odt")

# Email-prefix patterns specific to referrals
REFERRAL_EMAIL_PREFIXES = (
    "zuweis", "ueberweis", "überweis", "uberweis", "einweis",
    "anmeldung", "patientenanmeldung",
    "referent", "référent",
    "referral", "referring",
)

# Free-text indicators that this page IS about referrals (used for heuristic
# scoring after fetching, not for path matching).
REFERRAL_TEXT_HINTS = (
    "zuweiser", "zuweisung", "zuweisende ärzte", "zuweisende aerzte",
    "überweisung", "ueberweisung", "überweiser", "ueberweiser",
    "einweisung",
    "für zuweisende", "fuer zuweisende",
    "patientenanmeldung",
    "médecins référents", "medecins referents",
    "envoi de patient", "demande de consultation",
    "pour les médecins", "pour les medecins",
    "medici invianti", "rinvio",
    "richiesta di consulto",
    "for referring", "referring physicians", "refer a patient",
    "patient referral",
)

# If the entry URL 404s or no contact link is discoverable, try these paths at
# the domain root. Ordered most-likely first.
FALLBACK_PROBE_PATHS = (
    "/kontakt/", "/kontakt",
    "/contact/", "/contact",
    "/impressum/", "/impressum",
    "/team/", "/team", "/unser-team", "/das-team",
    "/ueber-uns/", "/ueber-uns", "/about", "/a-propos",
    "/datenschutz", "/datenschutz/",
    "/mentions-legales", "/contatti", "/chi-siamo",
)

SKIP_PATH_EXTENSIONS = (
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".rar", ".7z", ".mp4", ".mp3", ".mov", ".avi",
    ".css", ".js", ".xml", ".json",
)

# --- Noise email filters ---

# Exact domain matches to always discard (technical infrastructure, not a
# reachable business address)
NOISE_EMAIL_DOMAINS = {
    "sentry.wixpress.com",
    "sentry-next.wixpress.com",
    "sentry.io",
    "example.com", "example.ch", "example.org",
    "domain.com", "domain.ch",
    "yourmail.com", "mail.com",
    "localhost",
}

# Username patterns that indicate the candidate isn't an email:
# image filenames like "hero@2x.jpg", responsive-srcset "@560w", WebP sizes, etc.
NOISE_EMAIL_DOMAIN_SUFFIXES = (
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".ico",
    ".bmp", ".tiff",
)

# --- Priority buckets for outreach targeting ---

# Exact prefix match (or prefix followed by . - _) bumps to "priority"
PRIORITY_PREFIXES = (
    "info", "kontakt", "contact", "contatto",
    "sekretariat", "secretariat", "secretary", "segreteria",
    "verwaltung", "administration", "amministrazione",
    "anmeldung", "termine", "empfang", "reception", "accueil", "ricezione",
    "praxis", "klinik", "clinica", "cabinet", "studio",
    "office", "buero", "büro",
    "direktion", "direction", "direttore", "direzione",
    "leitung", "management", "gestione",
    "it", "edv", "tech", "it-support", "support",
    "backoffice", "buchhaltung", "admin",
    "mpa",  # Swiss: medizinische Praxisassistentin
)

# Any email on these domains is automatically priority (owner-operated HIN
# network domain — every Swiss clinic/practice uses this for secure email)
PRIORITY_DOMAIN_SUFFIXES = (
    "hin.ch",
)

# Prefixes that suggest a doctor/professional contact — bucketed as "general"
GENERAL_PREFIXES = ("arzt", "aerztin", "dr", "doc", "doctor", "med", "prof")


# --- Decoder constants ---

# Known DeCryptX ciphertexts seen in the wild (zio.ch network). Unknown
# ciphertexts are cryptographically un-decodeable without the key, so we just
# log them and move on.
DECRYPTX_KNOWN = {
    "3p0p0a311{0u3h1s2k2e2j3C0z1j0o1/3f3k": "mpa.zuerich@zio.ch",
    "2|0i3r310r3l3f3k0t2g0r1t0w3l3o0@1{2k2q1/0c1i3#": "zio.richterswil@zio.ch",
    "0m1q1b312i1m0a3u0u3v0@1{0i1p310c1i": "mpa.glarus@zio.ch",
    "3p3s3d0.2y0i0n0t2g1s3w3k1v0r1A1{1j2q0.1d2j": "mpa.winterthur@zio.ch",
    "0m3s3d201v3v1u1f1s3C2|1j3r313f0h": "mpa.uster@zio.ch",
}

# Fresh-looking desktop UA — the one in the old scraper's config.json is from
# Chrome 91 (2021). Some Cloudflare-fronted sites block old UAs with 403.
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-CH,de;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6,it;q=0.5",
    # Deliberately omitting "br" — urllib3/requests can transparently decompress
    # gzip/deflate but Brotli requires the optional `brotli` package. Some Swiss
    # hospital CDNs (Netlify, Cloudflare fronted) will send br if advertised,
    # leaving us with binary garbage.
    "Accept-Encoding": "gzip, deflate",
}
