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
    # generic CMS / theme placeholder domains
    "example.com", "example.ch", "example.org",
    "domain.com", "domain.ch", "domain.tld",
    "yourmail.com", "mail.com",
    "company.com", "yourcompany.com",
    "yourdomain.com", "placeholder.com",
    "test.com", "test.ch",
    "localhost",
    # Template placeholders caught in the audit (2026-04-23)
    "muster.com", "musterfirma.com",
    "beispiel.de", "beispiel.ch", "beispiel.com",
    "abc.com",
    "mysite.com",  # CMS template default — caught in post-enrichment sample
    # Legal / DPO-as-a-service (leak in from datenschutz/impressum pages)
    "activemind.legal",  # hirslanden's DPO service, 299x in audit
    # Platform legal (jimdo / wix datenschutz catcher)
    "jimdo.com", "wix.com", "wixsite.com",
    # Sentry monitoring services (msio.cloud is a Swiss variant)
    "msio.cloud", "msio.ch",
    # Stock photo attribution caught from <img alt> / watermarks
    "fotolia.com", "shutterstock.com", "gettyimages.com",
}

# Username patterns that indicate the candidate isn't an email:
# image filenames like "hero@2x.jpg", responsive-srcset "@560w", WebP sizes, etc.
NOISE_EMAIL_DOMAIN_SUFFIXES = (
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".ico",
    ".bmp", ".tiff",
)

# Regex patterns applied to the full domain portion of the email.
# Use these for suffix/infix matches we can't enumerate exactly (e.g. a
# customer-specific Sentry project ID is generated per org).
NOISE_EMAIL_DOMAIN_PATTERNS = (
    r"\.ingest\.sentry\.io$",     # *@o1039559.ingest.sentry.io (~200 in audit)
    r"^sentry\.service\.",         # sentry.service.msio.cloud
    r"\.wixpress\.com$",            # any Wix subdomain
)

# Regex patterns applied to the username (local-part). Catches template sample
# addresses and CSS-asset false positives that our email regex happily parses.
NOISE_USERNAME_PATTERNS = (
    r"^media--[0-9a-f]{8}--query$",   # 929+ CSS asset false positives in audit
    r"^max\.mustermann$",             # template sample, 194x in audit
    r"^peter\.muster$",
    r"^marilyn\.barbone$",            # fotolia watermark catcher
    r"^barbara$",                      # when on muster.ch
    r"^vorname\.nachname$",
    r"^vorname$", r"^nachname$",
)

# Regex patterns applied to the full domain to identify web-agency / webdesign
# shop addresses. These get dropped entirely — a clinic is not reachable
# through their website agency's contact email.
AGENCY_DOMAIN_PATTERNS = (
    # Word-boundary match on agency keywords. Boundary = start-of-string or
    # a hyphen/dot, so it catches `webdesign-stern5.ch`, `webdesign.ch`,
    # `foo.webdesign.bar`, but NOT e.g. `uxwebdesignerpro.ch` where the
    # keyword is glued to other letters.
    r"(^|[-.])(webdesign|webdesigner|webagentur|werbeagentur|internet-agentur|mediendesign)([-.]|$)",
    r"(^|[.])agentur[-.]",
    r"\.agency$",                       # organica.agency etc.
    r"\.(digital|studio)$",             # yoo.digital, *.studio
    r"^wepractice\.ch$",                # Medbase CMS vendor, 120x in audit
    r"^dachcomdigital\.",
    r"^lane-digital\.",
    r"^multidigital\.",
)

# --- Priority buckets for outreach targeting ---
#
# Tier order (best first). Used by classify() to sort within the priority
# bucket so the first element is always the most person-operated inbox.
# Each tier uses *startswith* matching on the username, which catches both
# bare prefixes (sekretariat@) and compounds (sekretariatsdienste@,
# secretariatdirection@) that the old exact-match missed.
#
# Compound-safe matching: "sekretariat" matches "sekretariatsdienste@x.ch".
# The separator-based fallback (prefix + . - _) is kept for "info.xyz@"
# style addresses.
#
# IT / admin / buchhaltung addresses REMOVED from priority — they're tech
# helpdesk, not referral-coordinator mailboxes. Meditransfer's cold email
# is irrelevant to the IT department.

# Tier TOP — secretary / reception / referral / MPA.
# These mailboxes are staffed by the person who actually processes patient
# referrals. Highest-value Meditransfer target.
PRIORITY_PREFIXES_TOP = (
    # German
    "sekretariat", "empfang", "anmeldung", "mpa",
    "zuweis", "zuweiser", "zuweisung", "ueberweis", "überweis", "einweis",
    "triage", "patientenanmeldung",
    # French
    "secretariat", "secrétariat", "accueil",
    "medecin-referent", "médecin-référent", "referent", "référent",
    # Italian
    "segreteria", "ricezione", "rinvio",
    # English
    "secretary", "reception", "referral", "referring",
    # Fixed appointment booking
    "termine", "termin", "appointment", "rdv",
)

# Tier MID — general reception mailboxes (current info@-tier behaviour).
PRIORITY_PREFIXES_MID = (
    "info", "kontakt", "contact", "contatto",
    "praxis", "klinik", "clinica", "cabinet", "studio",
)

# Tier LOW — generic office / administration. Still priority (they're
# owner-operated mailboxes) but ranked last.
PRIORITY_PREFIXES_LOW = (
    "office", "buero", "büro",
    "verwaltung", "administration", "amministrazione",
    "leitung",
)

# Flat list for back-compat with any external callers that import
# PRIORITY_PREFIXES directly. Order is TOP → MID → LOW.
PRIORITY_PREFIXES = PRIORITY_PREFIXES_TOP + PRIORITY_PREFIXES_MID + PRIORITY_PREFIXES_LOW

# Any email on these domains is automatically priority (owner-operated HIN
# network domain — every Swiss clinic/practice uses this for secure email).
# HIN addresses rank at TOP tier because they're person-operated by design.
PRIORITY_DOMAIN_SUFFIXES = (
    "hin.ch",
)

# Prefixes that suggest a doctor/professional contact — bucketed as "general"
GENERAL_PREFIXES = ("arzt", "aerztin", "dr", "doc", "doctor", "med", "prof")

# Page-types where a third-party address (web agency, DPO service, legal
# contact) typically appears. When classify() receives source context and
# an email's sources fall ONLY in this set AND the email's domain differs
# from the practice's own domain, the email is dropped as third-party.
THIRD_PARTY_SOURCE_HINTS = (
    "impressum", "imprint", "mentions-legales", "mentions_legales",
    "note-legali", "legal-notice", "legal",
    "datenschutz", "datenschutzerklaerung", "privacy", "cgu",
)


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
