# Email Pattern Reconnaissance — 20260419_213044

Sampled **80** clinic sites.

## Coverage

- Sites with any plaintext email (home or contact page): **54/80**  (67.5%)
- Plaintext email visible on homepage: **50/80**
- Plaintext email on contact page: **44/80**
- Contact link discoverable from homepage: **67/80**

## Patterns detected (sites where pattern appears on any page)

| Pattern | Count | Homepage | Contact page |
|---|---|---|---|
| `base64_email_candidate` | 138 | 71 | 67 |
| `plain_email` | 94 | 50 | 44 |
| `mailto_link` | 81 | 46 | 35 |
| `contact_form` | 74 | 36 | 38 |
| `wordpress` | 46 | 23 | 23 |
| `cookiebot_etc` | 15 | 7 | 8 |
| `html_entity_at_dec` | 13 | 9 | 4 |
| `typo3` | 12 | 6 | 6 |
| `recaptcha` | 10 | 2 | 8 |
| `html_entity_dot_dec` | 9 | 5 | 4 |
| `wix` | 9 | 5 | 4 |
| `cf_email_protect` | 6 | 3 | 3 |
| `squarespace` | 6 | 3 | 3 |
| `cf_cfemail` | 5 | 2 | 3 |
| `joomla` | 4 | 2 | 2 |
| `text_at_brackets` | 4 | 2 | 2 |
| `js_email_charcode` | 2 | 1 | 1 |
| `html_entity_at_hex` | 1 | 1 | 0 |
| `html_entity_dot_hex` | 1 | 1 | 0 |
| `text_dot_brackets` | 1 | 0 | 1 |

## Status codes

- 200: 71
- 404: 5
- 403: 2
- error: 2

## Top servers

- Apache: 28
- nginx: 18
- Pepyaka: 6
- cloudflare: 5
- nginx-rc: 2
- CM4all Webserver: 2
- Netlify: 1
- Microsoft-IIS/10.0: 1
- Apache/2.4.62 (Win64) OpenSSL/1.1.1d: 1
- webnode: 1

## Per-URL details

### https://www.hirslanden.ch/de/st--anna-im-bahnhof/aerzte.fmh.html/6.html
- Section: clinics · Title: Hirslanden St. Anna im Bahnhof - Chirurgie Plastische
- Homepage status: 200 · server: ``
- Homepage patterns: ['base64_email_candidate', 'contact_form']
    - `base64_email_candidate`: `9l8QO0aHyMuQlThSXQUo4c05Go1Lo0i`
    - `base64_email_candidate`: `CDkNDe5qnzJibC4Iq83lndSfNArlw3S2k7FlhWo`
    - `contact_form`: `<form`
- Contact links: [('https://www.hirslanden.ch/de/st--anna-im-bahnhof/kontakt.html', 3), ('https://www.hirslanden.ch/de/corporate/datenschutzerklaerung.html', 3), ('https://www.hirslanden.ch/de/corporate/impressum.html', 3), ('https://www.hirslanden.ch/content/corporate/de/hirslanden-gruppe/kontakt/healthline', 2), ('https://www.hirslanden.ch/de/corporate/ueber-uns.html', 2)]
- Best contact page: https://www.hirslanden.ch/de/klinik-st--anna/kontakt.html (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'mailto_link', 'plain_email']
      - `mailto_link`: `klinik-stanna@hirslanden.ch`
      - `mailto_link`: `meggen.stanna@hirslanden.ch`
      - `plain_email`: `klinik-stanna@hirslanden.ch`
      - `plain_email`: `meggen.stanna@hirslanden.ch`
      - `base64_email_candidate`: `pZf8AJotu170CGkRficPELOVnLHjB4dcwhVuBP1QVOSjOy`
      - `base64_email_candidate`: `nOjigMalp41ZHnHRP4oTRz2yaanjN3kUnXkQFzw`
      - `contact_form`: `<form`
      - `cookiebot_etc`: `OneTrust`

### https://www.pzmag.ch/kliniken-angebot/klinik-fuer-depression-angst/psychotherapiestation-muensingen
- Section: hospitals · Title: Psychiatriezentrum Münsingen PZM - Psychotherapiestation
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'typo3']
    - `base64_email_candidate`: `assets/5d9ac5dfbe2bf88b1381d314766387c7/Icons/favicon`
    - `base64_email_candidate`: `splidejs/splide/dist/css/splide`
    - `contact_form`: `<form`
    - `typo3`: `typo3conf`
- Contact links: [('https://www.pzmag.ch/datenschutz', 3), ('https://www.pzmag.ch/kontakt', 3), ('https://www.pzmag.ch/aufenthalt-besuch/anfahrt-anreise', 3), ('https://www.pzmag.ch/quicklinks/anfahrt-warenannahme', 3), ('https://www.pzmag.ch/impressum', 3)]
- Best contact page: https://www.pzmag.ch/datenschutz (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'typo3']
      - `base64_email_candidate`: `assets/5d9ac5dfbe2bf88b1381d314766387c7/Icons/favicon`
      - `base64_email_candidate`: `splidejs/splide/dist/css/splide`
      - `contact_form`: `<form`
      - `contact_form`: `Kontaktformular`
      - `typo3`: `typo3conf`

### https://www.swissmedical.net/fr/hopitaux/genolier/centres/oncologie
- Section: clinics · Title: Clinique de Genolier - Oncologie
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
    - `mailto_link`: `info@genolier.net`
    - `mailto_link`: `consultinfonco@genolier.net`
    - `plain_email`: `info@genolier.net`
    - `plain_email`: `consultinfonco@genolier.net`
    - `base64_email_candidate`: `/site/templates/public/img/favicon/apple`
    - `base64_email_candidate`: `/site/templates/public/img/favicon/favicon`
    - `contact_form`: `<form`
- Contact links: [('https://www.swissmedical.net/fr/mentions-legales', 5), ('https://www.swissmedical.net/fr/hopitaux/patients-internationaux/contact-us', 3), ('https://www.swissmedical.net/fr/hopitaux/genolier/contact', 2), ('https://www.swissmedical.net/fr/hopitaux/genolier/a-propos', 2), ('https://www.swissmedical.net/fr/hopitaux/genolier/a-propos/swiss-medical-recovery', 2)]
- Best contact page: https://www.swissmedical.net/fr/mentions-legales (status 200)
  - patterns: ['base64_email_candidate', 'contact_form']
      - `base64_email_candidate`: `/site/templates/public/img/favicon/apple`
      - `base64_email_candidate`: `/site/templates/public/img/favicon/favicon`
      - `contact_form`: `<form`

### https://www.praxismuehleberg.ch/
- Section: groupPractices · Title: Gemeinschaftspraxis PuB Mühleberg
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'html_entity_at_dec', 'html_entity_dot_dec', 'mailto_link', 'wordpress']
    - `mailto_link`: `pra&#120;&#105;&#115;&#109;&#117;&#101;h&#108;&#101;ber&#103;&#64;&#104;&#105;&#110;&#46;ch`
    - `html_entity_at_dec`: `&#64;`
    - `html_entity_dot_dec`: `&#46;`
    - `base64_email_candidate`: `content/uploads/2018/09/favicon`
    - `base64_email_candidate`: `PropertyValueSpecification`
    - `contact_form`: `id='contact`
    - `contact_form`: `id="contact`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-json`
- Contact links: [('https://www.praxismuehleberg.ch/impressum-datenschutz', 6), ('https://www.praxismuehleberg.ch/team/', 3), ('https://www.praxismuehleberg.ch/kontakt/', 3), ('http://praxismuehleberg.ch/kontakt', 2), ('https://www.praxismuehleberg.ch/index.php/team', 2)]
- Best contact page: https://www.praxismuehleberg.ch/impressum-datenschutz/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'html_entity_at_dec', 'html_entity_dot_dec', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `pra&#120;&#105;smu&#101;&#104;&#108;&#101;be&#114;&#103;&#64;hi&#110;&#46;&#99;&#104;`
      - `html_entity_at_dec`: `&#64;`
      - `html_entity_dot_dec`: `&#46;`
      - `plain_email`: `praxismuehleberg@hin.ch`
      - `base64_email_candidate`: `content/uploads/2018/09/favicon`
      - `base64_email_candidate`: `PropertyValueSpecification`
      - `contact_form`: `id='contact`
      - `contact_form`: `id="contact`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-json`

### http://www.biotonus.ch/fr/index.php?testnavigateur=no
- Section: clinics · Title: Clinique Bon Port Montreux - Médecine Interne
- **Errors**: ['HTTP 404']
- Homepage status: 404 · server: `Apache`

### https://medsite.ch/beate.sprecher
- Section: medClinics · Title: Praxis für Hausarztmedizin, Promenade 33a Davos Platz
- Homepage status: 200 · server: `nginx-rc`
- Homepage patterns: ['base64_email_candidate']
    - `base64_email_candidate`: `src/js/vmaxformvalidator`
    - `base64_email_candidate`: `sprecher/unserpraxisteam/`
- Contact links: [('https://medsite.ch/beate.sprecher/unserpraxisteam/', 3), ('https://medsite.ch/beate.sprecher/kontakt/', 3)]
- Best contact page: https://medsite.ch/beate.sprecher/unserpraxisteam/ (status 200)
  - patterns: ['base64_email_candidate']
      - `base64_email_candidate`: `src/js/vmaxformvalidator`
      - `base64_email_candidate`: `sprecher/unserpraxisteam/`

### https://carougeneralistes.ch/
- Section: groupPractices · Title: Carougénéralistes Cabinet Médical
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'wordpress']
    - `base64_email_candidate`: `content/themes/astra/assets/css/minified/frontend`
    - `base64_email_candidate`: `content/themes/astra/assets/fonts/astra`
    - `contact_form`: `id='contact`
    - `contact_form`: `id="contact`
    - `wordpress`: `wp-json`
    - `wordpress`: `wp-content`
- Contact links: [('https://carougeneralistes.ch/equipe/', 3), ('https://carougeneralistes.ch/contact/', 3)]
- Best contact page: https://carougeneralistes.ch/equipe/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'wordpress']
      - `base64_email_candidate`: `content/themes/astra/assets/css/minified/frontend`
      - `base64_email_candidate`: `content/themes/astra/assets/fonts/astra`
      - `contact_form`: `id='contact`
      - `contact_form`: `id="contact`
      - `wordpress`: `wp-json`
      - `wordpress`: `wp-content`

### https://www.spitalmenziken.ch/unser-angebot/operative-medizin/aesthetische-chirurgie/?S=28
- Section: hospitals · Title: Asana Gruppe AG, Spital Menziken - Chirurgie Plastische
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'mailto_link', 'plain_email', 'typo3']
    - `mailto_link`: `praxis@spitalmenziken.ch`
    - `plain_email`: `ImpfzentrumMenziken@impfkampagne.onmicrosoft.com`
    - `plain_email`: `praxis@spitalmenziken.ch`
    - `base64_email_candidate`: `org/TR/xhtml1/DTD/xhtml1`
    - `base64_email_candidate`: `typo3temp/Assets/2ba2d28e2f`
    - `contact_form`: `<form`
    - `typo3`: `typo3temp`
    - `typo3`: `typo3conf`
    - `cookiebot_etc`: `Cookiebot`
    - `cookiebot_etc`: `cookiebot`
- Contact links: [('https://www.spitalmenziken.ch/ueber-uns/impressum/datenschutzerklaerung/?S=62&cHash=1fd46a56ac4e392d1cdc4019caf96bff&L=0', 7), ('https://www.spitalmenziken.ch/drdunst/ueber-uns/?S=28', 3), ('https://www.spitalmenziken.ch/drdunst/drdunst/team/?S=28', 3), ('https://www.spitalmenziken.ch/drdunst/patienten-besucher/anreise/anfahrtsplan/?S=28', 3), ('https://www.spitalmenziken.ch/drdunst/ueber-uns/telefon/?S=28', 2)]
- Best contact page: https://www.spitalmenziken.ch/ueber-uns/impressum/datenschutzerklaerung/?S=62&cHash=1fd46a56ac4e392d1cdc4019caf96bff&L=0 (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'mailto_link', 'plain_email', 'typo3']
      - `mailto_link`: `praxis@spitalmenziken.ch`
      - `plain_email`: `ImpfzentrumMenziken@impfkampagne.onmicrosoft.com`
      - `plain_email`: `direktion@spitalmenziken.ch`
      - `base64_email_candidate`: `org/TR/xhtml1/DTD/xhtml1`
      - `base64_email_candidate`: `typo3temp/Assets/c03c8e2dfe`
      - `contact_form`: `<form`
      - `contact_form`: `Kontaktformular`
      - `typo3`: `typo3temp`
      - `typo3`: `typo3conf`
      - `cookiebot_etc`: `Cookiebot`
      - `cookiebot_etc`: `cookiebot`

### https://www.uzb.ch/
- Section: hospitals · Title: Universitätsspital Basel - Zahnmedizinische Klinik
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'html_entity_at_dec', 'html_entity_dot_dec', 'mailto_link', 'plain_email']
    - `mailto_link`: `mail@uzb.ch`
    - `html_entity_at_dec`: `&#64;`
    - `html_entity_dot_dec`: `&#46;`
    - `plain_email`: `mail@uzb.ch`
    - `base64_email_candidate`: `assets/uzb/images/signet`
    - `base64_email_candidate`: `wissen/uebersicht/category/aktuelles`
- Contact links: [('https://www.uzb.ch/impressum', 3), ('https://www.uzb.ch/datenschutz', 3), ('https://www.uzb.ch/unternehmen', 1), ('https://www.uzb.ch/fuer-aerzt-innen/fuer-ueberweiser-innen', 1)]
- Best contact page: https://www.uzb.ch/impressum (status 200)
  - patterns: ['base64_email_candidate', 'html_entity_at_dec', 'html_entity_dot_dec', 'mailto_link', 'plain_email']
      - `mailto_link`: `mail@uzb.ch`
      - `html_entity_at_dec`: `&#64;`
      - `html_entity_dot_dec`: `&#46;`
      - `plain_email`: `mail@uzb.ch`
      - `base64_email_candidate`: `assets/uzb/images/signet`
      - `base64_email_candidate`: `wissen/uebersicht/category/aktuelles`

### http://www.chirurgia-gianom.ch/it/studio-medico/
- Section: medClinics · Title: Studio Medico Dr. med. Gianom Duri
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'html_entity_at_dec', 'html_entity_dot_dec', 'plain_email', 'typo3']
    - `html_entity_at_dec`: `&#64;`
    - `html_entity_dot_dec`: `&#46;`
    - `plain_email`: `info@chirurgia-gianom.ch`
    - `base64_email_candidate`: `/typo3conf/ext/spotwebsite/Resources/Public/Assets/Images/Icons/favicon`
    - `base64_email_candidate`: `/typo3conf/ext/spotwebsite/Resources/Public/Assets/Images/Icons/touch`
    - `typo3`: `typo3conf`
    - `typo3`: `typo3temp`
- Contact links: [('https://www.chirurgia-gianom.ch/it/service/impressum/', 3)]
- Best contact page: https://www.chirurgia-gianom.ch/it/service/impressum/ (status 200)
  - patterns: ['base64_email_candidate', 'html_entity_at_dec', 'html_entity_dot_dec', 'plain_email', 'typo3']
      - `html_entity_at_dec`: `&#64;`
      - `html_entity_dot_dec`: `&#46;`
      - `plain_email`: `info@chirurgia-gianom.ch`
      - `base64_email_candidate`: `/typo3conf/ext/spotwebsite/Resources/Public/Assets/Images/Icons/favicon`
      - `base64_email_candidate`: `ch/it/service/impressum/`
      - `typo3`: `typo3conf`
      - `typo3`: `typo3temp`

### https://www.arztpraxis-reichenburg.ch/
- Section: medClinics · Title: Praxis Dr. med. Till Elisabeth
- Homepage status: 200 · server: `cloudflare`
- Homepage patterns: ['base64_email_candidate', 'cf_cfemail', 'cf_email_protect']
    - `cf_cfemail`: `6706151d131715061f0e144a15020e040f020905121500270f0e0949040f`
    - `cf_email_protect`: `/cdn-cgi/l/email-protection`
    - `base64_email_candidate`: `com/app/cms/image/transf/dimension=`
    - `base64_email_candidate`: `jpg/path/s01720c1a7b34ec69/backgroundarea/if2ea20eb70e89705/version/1651828686/image`
- Contact links: [('https://www.arztpraxis-reichenburg.ch/team/', 3), ('https://www.arztpraxis-reichenburg.ch/kontakt/', 3), ('https://www.arztpraxis-reichenburg.ch/datenschutz/', 3)]
- Best contact page: https://www.arztpraxis-reichenburg.ch/team/ (status 200)
  - patterns: ['base64_email_candidate', 'cf_cfemail', 'cf_email_protect']
      - `cf_cfemail`: `bcddcec6c8ccceddc4d5cf91ced9d5dfd4d9d2dec9cedbfcd4d5d292dfd4`
      - `cf_email_protect`: `/cdn-cgi/l/email-protection`
      - `base64_email_candidate`: `com/app/cms/image/transf/dimension=`
      - `base64_email_candidate`: `jpg/path/s01720c1a7b34ec69/backgroundarea/i3b81d085e0d59545/version/1651828702/image`

### https://www.hirslanden.ch/de/klinik-hirslanden/centers/hautaerzte-zentrum-zuerisee.html/
- Section: medClinics · Title: Hautärzte-Zentrum am Zürisee (dresDermal GmbH)
- Homepage status: 200 · server: ``
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'html_entity_at_dec', 'mailto_link', 'plain_email']
    - `mailto_link`: `info&#64;hautaerzte-zz.ch`
    - `mailto_link`: `info@hautaerzte-zz.ch`
    - `html_entity_at_dec`: `&#64;`
    - `plain_email`: `info@hautaerzte-zz.ch`
    - `base64_email_candidate`: `qIRQn1N2OJJ3PJr3dFmc8aHPXLc`
    - `base64_email_candidate`: `N6BBK71aC5gRWOrofY1gsJ8hSIpXc8AT3un0`
    - `contact_form`: `<form`
    - `cookiebot_etc`: `OneTrust`
- Contact links: [('https://www.hirslanden.ch/de/corporate/ueber-uns/kontakt/healthline.html', 4), ('https://www.hirslanden.ch/de/klinik-hirslanden/kontakt.html', 3), ('https://www.hirslanden.ch/de/klinik-hirslanden/centers/hautaerzte-zentrum-zuerisee/team.html', 3), ('https://www.hirslanden.ch/de/klinik-hirslanden/centers/hautaerzte-zentrum-zuerisee/kontakt.html', 3), ('https://www.hirslanden.ch/de/corporate/datenschutzerklaerung.html', 3)]
- Best contact page: https://www.hirslanden.ch/de/corporate/ueber-uns/kontakt/healthline.html (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc']
      - `base64_email_candidate`: `9l8QO0aHyMuQlThSXQe15FW9QxIGC0yCXtCLp8htKhfI7trmK2kljd5gk4rdm9FdXv2qprCKMPe`
      - `base64_email_candidate`: `clientlibs/hirslanden/clientlibs/frontend`
      - `contact_form`: `<form`
      - `cookiebot_etc`: `OneTrust`

### https://www.luks.ch/standorte/standort-luzern/augenklinik
- Section: hospitals · Title: Luzerner Kantonsspital Luzern - Augenklinik
- Homepage status: 200 · server: `Netlify`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
    - `mailto_link`: `augenklinik@luks.ch`
    - `plain_email`: `augenklinik@luks.ch`
    - `base64_email_candidate`: `4z9JQqD2Q3rI43oSrpQdZXu8vcG48uZXaHWjj1svsRQ`
    - `base64_email_candidate`: `d09GRgABAAAAAAZgABAAAAAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABGRlRNAAAGRAAAABoAAAAci6qHkUdERUYAAAWgAAAAIwAAACQAYABXR1BPUwAA`
    - `contact_form`: `<form`
- Contact links: [('https://www.luks.ch/ihr-luks/kontakt', 3), ('https://www.luks.ch/standorte/standort-luzern/augenklinik/kontakt-und-anreise-augenklinik', 3), ('https://www.luks.ch/standorte/standort-luzern/augenklinik/leistungsangebot-augenklinik/kontaktlinsen', 3), ('https://www.luks.ch/impressum', 3), ('https://www.luks.ch/ihr-luks', 1)]
- Best contact page: https://www.luks.ch/ihr-luks/kontakt/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form']
      - `base64_email_candidate`: `4z9JQqD2Q3rI43oSrpQdZXu8vcG48uZXaHWjj1svsRQ`
      - `base64_email_candidate`: `d09GRgABAAAAAAZgABAAAAAADAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABGRlRNAAAGRAAAABoAAAAci6qHkUdERUYAAAWgAAAAIwAAACQAYABXR1BPUwAA`
      - `contact_form`: `<form`
      - `contact_form`: `kontaktformular`

### https://www.hug.ch/medecine-interne-generale
- Section: hospitals · Title: HUG - Médecine Interne
- Homepage status: 200 · server: ``
- Homepage patterns: ['base64_email_candidate', 'contact_form']
    - `base64_email_candidate`: `/sites/interhug/files/favicons/apple`
    - `base64_email_candidate`: `ch/sites/interhug/files/homepage/img/hug`
    - `contact_form`: `<form`
    - `contact_form`: `id="contact`
- Contact links: [('https://www.hug.ch/contact', 3), ('https://www.hug.ch/contact-formation', 3), ('https://www.hug.ch/medecine-interne-generale/equipe-du-service-medecine-interne-generale', 3), ('https://www.hug.ch/cadre-legal-et-politique', 2)]
- Best contact page: https://www.hug.ch/contact (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'recaptcha']
      - `base64_email_candidate`: `/sites/interhug/files/favicons/apple`
      - `base64_email_candidate`: `ch/sites/interhug/files/homepage/img/hug`
      - `contact_form`: `<form`
      - `recaptcha`: `g-recaptcha`

### https://www.praxisamloewenplatz.ch/
- Section: groupPractices · Title: Praxis am Löwenplatz
- Homepage status: 200 · server: `Microsoft-IIS/10.0`
- Homepage patterns: ['base64_email_candidate']
    - `base64_email_candidate`: `download/einwilligungserklarung`
    - `base64_email_candidate`: `stopImmediatePropagation`
- Contact links: [('https://www.praxisamloewenplatz.ch/praxis/unser-team.html', 3), ('https://www.praxisamloewenplatz.ch/praxis/datenschutz.html', 3), ('https://www.praxisamloewenplatz.ch/praxis/impressum.html', 3)]
- Best contact page: https://www.praxisamloewenplatz.ch/praxis/unser-team.html (status 200)
  - patterns: ['base64_email_candidate']
      - `base64_email_candidate`: `stopImmediatePropagation`

### https://www.cabinet-chirurgie.ch/
- Section: medClinics · Title: Cabinet Dr. Dominguez Stéphane
- **Errors**: ['HTTP 403']
- Homepage status: 403 · server: `nginx`

### https://www.psychiater-thun.ch/
- Section: medClinics · Title: Praxis Dr. med. Reichard Stefan
- **Errors**: ['HTTPSConnectionPool(host=\'www.psychiater-thun.ch\', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLCertVerificationError(1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for \'www.psychiater-thun.ch\'. (_ssl.c:1032)")))']
- Homepage status: ? · server: ``

### https://www.hno-luzern.ch/
- Section: groupPractices · Title: hals-nasen-ohren-praxis
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'joomla', 'mailto_link', 'plain_email', 'recaptcha', 'squarespace', 'wordpress']
    - `mailto_link`: `info@hno-luzern.ch`
    - `mailto_link`: `hno-luzern@hin.ch`
    - `plain_email`: `info@hno-luzern.ch`
    - `plain_email`: `hno-luzern@hin.ch`
    - `base64_email_candidate`: `com/s/abel/v18/MwQ5bhbm2POE2V9BPQ`
    - `base64_email_candidate`: `com/s/roboto/v51/KFO7CnqEu92Fr1ME7kSn66aGLdTylUAMa3yUBA`
    - `recaptcha`: `grecaptcha`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-includes`
    - `joomla`: `joomla`
    - `squarespace`: `squarespace`
- Contact links: [('https://www.hno-luzern.ch/spezialsprechstunden/', 3), ('https://www.hno-luzern.ch/team/', 3), ('https://www.hno-luzern.ch/kontakt/', 3), ('https://www.hno-luzern.ch/anfahrt/', 3), ('https://www.hno-luzern.ch/datenschutzerklaerung/', 3)]
- Best contact page: https://www.hno-luzern.ch/spezialsprechstunden/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'joomla', 'mailto_link', 'plain_email', 'recaptcha', 'squarespace', 'wordpress']
      - `mailto_link`: `info@hno-luzern.ch`
      - `mailto_link`: `hno-luzern@hin.ch`
      - `plain_email`: `info@hno-luzern.ch`
      - `plain_email`: `hno-luzern@hin.ch`
      - `base64_email_candidate`: `Nasenspezialsprechstunde`
      - `base64_email_candidate`: `content/uploads/2022/03/shutterstock`
      - `contact_form`: `Kontaktformular`
      - `contact_form`: `<form`
      - `recaptcha`: `grecaptcha`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-includes`
      - `joomla`: `joomla`
      - `squarespace`: `squarespace`

### https://hautarztbern.ch/
- Section: medClinics · Title: Praxis Dr. med. Sigrist Urs
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
    - `mailto_link`: `info@hautarztbern.ch`
    - `plain_email`: `apple-touch-icon@2x.png`
    - `plain_email`: `favicon@2x.png`
    - `base64_email_candidate`: `/images/backgrounds/hautarzt`
    - `base64_email_candidate`: `klnjoq6cv6tvinr3p0hrhn20e2d52at8`
    - `contact_form`: `<form`
- Contact links: [('https://hautarztbern.ch/de/contact/', 3), ('https://hautarztbern.ch/de/general/about.php', 3), ('https://hautarztbern.ch/de/general/impressum.php', 3), ('https://hautarztbern.ch/de/service/', 1)]
- Best contact page: https://hautarztbern.ch/de/contact/ (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
      - `mailto_link`: `info@hautarztbern.ch`
      - `plain_email`: `apple-touch-icon@2x.png`
      - `plain_email`: `favicon@2x.png`
      - `base64_email_candidate`: `klnjoq6cv6tvinr3p0hrhn20e2d52at8`
      - `base64_email_candidate`: `/de/service/aesthetische`

### https://herz-praxis.ch/praxis/dr-med-roman-netzer
- Section: medClinics · Title: Praxis Dr. med. Netzer Roman
- **Errors**: ['HTTP 404']
- Homepage status: 404 · server: `Apache/2.4.62 (Win64) OpenSSL/1.1.1d`

### https://www.moncucco.ch/anestesiologia.asp
- Section: clinics · Title: Clinica Luganese Moncucco - Anestesia
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
    - `mailto_link`: `anestesiaambulatorio.cm@moncucco.ch`
    - `mailto_link`: `anestesiaambulatorio.csc@moncucco.ch`
    - `plain_email`: `anestesiaambulatorio.cm@moncucco.ch`
    - `plain_email`: `anestesiaambulatorio.csc@moncucco.ch`
    - `base64_email_candidate`: `ch/immaginiSpecializzazioni/mon`
    - `base64_email_candidate`: `ch/fonts/fontawesome/css/fontawesome`
- Contact links: [('https://www.moncucco.ch/contatti.php', 3)]
- Best contact page: https://www.moncucco.ch/contatti.php (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'recaptcha']
      - `mailto_link`: `info@moncucco.ch`
      - `plain_email`: `info@moncucco.ch`
      - `base64_email_candidate`: `ch/fonts/fontawesome/css/fontawesome`
      - `base64_email_candidate`: `3fr3allyFk5hKegzpSvElE3g`
      - `contact_form`: `<form`
      - `recaptcha`: `g-recaptcha`
      - `recaptcha`: `grecaptcha`

### https://praxis-gruppe.ch/praxen/praxis-gruppe-lenzburg/
- Section: medClinics · Title: Praxis Dr. med. Jonas Alexander
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `lenzburg@praxis-gruppe.ch`
    - `plain_email`: `lenzburg@praxis-gruppe.ch`
    - `plain_email`: `seon@praxis-gruppe.ch`
    - `base64_email_candidate`: `content/uploads/2022/10/csm`
    - `base64_email_candidate`: `PropertyValueSpecification`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-json`
- Contact links: [('https://praxis-gruppe.ch/praxen/praxis-gruppe-lenzburg/kontakt/', 3), ('https://praxis-gruppe.ch/impressum', 3), ('https://praxis-gruppe.ch/datenschutz', 3)]
- Best contact page: https://praxis-gruppe.ch/praxen/praxis-gruppe-lenzburg/kontakt/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `lenzburg@praxis-gruppe.ch`
      - `mailto_link`: `pgs.lenzburg@hin.ch`
      - `plain_email`: `lenzburg@praxis-gruppe.ch`
      - `plain_email`: `pgs.lenzburg@hin.ch`
      - `base64_email_candidate`: `content/uploads/2022/10/schweiz`
      - `base64_email_candidate`: `PropertyValueSpecification`
      - `contact_form`: `<form`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-json`

### https://www.berdou-urocare.ch/
- Section: medClinics · Title: Praxis Dr. med. Berdou Roger
- **Errors**: ['HTTP 404']
- Homepage status: 404 · server: `Pepyaka`

### https://www.hirslanden.ch/de/klinik-st--anna/fachgebiete/zahnmedizin.html
- Section: clinics · Title: Hirslanden Klinik St. Anna - Zahnmedizinische Klinik
- Homepage status: 200 · server: ``
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc']
    - `base64_email_candidate`: `pZf8AJotu170CGkRficPELOVnLHjB4dcwhVuBP1QVOR3`
    - `base64_email_candidate`: `rGp51yAdfkNkMjCMv8XpFZHl9JJy2jzT1OPFuypH`
    - `contact_form`: `<form`
    - `cookiebot_etc`: `OneTrust`
- Contact links: [('https://www.hirslanden.ch/de/klinik-st--anna/kontakt.html', 3), ('https://www.hirslanden.ch/de/klinik-st--anna/jobs-und-karriere/team-hr.html', 3), ('https://www.hirslanden.ch/de/corporate/datenschutzerklaerung.html', 3), ('https://www.hirslanden.ch/de/corporate/impressum.html', 3), ('https://www.hirslanden.ch/de/klinik-st--anna/versicherung.html', 1)]
- Best contact page: https://www.hirslanden.ch/de/klinik-st--anna/kontakt.html (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'mailto_link', 'plain_email']
      - `mailto_link`: `klinik-stanna@hirslanden.ch`
      - `mailto_link`: `meggen.stanna@hirslanden.ch`
      - `plain_email`: `klinik-stanna@hirslanden.ch`
      - `plain_email`: `meggen.stanna@hirslanden.ch`
      - `base64_email_candidate`: `pZf8AJotu170CGkRficPELOVnLHjB4dcwhVuBP1QVOSjOy`
      - `base64_email_candidate`: `nOjigMalp41ZHnHRP4oTRz2yaanjN3kUnXkQFzw`
      - `contact_form`: `<form`
      - `cookiebot_etc`: `OneTrust`

### https://www.aerztewaedenswil.ch/de/Home/Aerzte.3.html?aid=45
- Section: medClinics · Title: Praxis Roth Götz
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
    - `mailto_link`: `goetz.roth@gmx.net`
    - `plain_email`: `goetz.roth@gmx.net`
    - `base64_email_candidate`: `org/TR/xhtml1/DTD/xhtml1`
    - `base64_email_candidate`: `/jslib/jScrollPane2/custom/jquery`

### http://www.brestel.ch/
- Section: medClinics · Title: Praxis Dr. med. Brestel Rolf
- Homepage status: 200 · server: `CM4all Webserver`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
    - `mailto_link`: `praxis%40brestel.ch`
    - `mailto_link`: `praxis@brestel.ch`
    - `plain_email`: `praxis@brestel.ch`
    - `base64_email_candidate`: `com/beng/designs/data/sys/cm`
    - `base64_email_candidate`: `cm4all/e/static/3rdparty/font`
- Contact links: [('https://www.brestel.ch/Team/', 3), ('https://www.brestel.ch/Kontakt/', 3), ('https://www.brestel.ch/Team/Dr-med-Rolf-Brestel/index.php/', 3), ('https://www.brestel.ch/Datenschutz/', 3), ('https://www.brestel.ch/Team/Dr-med-Rolf-Brestel/', 2)]
- Best contact page: https://www.brestel.ch/Team/ (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
      - `mailto_link`: `praxis%40brestel.ch`
      - `mailto_link`: `praxis@brestel.ch`
      - `plain_email`: `praxis@brestel.ch`
      - `base64_email_candidate`: `com/beng/designs/data/sys/cm`
      - `base64_email_candidate`: `cm4all/e/static/3rdparty/font`

### https://www.praxispfluggaesslein.ch/
- Section: groupPractices · Title: Praxis Pfluggässlein
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `praxispfluggaesslein@hin.ch`
    - `plain_email`: `praxispfluggaesslein@hin.ch`
    - `base64_email_candidate`: `content/plugins/responsive`
    - `base64_email_candidate`: `lightbox/assets/swipebox/swipebox`
    - `wordpress`: `wp-json`
    - `wordpress`: `wp-includes`
- Contact links: [('https://www.praxispfluggaesslein.ch/portrait/team/', 3), ('https://www.praxispfluggaesslein.ch/kontakt/', 3), ('https://www.praxispfluggaesslein.ch/impressum/', 3), ('https://www.praxispfluggaesslein.ch/datenschutz/', 3)]
- Best contact page: https://www.praxispfluggaesslein.ch/portrait/team/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `praxispfluggaesslein@hin.ch`
      - `plain_email`: `praxispfluggaesslein@hin.ch`
      - `base64_email_candidate`: `content/plugins/responsive`
      - `base64_email_candidate`: `lightbox/assets/swipebox/swipebox`
      - `contact_form`: `<form`
      - `wordpress`: `wp-json`
      - `wordpress`: `wp-includes`

### https://www.lindenhofgruppe.ch/de/unsere-aerzte/aerzte/marco-travaglini.php
- Section: medClinics · Title: Praxis Dr. med. Travaglini Marco
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'plain_email']
    - `plain_email`: `b68b13cf-3e16c5a5@560w.jpg`
    - `plain_email`: `b68b13cf-3e16c5a5@800w2x.jpg`
    - `base64_email_candidate`: `ch/wAssets/img/aerzte/weblication/wThumbnails/fb6fbed5fb6f561g00faddd128f45e7b`
    - `base64_email_candidate`: `/wGlobal/wGlobal/layout/images/site`
    - `contact_form`: `<form`
- Contact links: [('https://www.lindenhofgruppe.ch/de/fachgebiete/schmerzsprechstunde/kontakt/', 5), ('https://www.lindenhofgruppe.ch/de/ueber-uns/', 3), ('https://www.lindenhofgruppe.ch/de/kontakt/', 3), ('https://www.lindenhofgruppe.ch/de/fachgebiete/allgemeine-innere-medizin/kontakt/', 3), ('https://www.lindenhofgruppe.ch/de/fachgebiete/anaesthesiologie/kontakt/', 3)]
- Best contact page: https://www.lindenhofgruppe.ch/de/fachgebiete/schmerzsprechstunde/kontakt/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'plain_email']
      - `plain_email`: `8745cfb6-d8b40d01-mh698@2048w.jpg`
      - `plain_email`: `8745cfb6-d8b40d01-mh1396@2048w2x.jpg`
      - `base64_email_candidate`: `ch/de/fachgebiete/schmerzsprechstunde/kontakt/`
      - `base64_email_candidate`: `/wGlobal/wGlobal/layout/images/site`
      - `contact_form`: `<form`

### https://www.derbauch.ch/
- Section: groupPractices · Title: Bauchzentrum Rüti
- Homepage status: 200 · server: `cloudflare`
- Homepage patterns: ['base64_email_candidate', 'cf_email_protect', 'mailto_link', 'plain_email']
    - `mailto_link`: `gastro@derbauch.ch`
    - `cf_email_protect`: `/cdn-cgi/l/email-protection`
    - `plain_email`: `gastro@derbauch.ch`
    - `base64_email_candidate`: `com/app/cms/image/transf/none/path/s97079affc6f3b504/backgroundarea/i5f7bce28568e1f24/version/1552137052/image`
    - `base64_email_candidate`: `com/cms/o/s97079affc6f3b504/img/favicon`
- Contact links: [('https://www.derbauch.ch/kontakt/', 3), ('https://www.derbauch.ch/team-1/', 3), ('https://www.derbauch.ch/impressum/', 3), ('https://www.derbauch.ch/team/', 2), ('https://www.derbauch.ch/team/mitarbeiterinnen/', 2)]
- Best contact page: https://www.derbauch.ch/kontakt/ (status 200)
  - patterns: ['base64_email_candidate', 'cf_cfemail', 'cf_email_protect', 'plain_email']
      - `cf_cfemail`: `afc8cedcdbddc0efcbcaddcdcedaccc781ccc7`
      - `cf_cfemail`: `1f7c77766d6a6d78767a5f7b7a6d7d7e6a7c77317c77`
      - `cf_email_protect`: `/cdn-cgi/l/email-protection`
      - `plain_email`: `gastro@derbauch.ch`
      - `plain_email`: `chirurgie@derbauch.ch`
      - `base64_email_candidate`: `com/app/cms/image/transf/none/path/s97079affc6f3b504/backgroundarea/i5f7bce28568e1f24/version/1552137052/image`
      - `base64_email_candidate`: `com/cms/o/s97079affc6f3b504/img/favicon`

### https://www.bethesda-spital.ch/de/medizinisches-angebot/anaesthesie.html
- Section: hospitals · Title: Bethesda Spital Basel - Anästhesie Allgemein
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'html_entity_at_dec', 'html_entity_dot_dec', 'plain_email']
    - `html_entity_at_dec`: `&#64;`
    - `html_entity_dot_dec`: `&#46;`
    - `plain_email`: `ana@bethesda-spital.ch`
    - `plain_email`: `notexisting@nodomain.com`
    - `base64_email_candidate`: `module/webresources/css/fonts`
    - `base64_email_candidate`: `module/webresources/css/app`
    - `contact_form`: `kontaktformular`
    - `contact_form`: `Kontaktformular`
- Contact links: [('https://www.bethesda-spital.ch/de/ueber-uns/mitarbeitende/staff/portrait/spital/weitere/carla-fernandes.html', 5), ('https://www.bethesda-spital.ch/de/ueber-uns/kontaktformular.html', 5), ('https://www.bethesda-spital.ch/de/ueber-uns/impressum.html', 5), ('https://www.bethesda-spital.ch/de/ueber-uns/datenschutz.html', 5), ('https://www.bethesda-spital.ch/de/ueber-uns/mitarbeitende/staff/portrait/spital/chefaerzte/henrik-sjoestroem.html', 4)]
- Best contact page: https://www.bethesda-spital.ch/de/ueber-uns/mitarbeitende/staff/portrait/spital/weitere/carla-fernandes.html (status 200)
  - patterns: ['base64_email_candidate', 'contact_form']
      - `base64_email_candidate`: `uns/mitarbeitende/staff/portrait/spital/weitere/carla`
      - `base64_email_candidate`: `theme/small/dam/spital/de/Mitarbeitende/Fernandes`
      - `contact_form`: `kontaktformular`
      - `contact_form`: `Kontaktformular`

### https://www.centremtheytaz.ch/
- Section: groupPractices · Title: Centre Maurice Theytaz
- Homepage status: 200 · server: `webnode`
- Homepage patterns: ['base64_email_candidate', 'cookiebot_etc', 'mailto_link', 'plain_email']
    - `mailto_link`: `info@centremtheytaz.ch`
    - `plain_email`: `info@centremtheytaz.ch`
    - `plain_email`: `contact@example.com`
    - `base64_email_candidate`: `com/da9d8bedf970aa1ba5fad37aa6234e78/200000150`
    - `base64_email_candidate`: `com/da9d8bedf970aa1ba5fad37aa6234e78/200000125`
    - `cookiebot_etc`: `iubenda`
- Contact links: [('https://www.centremtheytaz.ch/equipe/', 3), ('https://www.centremtheytaz.ch/contact/', 3)]
- Best contact page: https://www.centremtheytaz.ch/equipe/ (status 200)
  - patterns: ['base64_email_candidate', 'cookiebot_etc', 'mailto_link', 'plain_email']
      - `mailto_link`: `vincentpequignot@me.com`
      - `mailto_link`: `lpequignot@centremtheytaz.ch`
      - `plain_email`: `vincentpequignot@me.com`
      - `plain_email`: `lpequignot@centremtheytaz.ch`
      - `base64_email_candidate`: `com/da9d8bedf970aa1ba5fad37aa6234e78/200000071`
      - `base64_email_candidate`: `com/da9d8bedf970aa1ba5fad37aa6234e78/200000138`
      - `cookiebot_etc`: `iubenda`

### https://www.pzhi.ch/zuweisende-und-fachpersonen/angebot/spital/
- Section: hospitals · Title: Hildegard-Hospiz Spital-Stiftung - Palliativmedizin
- **Errors**: ['HTTPSConnectionPool(host=\'www.pzhi.ch\', port=443): Max retries exceeded with url: /zuweisende-und-fachpersonen/angebot/spital/ (Caused by SSLError(SSLCertVerificationError(1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for \'www.pzhi.ch\'. (_ssl.c:1032)")))']
- Homepage status: ? · server: ``

### https://praxisamschanzweg.ch/
- Section: groupPractices · Title: Praxis Dr. Geiges
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'squarespace', 'wordpress']
    - `base64_email_candidate`: `openingHoursSpecification`
    - `base64_email_candidate`: `OpeningHoursSpecification`
    - `wordpress`: `wp-json`
    - `wordpress`: `wp-content`
    - `squarespace`: `squarespace`
- Contact links: [('https://praxisamschanzweg.ch/impressum-datenschutzerklaerung', 5), ('https://praxisamschanzweg.ch/', 1)]
- Best contact page: https://praxisamschanzweg.ch/impressum-datenschutzerklaerung/ (status 200)
  - patterns: ['base64_email_candidate', 'recaptcha', 'squarespace', 'wordpress']
      - `base64_email_candidate`: `datenschutzerklaerung/feed/`
      - `base64_email_candidate`: `content/themes/Divi/includes/builder/styles/images/preloader`
      - `recaptcha`: `grecaptcha`
      - `wordpress`: `wp-json`
      - `wordpress`: `wp-content`
      - `squarespace`: `squarespace`

### https://www.neuchatelfamille.ch/N155214/centre-d-information-de-prevention-et-de-traitement-des-addictions-drop-in.html
- Section: groupPractices · Title: DROP-IN - Centre d'information, de prévention et de traitement des addictions
- Homepage status: 200 · server: `Microsoft-IIS/8.5`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'html_entity_at_dec', 'html_entity_at_hex', 'html_entity_dot_hex', 'mailto_link', 'plain_email']
    - `mailto_link`: `i&#x6E;&#x66;&#111;&#64;d&#114;op-&#105;&#x6E;.c&#x68;`
    - `mailto_link`: `info@neuchatelfamille.ch`
    - `html_entity_at_dec`: `&#64;`
    - `html_entity_at_hex`: `&#x40;`
    - `html_entity_dot_hex`: `&#x2E;`
    - `plain_email`: `info@neuchatelfamille.ch`
    - `base64_email_candidate`: `UckCPvH8ZES5FDuR6p1ELDBU36MbaE`
    - `base64_email_candidate`: `F3inoFgRRPDZtlz46IbkkSMBqkMeANBH5sE`
    - `contact_form`: `<form`
- Contact links: [('https://www.neuchatelfamille.ch/N5302/maison-decoration-equipement-bibelots-et-cadeaux.html?M=2204871', 3), ('https://www.neuchatelfamille.ch/N7710/contacts.html', 3)]
- Best contact page: https://www.neuchatelfamille.ch/N5302/maison-decoration-equipement-bibelots-et-cadeaux.html?M=2204871 (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'recaptcha']
      - `mailto_link`: `info@neuchatelfamille.ch`
      - `plain_email`: `info@neuchatelfamille.ch`
      - `base64_email_candidate`: `UckCPvH8ZES5FDuR6p1ELDBU36MbaE`
      - `base64_email_candidate`: `F3inoFgRRPDZtlz46IbkkSMBqkMeANBH5sE`
      - `contact_form`: `<form`
      - `recaptcha`: `g-recaptcha`

### https://vista.ch/standort/aivla-vista-augenpraxis-st-moritz/
- Section: groupPractices · Title: Aivla Vista Augenpraxis St. Moritz
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `augenpraxis.aivla@vista.ch`
    - `plain_email`: `augenpraxis.aivla@vista.ch`
    - `base64_email_candidate`: `includes/js/jquery/jquery`
    - `base64_email_candidate`: `AIzaSyD2mJ9XqqqBjhXfsLTKR0P6v875`
    - `contact_form`: `id='contact`
    - `contact_form`: `<form`
    - `wordpress`: `wp-json`
    - `wordpress`: `wp-content`
- Contact links: [('https://vista.ch/ueber-uns/kontakt/', 5), ('https://vista.ch/ueber-uns/', 3), ('https://vista.ch/impressum/', 3), ('https://vista.ch/datenschutzerklaerung/', 3), ('https://vista.ch/ueber-uns/klinische-forschung/', 2)]
- Best contact page: https://vista.ch/ueber-uns/kontakt/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `qm@vista.ch`
      - `mailto_link`: `Samuel.Steiner@vista.ch`
      - `plain_email`: `qm@vista.ch`
      - `plain_email`: `Samuel.Steiner@vista.ch`
      - `base64_email_candidate`: `content/uploads/2026/01/steiner`
      - `base64_email_candidate`: `includes/js/jquery/jquery`
      - `contact_form`: `id='contact`
      - `contact_form`: `<form`
      - `wordpress`: `wp-json`
      - `wordpress`: `wp-content`

### https://www.stadt-zuerich.ch/stadtspital/de/leistungsangebot/intensivmedizin/Intensivstationen.html
- Section: hospitals · Title: Stadtspital Waid Zürich - Intensiv
- **Errors**: ['HTTP 404']
- Homepage status: 404 · server: `Server`

### https://www.hausarztpraxis-binningen.ch/
- Section: groupPractices · Title: Hausarztpraxis Binningen
- Homepage status: 200 · server: `Pepyaka`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wix']
    - `mailto_link`: `hausarztpraxis-binningen@hin.ch`
    - `plain_email`: `hausarztpraxis-binningen@hin.ch`
    - `plain_email`: `605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com`
    - `base64_email_candidate`: `componentsLibrariesTopology`
    - `base64_email_candidate`: `isRunningInDifferentSiteContext`
    - `contact_form`: `<form`
    - `wix`: `static.wixstatic`
- Contact links: [('https://www.hausarztpraxis-binningen.ch/datenschutz', 3), ('https://www.hausarztpraxis-binningen.ch/kontakt', 3), ('https://www.hausarztpraxis-binningen.ch/praxis', 1)]
- Best contact page: https://www.hausarztpraxis-binningen.ch/datenschutz (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wix']
      - `mailto_link`: `hausarztpraxis-binningen@hin.ch`
      - `plain_email`: `hausarztpraxis-binningen@hin.ch`
      - `plain_email`: `605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com`
      - `base64_email_candidate`: `componentsLibrariesTopology`
      - `base64_email_candidate`: `isRunningInDifferentSiteContext`
      - `wix`: `static.wixstatic`

### https://kaldune.ch/dr-med-andreas-kaldune/
- Section: medClinics · Title: Praxis Dr. med. Kaldune Andreas Erwin
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `a.kaldune@hin.ch`
    - `mailto_link`: `aselbkal@hin.ch`
    - `plain_email`: `a.kaldune@hin.ch`
    - `plain_email`: `aselbkal@hin.ch`
    - `base64_email_candidate`: `content/uploads/2023/08/websitenow`
    - `base64_email_candidate`: `PropertyValueSpecification`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-includes`
- Contact links: [('https://kaldune.ch/dr-med-andreas-kaldune/kontakt/', 3), ('https://kaldune.ch/dipl-psych-anja-selb-kaldune/kontakt/', 3), ('https://kaldune.ch/impressum', 3), ('https://kaldune.ch/datenschutzerklarung/', 3)]
- Best contact page: https://kaldune.ch/dr-med-andreas-kaldune/kontakt/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'recaptcha', 'wordpress']
      - `mailto_link`: `a.kaldune@hin.ch`
      - `mailto_link`: `aselbkal@hin.ch`
      - `plain_email`: `a.kaldune@hin.ch`
      - `plain_email`: `aselbkal@hin.ch`
      - `base64_email_candidate`: `content/uploads/2023/08/websitenow`
      - `base64_email_candidate`: `PropertyValueSpecification`
      - `contact_form`: `<form`
      - `recaptcha`: `g-recaptcha`
      - `recaptcha`: `grecaptcha`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-includes`

### https://praxis-seuzach.ch/
- Section: groupPractices · Title: Hausarztpraxis Birchstrasse 2
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'recaptcha', 'text_at_brackets', 'wordpress']
    - `text_at_brackets`: `cbguf[at]uva.pu`
    - `text_at_brackets`: `srrqonpx[at]cenkvf-frhmnpu.pu`
    - `base64_email_candidate`: `content/uploads/2025/03/logo`
    - `base64_email_candidate`: `content/uploads/2020/10/cropped`
    - `contact_form`: `id='contact`
    - `contact_form`: `<form`
    - `recaptcha`: `g-recaptcha`
    - `recaptcha`: `grecaptcha`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-json`
- Contact links: [('https://praxis-seuzach.ch/datenschutzerklaerung/', 3)]
- Best contact page: https://praxis-seuzach.ch/datenschutzerklaerung/ (status 200)
  - patterns: ['base64_email_candidate', 'wordpress']
      - `base64_email_candidate`: `ch/datenschutzerklaerung/`
      - `base64_email_candidate`: `Datenschutzgrundverordnung`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-json`

### https://www.solothurnerspitaeler.ch/unsere-spitaeler/kantonsspital-olten/medizinisches-angebot/innere-medizin/haematologie
- Section: hospitals · Title: Kantonsspital Olten - Hämatologie
- Homepage status: 200 · server: `cloudflare`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'typo3']
    - `base64_email_candidate`: `qwv6adkqi8qvbut2q4wkged777sacr`
    - `base64_email_candidate`: `/assets/images/accordion/arrow`
    - `contact_form`: `<form`
    - `contact_form`: `kontaktformular`
    - `typo3`: `typo3conf`
    - `cookiebot_etc`: `usercentrics`
- Contact links: [('https://www.solothurnerspitaeler.ch/system/e-mail-kontaktformular?addressType=department&addressUid=15&cHash=e88b480e9bf957098ddcc54120fec1f5', 3), ('https://www.solothurnerspitaeler.ch/system/e-mail-kontaktformular?addressType=manual&addressUid=9&cHash=aa828a320a8ab8636969fe34ff9199e0', 3), ('https://www.solothurnerspitaeler.ch/organisation/kontakt-fuer-lieferanten-versicherungen', 3), ('https://www.solothurnerspitaeler.ch/footer/impressum', 3), ('https://www.solothurnerspitaeler.ch/footer/disclaimerdatenschutz', 3)]
- Best contact page: https://www.solothurnerspitaeler.ch/system/e-mail-kontaktformular?addressType=department&addressUid=15&cHash=e88b480e9bf957098ddcc54120fec1f5 (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'recaptcha', 'typo3']
      - `base64_email_candidate`: `qwv6adkqi8qvbut2q4wkged777sacr`
      - `base64_email_candidate`: `/assets/images/accordion/arrow`
      - `contact_form`: `Kontaktformular`
      - `contact_form`: `kontaktformular`
      - `recaptcha`: `g-recaptcha`
      - `typo3`: `typo3conf`
      - `typo3`: `typo3temp`
      - `cookiebot_etc`: `usercentrics`

### https://www.hochgebirgsklinik.ch/
- Section: clinics · Title: Hochgebirgsklinik Davos - Kinderklinik
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `info@hgk.ch`
    - `plain_email`: `info@hgk.ch`
    - `base64_email_candidate`: `data/c40df9203fa76f82fe1f4456/script`
    - `base64_email_candidate`: `content/uploads/2024/10/HGK`
    - `contact_form`: `id='contact`
    - `contact_form`: `id="contact`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-includes`
- Contact links: [('https://hochgebirgsklinik.ch/ueber-uns/kontakt/', 5), ('https://hochgebirgsklinik.ch/ueber-uns/', 3), ('https://hochgebirgsklinik.ch/datenschutzerklaerung/', 3), ('https://hochgebirgsklinik.ch/impressum/', 3), ('https://hochgebirgsklinik.ch/ueber-uns/news/', 2)]
- Best contact page: https://hochgebirgsklinik.ch/ueber-uns/kontakt/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `info@hgk.ch`
      - `mailto_link`: `ambulatorium@hgk.ch`
      - `plain_email`: `info@hgk.ch`
      - `plain_email`: `ambulatorium@hgk.ch`
      - `base64_email_candidate`: `data/c40df9203fa76f82fe1f4456/script`
      - `base64_email_candidate`: `content/uploads/2024/11/hochgebirgsklinik`
      - `contact_form`: `id='contact`
      - `contact_form`: `kontaktformular`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-includes`

### https://www.dr-vanhoute.ch/
- Section: medClinics · Title: Praxis Dr. med. Van Houte Michael
- **Errors**: ['HTTP 403']
- Homepage status: 403 · server: `nginx`

### https://cmmv.ch/
- Section: medicalCenters · Title: Centre Médical Meyrin Village - 2ème étage
- Homepage status: 200 · server: `Apache/2.4.25 (Debian)`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
    - `mailto_link`: `secretariat@cmmv.ch`
    - `plain_email`: `secretariat@cmmv.ch`
    - `base64_email_candidate`: `generaliste/meyrin/pcoz5/dr`
    - `base64_email_candidate`: `generale/meyrin/pcr7h/dr`

### https://www.cmduchevalblanc.ch/
- Section: medClinics · Title: Cabinet médical du Cheval-Blanc
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
    - `mailto_link`: `cmduchevalblanc@amge.ch`
    - `plain_email`: `cmduchevalblanc@amge.ch`
    - `base64_email_candidate`: `66cdaf3637c242b2a4699357`
    - `base64_email_candidate`: `66cdaf3537c242b2a4699321`
    - `contact_form`: `id="contact`
    - `contact_form`: `<form`
- Contact links: [('https://www.cmduchevalblanc.ch/equipe/dre-elisabeth-de-preux.html', 2), ('https://www.cmduchevalblanc.ch/equipe/jessica-leocata.html', 2), ('https://www.cmduchevalblanc.ch/equipe/dre-maud-tartarat.html', 2), ('https://www.cmduchevalblanc.ch/equipe.html', 2), ('https://www.cmduchevalblanc.ch/', 1)]
- Best contact page: https://www.cmduchevalblanc.ch/equipe/dre-elisabeth-de-preux.html (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
      - `mailto_link`: `cmduchevalblanc@amge.ch`
      - `plain_email`: `cmduchevalblanc@amge.ch`
      - `base64_email_candidate`: `66e14ff1bb001b3c65db8aad`
      - `base64_email_candidate`: `66cdaf3537c242b2a4699321`

### https://www.praxiszentrumamrheinfall.ch/
- Section: medicalCenters · Title: Praxiszentrum am Rheinfall
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `info@praxiszentrumamrheinfall.ch</span`
    - `mailto_link`: `info@praxiszentrumamrheinfall.ch`
    - `plain_email`: `info@praxiszentrumamrheinfall.ch`
    - `base64_email_candidate`: `praxiszentrumamrheinfall`
    - `base64_email_candidate`: `content/uploads/2026/03/Bild`
    - `contact_form`: `id='contact`
    - `contact_form`: `id="contact`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-json`
- Contact links: [('https://www.praxiszentrumamrheinfall.ch/kontakt/', 3), ('https://www.praxiszentrumamrheinfall.ch/impressum_disclaimer/', 3), ('https://www.praxiszentrumamrheinfall.ch/datenschutz/', 3), ('https://www.praxiszentrumamrheinfall.ch/impressum_disclaimer', 3), ('https://www.praxiszentrumamrheinfall.ch/datenschutz', 3)]
- Best contact page: https://www.praxiszentrumamrheinfall.ch/kontakt/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `info@praxiszentrumamrheinfall.ch</span`
      - `plain_email`: `info@praxiszentrumamrheinfall.ch`
      - `plain_email`: `praxiszentrumamrheinfall@hin.ch`
      - `base64_email_candidate`: `praxiszentrumamrheinfall`
      - `base64_email_candidate`: `PropertyValueSpecification`
      - `contact_form`: `id='contact`
      - `contact_form`: `kontaktformular`
      - `wordpress`: `wp-json`
      - `wordpress`: `wp-content`

### https://praxis-tomaschett.ch/
- Section: medClinics · Title: Praxis Dr. med. Tomaschett Martin Paul
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `praxis.tomaschett@hin.ch`
    - `plain_email`: `praxis.tomaschett@hin.ch`
    - `base64_email_candidate`: `org/TR/xhtml1/DTD/xhtml1`
    - `base64_email_candidate`: `content/themes/tomaschett/style`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-includes`
- Contact links: [('https://praxis-tomaschett.ch/team-2/', 3), ('https://praxis-tomaschett.ch/kontakt/', 3)]
- Best contact page: https://praxis-tomaschett.ch/team-2/ (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `praxis.tomaschett@hin.ch`
      - `plain_email`: `praxis.tomaschett@hin.ch`
      - `base64_email_candidate`: `org/TR/xhtml1/DTD/xhtml1`
      - `base64_email_candidate`: `content/themes/tomaschett/style`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-includes`

### https://www.swissmedical.net/en/hospitals/valere/centres/radiology
- Section: clinics · Title: Clinique Valère Sion - Radiologie Clinique
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
    - `mailto_link`: `info@cliniquevalere.ch`
    - `mailto_link`: `crv@cliniquevalere.ch`
    - `plain_email`: `info@cliniquevalere.ch`
    - `plain_email`: `crv@cliniquevalere.ch`
    - `base64_email_candidate`: `/site/templates/public/img/favicon/apple`
    - `base64_email_candidate`: `/site/templates/public/img/favicon/favicon`
    - `contact_form`: `<form`
- Contact links: [('https://www.swissmedical.net/en/hospitals/valere/about', 3), ('https://www.swissmedical.net/en/legal-notice', 3), ('https://www.swissmedical.net/en/hospitals/valere/contact', 2), ('https://www.swissmedical.net/en/hospitals/valere/about/medical-infrastructure', 2), ('https://www.swissmedical.net/en/hospitals/valere/about/organization', 2)]
- Best contact page: https://www.swissmedical.net/en/hospitals/valere/about (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
      - `mailto_link`: `info@cliniquevalere.ch`
      - `plain_email`: `info@cliniquevalere.ch`
      - `base64_email_candidate`: `/site/templates/public/img/favicon/apple`
      - `base64_email_candidate`: `/site/templates/public/img/favicon/favicon`
      - `contact_form`: `<form`

### https://www.hirslanden.ch/fr/clinique-des-grangettes/centres-et-instituts/radio-oncologie.html
- Section: clinics · Title: Clinique des Grangettes - Radio-oncologie
- Homepage status: 200 · server: ``
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'mailto_link', 'plain_email']
    - `mailto_link`: `secretariat.radiotherapie@grangettes.ch`
    - `plain_email`: `secretariat.radiotherapie@grangettes.ch`
    - `base64_email_candidate`: `cYzAaC64lNRaO15boxdobBlBoMJUUgZaZZh3PNQsAQGs1l`
    - `base64_email_candidate`: `VPawL1wEMx6IM1XJGYLYdz98P1VB0HHDbwRLB5WKCYXcRbqtdJl2yGqrXuM4FJ9`
    - `contact_form`: `<form`
    - `cookiebot_etc`: `OneTrust`
- Contact links: [('https://www.hirslanden.ch/fr/corporate/a-propos-de-nous/contact/healthline.html', 4), ('https://www.hirslanden.ch/fr/corporate/mentions-legales.html', 4), ('https://www.hirslanden.ch/fr/clinique-des-grangettes/contact.html', 3), ('https://www.hirslanden.ch/fr/clinique-des-grangettes/centres-et-instituts/radio-oncologie/equipe.html', 2), ('https://www.hirslanden.ch/fr/clinique-des-grangettes/centres-et-instituts/radio-oncologie/contact.html', 2)]
- Best contact page: https://www.hirslanden.ch/fr/corporate/a-propos-de-nous/contact/healthline.html (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc']
      - `base64_email_candidate`: `9l8QO0aHyMuQlThSXbDEFm6FbtD1EVx6tz80C4RtKhfI7trmK2kljd5gk4rdm9FdXv2qprCKMPe`
      - `base64_email_candidate`: `clientlibs/hirslanden/clientlibs/frontend`
      - `contact_form`: `<form`
      - `cookiebot_etc`: `OneTrust`

### https://www.usz.ch/fachbereich/konsiliarpsychiatrie-psychosomatik/
- Section: hospitals · Title: Universitätsspital Zürich - Psych. Ambulatorium
- Homepage status: 200 · server: ``
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'html_entity_at_dec', 'html_entity_dot_dec', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `psy&#046;&#105;n&#102;o&#064;&#117;&#115;z.c&#104;`
    - `mailto_link`: `p&#115;&#121;.&#105;&#110;&#102;o&#064;&#117;&#115;z&#046;&#099;h`
    - `html_entity_at_dec`: `&#064;`
    - `html_entity_dot_dec`: `&#046;`
    - `plain_email`: `psy.info@usz.ch`
    - `base64_email_candidate`: `data/a1a8e2e62e34e015d2d084a5/script`
    - `base64_email_candidate`: `ch/fachbereich/konsiliarpsychiatrie`
    - `contact_form`: `<form`
    - `contact_form`: `Kontaktformular`
    - `wordpress`: `wp-includes`
    - `wordpress`: `generator" content="WordPress`
- Contact links: [('https://www.usz.ch/kontakt/', 3), ('https://www.usz.ch/team/', 3), ('https://www.usz.ch/fachbereich/konsiliarpsychiatrie-psychosomatik/team/', 3), ('https://www.usz.ch/fachbereich/konsiliarpsychiatrie-psychosomatik/ueber-uns/', 3), ('https://www.usz.ch/kontakt-fachbereiche/?to_email=fHvJMrGWCvFmDlNZ', 3)]
- Best contact page: https://www.usz.ch/kontakt/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'plain_email', 'wordpress']
      - `plain_email`: `usz-icon-warnung@2x.png`
      - `plain_email`: `usz-icon-kontakt@2x-1.png`
      - `base64_email_candidate`: `data/a1a8e2e62e34e015d2d084a5/script`
      - `base64_email_candidate`: `com/UniversitaetsspitalZuerich`
      - `contact_form`: `Kontaktformular`
      - `contact_form`: `<form`
      - `wordpress`: `wp-includes`
      - `wordpress`: `generator" content="WordPress`

### https://www.frauenpraxis-buelach.ch/
- Section: groupPractices · Title: Frauenpraxis Bülach
- Homepage status: 200 · server: `cloudflare`
- Homepage patterns: ['base64_email_candidate', 'cf_cfemail', 'cf_email_protect']
    - `cf_cfemail`: `e38a8d858ca385938196868f82808bcd808b`
    - `cf_email_protect`: `/cdn-cgi/l/email-protection`
    - `base64_email_candidate`: `com/app/cms/image/transf/dimension=`
    - `base64_email_candidate`: `jpg/path/sf201d8755fd7026c/image/i77ef7cada4925c1c/version/1763470340/image`
- Contact links: [('https://www.frauenpraxis-buelach.ch/team/', 3), ('https://www.frauenpraxis-buelach.ch/kontakt/', 3), ('https://www.frauenpraxis-buelach.ch/about/', 3), ('https://www.frauenpraxis-buelach.ch/j/privacy', 1)]
- Best contact page: https://www.frauenpraxis-buelach.ch/team/ (status 200)
  - patterns: ['base64_email_candidate', 'cf_cfemail', 'cf_email_protect']
      - `cf_cfemail`: `acc5c2cac3eccadcced9c9c0cdcfc482cfc4`
      - `cf_email_protect`: `/cdn-cgi/l/email-protection`
      - `base64_email_candidate`: `com/app/cms/image/transf/dimension=`
      - `base64_email_candidate`: `jpg/path/sf201d8755fd7026c/image/i5cb38ed9e586d22d/version/1763471391/image`

### https://www.neuropsychiatrie.ch/
- Section: groupPractices · Title: NeuroPsychiatrie.CH - Einkaufszentrum Glatt
- Homepage status: 200 · server: `Squarespace`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'squarespace']
    - `mailto_link`: `neuropsychiatrie@hin.ch`
    - `plain_email`: `user@domain.com`
    - `plain_email`: `neuropsychiatrie@hin.ch`
    - `base64_email_candidate`: `com/content/v1/5a3615198a02c74fc8502cbe/1513495842792`
    - `base64_email_candidate`: `WN1BNZVZLS544MK7LZZP/favicon`
    - `contact_form`: `<form`
    - `squarespace`: `Squarespace`
    - `squarespace`: `squarespace`
- Contact links: [('https://www.neuropsychiatrie.ch/psychiatrische-sprechstunde', 3), ('https://www.neuropsychiatrie.ch/neuropsychologische-sprechstunde', 3), ('https://www.neuropsychiatrie.ch/Sprechstunden', 3), ('https://www.neuropsychiatrie.ch/ueber-uns', 3), ('https://www.neuropsychiatrie.ch/impressum', 3)]
- Best contact page: https://www.neuropsychiatrie.ch/psychiatrische-sprechstunde (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'squarespace']
      - `mailto_link`: `neuropsychiatrie@hin.ch`
      - `plain_email`: `user@domain.com`
      - `plain_email`: `neuropsychiatrie@hin.ch`
      - `base64_email_candidate`: `com/content/v1/5a3615198a02c74fc8502cbe/1513495842792`
      - `base64_email_candidate`: `WN1BNZVZLS544MK7LZZP/favicon`
      - `contact_form`: `<form`
      - `squarespace`: `Squarespace`
      - `squarespace`: `squarespace`

### https://www.olivierlieger.ch/
- Section: medClinics · Title: Praxis PD Dr. Dr. med. Lieger Olivier
- Homepage status: 200 · server: `nginx-rc`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
    - `mailto_link`: `olivier.lie`
    - `plain_email`: `ger@hin.ch`
    - `base64_email_candidate`: `/application/themes/lieger/css/skins/default`
    - `base64_email_candidate`: `c9430b861b5e7a7e9463563aa33362c78f0c500f`
- Contact links: [('https://www.olivierlieger.ch/team', 3), ('https://www.olivierlieger.ch/kontakt', 3), ('https://www.olivierlieger.ch/impressum', 3), ('https://www.olivierlieger.ch/datenschutz', 3)]
- Best contact page: https://www.olivierlieger.ch/team (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
      - `mailto_link`: `olivier.lie`
      - `plain_email`: `ger@hin.ch`
      - `base64_email_candidate`: `/application/themes/lieger/css/skins/default`
      - `base64_email_candidate`: `c9430b861b5e7a7e9463563aa33362c78f0c500f`

### https://praxisgleis6.ch/team/
- Section: medClinics · Title: Orthopädische Praxis Axel Stamm
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'html_entity_at_dec', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `prax&#105;&#115;&#103;&#108;eis&#54;&#64;&#104;in.c&#104;`
    - `mailto_link`: `praxisgleis6@hin.ch`
    - `html_entity_at_dec`: `&#64;`
    - `plain_email`: `praxisgleis6@hin.ch`
    - `plain_email`: `physiogleis6@hin.ch`
    - `base64_email_candidate`: `content/uploads/2020/06/praxis`
    - `base64_email_candidate`: `content/uploads/2021/05/praxisgleis6`
    - `contact_form`: `<form`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-json`
- Contact links: [('https://praxisgleis6.ch/team/', 3), ('https://praxisgleis6.ch/kontakt/', 3), ('https://praxisgleis6.ch/impressum/', 3), ('https://praxisgleis6.ch/datenschutz/', 3), ('http://praxisgleis6.ch/kontakt/', 2)]
- Best contact page: https://praxisgleis6.ch/team/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'html_entity_at_dec', 'html_entity_dot_dec', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `&#112;r&#97;x&#105;s&#103;l&#101;is&#54;&#64;hi&#110;&#46;c&#104;`
      - `mailto_link`: `praxisgleis6@hin.ch`
      - `html_entity_at_dec`: `&#64;`
      - `html_entity_dot_dec`: `&#46;`
      - `plain_email`: `praxisgleis6@hin.ch`
      - `plain_email`: `physiogleis6@hin.ch`
      - `base64_email_candidate`: `content/uploads/2020/06/praxis`
      - `base64_email_candidate`: `content/uploads/2021/05/praxisgleis6`
      - `contact_form`: `<form`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-json`

### https://www.avagyn.ch/
- Section: medClinics · Title: AVA Gyn GmbH
- Homepage status: 200 · server: `Pepyaka`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wix']
    - `mailto_link`: `avagyn@hin.ch`
    - `plain_email`: `avagyn@hin.ch`
    - `plain_email`: `605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com`
    - `base64_email_candidate`: `fb6d3fe0f3194ff2bdad975689cf3fa6`
    - `base64_email_candidate`: `componentsLibrariesTopology`
    - `wix`: `static.wixstatic`
- Contact links: [('https://www.avagyn.ch/über-uns', 3), ('https://www.avagyn.ch/kontakt', 3), ('https://www.avagyn.ch/impressum', 3), ('https://www.avagyn.ch/datenschutzerklaerung', 3)]
- Best contact page: https://www.avagyn.ch/%C3%BCber-uns (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wix']
      - `mailto_link`: `avagyn@hin.ch`
      - `plain_email`: `avagyn@hin.ch`
      - `plain_email`: `605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com`
      - `base64_email_candidate`: `fb6d3fe0f3194ff2bdad975689cf3fa6`
      - `base64_email_candidate`: `componentsLibrariesTopology`
      - `wix`: `static.wixstatic`

### https://www.orl-silbergasse.ch/isabelle-giudicelli
- Section: medClinics · Title: Praxis Dr. med. Giudicelli-Tschumi Isabelle
- Homepage status: 200 · server: ``
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
    - `mailto_link`: `orl.silbergasse@hin.ch`
    - `plain_email`: `orl.silbergasse@hin.ch`
    - `base64_email_candidate`: `/assets/images/favicons/browserconfig`
    - `base64_email_candidate`: `/assets/images/favicons/apple`
- Contact links: [('https://www.orl-silbergasse.ch/impressum', 3), ('https://www.orl-silbergasse.ch/datenschutz', 3), ('https://www.orl-silbergasse.ch/', 1)]
- Best contact page: https://www.orl-silbergasse.ch/impressum (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
      - `mailto_link`: `orl.silbergasse@hin.ch`
      - `mailto_link`: `info@diff.ch`
      - `plain_email`: `orl.silbergasse@hin.ch`
      - `plain_email`: `info@diff.ch`
      - `base64_email_candidate`: `/assets/images/favicons/browserconfig`
      - `base64_email_candidate`: `/assets/images/favicons/apple`

### https://www.moncucco.ch/ematologia_emostasi.asp
- Section: clinics · Title: Clinica Luganese Moncucco - Ematologia
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
    - `mailto_link`: `ematologia.cm@moncucco.ch`
    - `mailto_link`: `poliambulatorio.csc@moncucco.ch`
    - `plain_email`: `ematologia.cm@moncucco.ch`
    - `plain_email`: `poliambulatorio.csc@moncucco.ch`
    - `base64_email_candidate`: `ch/immaginiSpecializzazioni/mon`
    - `base64_email_candidate`: `ch/fonts/fontawesome/css/fontawesome`
- Contact links: [('https://www.moncucco.ch/contatti.php', 3)]
- Best contact page: https://www.moncucco.ch/contatti.php (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'recaptcha']
      - `mailto_link`: `info@moncucco.ch`
      - `plain_email`: `info@moncucco.ch`
      - `base64_email_candidate`: `ch/fonts/fontawesome/css/fontawesome`
      - `base64_email_candidate`: `3fr3allyFk5hKegzpSvElE3g`
      - `contact_form`: `<form`
      - `recaptcha`: `g-recaptcha`
      - `recaptcha`: `grecaptcha`

### https://praxisamsee-gersau.ch/
- Section: medClinics · Title: Praxis Dr. med. De Groot Uwe
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'text_at_brackets', 'wordpress']
    - `mailto_link`: `praxisamsee-gersau@hin.ch`
    - `text_at_brackets`: `praxisamsee-gersau(at)hin.ch`
    - `plain_email`: `praxisamsee-gersau@hin.ch`
    - `base64_email_candidate`: `content/uploads/2020/05/cropped`
    - `base64_email_candidate`: `plugin/fonts/fontawesome/5`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-json`
- Contact links: [('https://praxisamsee-gersau.ch/team/', 3), ('https://praxisamsee-gersau.ch/kontakt/', 3), ('https://praxisamsee-gersau.ch/impressum/', 3), ('https://praxisamsee-gersau.ch/datenschutz/', 3)]
- Best contact page: https://praxisamsee-gersau.ch/team/ (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'text_at_brackets', 'wordpress']
      - `mailto_link`: `praxisamsee-gersau@hin.ch`
      - `text_at_brackets`: `praxisamsee-gersau(at)hin.ch`
      - `plain_email`: `praxisamsee-gersau@hin.ch`
      - `base64_email_candidate`: `content/uploads/2020/06/dr`
      - `base64_email_candidate`: `content/uploads/2020/06/team`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-json`

### https://www.praxis-behrens-kohl.ch/
- Section: groupPractices · Title: Gemeinschaftspraxis Dr. Claudia Behrens und Frau Dr. Christine Kohl
- Homepage status: 200 · server: `Pepyaka`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wix']
    - `mailto_link`: `praxis.behrens@hin.ch`
    - `mailto_link`: `praxis.kohl@hin.ch`
    - `plain_email`: `praxis.behrens@hin.ch`
    - `plain_email`: `praxis.kohl@hin.ch`
    - `base64_email_candidate`: `componentsLibrariesTopology`
    - `base64_email_candidate`: `isRunningInDifferentSiteContext`
    - `contact_form`: `kontaktformular`
    - `contact_form`: `Kontaktformular`
    - `wix`: `static.wixstatic`
- Contact links: [('https://www.praxis-behrens-kohl.ch/kontaktformular', 3), ('https://www.praxis-behrens-kohl.ch/impressum', 3), ('https://www.praxis-behrens-kohl.ch/datenschutz', 3), ('https://www.praxis-behrens-kohl.ch', 1)]
- Best contact page: https://www.praxis-behrens-kohl.ch/kontaktformular (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'plain_email', 'wix']
      - `plain_email`: `605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com`
      - `base64_email_candidate`: `componentsLibrariesTopology`
      - `base64_email_candidate`: `isRunningInDifferentSiteContext`
      - `contact_form`: `kontaktformular`
      - `contact_form`: `Kontaktformular`
      - `wix`: `static.wixstatic`

### https://cseb.ch/betriebe/ospidal/
- Section: hospitals · Title: Ospidal Scuol, Center da sandà Engiadina Bassa - Ginecologica
- Homepage status: 200 · server: ``
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `ospidal@cseb.ch`
    - `mailto_link`: `info@cseb.ch`
    - `plain_email`: `ospidal@cseb.ch`
    - `plain_email`: `info@cseb.ch`
    - `base64_email_candidate`: `data/41042a57ce53cfa12fe37f2e/script`
    - `base64_email_candidate`: `ch/rm/intrapraisas/ospidal/lospidal/`
    - `contact_form`: `<form`
    - `wordpress`: `wp-includes`
    - `wordpress`: `wp-content`
- Contact links: [('https://cseb.ch/service/medienkontakt/', 3), ('https://cseb.ch/impressum/', 3), ('https://cseb.ch/datenschutzerklaerung/', 3), ('https://cseb.ch/betriebe/clinica-curativa/ueber-die-clinica-curativa/', 1), ('https://cseb.ch/betriebe/chuerapflege/pflege-wohnen-im-alter/', 1)]
- Best contact page: https://cseb.ch/service/medienkontakt/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `andrea.matossi@cseb.ch`
      - `mailto_link`: `info@cseb.ch`
      - `plain_email`: `andrea.matossi@cseb.ch`
      - `plain_email`: `info@cseb.ch`
      - `base64_email_candidate`: `data/41042a57ce53cfa12fe37f2e/script`
      - `base64_email_candidate`: `ch/service/medienkontakt/`
      - `contact_form`: `<form`
      - `wordpress`: `wp-includes`
      - `wordpress`: `wp-content`

### https://www.chuv.ch/fr/disa/disa-home/
- Section: hospitals · Title: DISA Div. int. santé des adolesc - Ambulatoire
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'typo3']
    - `base64_email_candidate`: `package/Resources/Public/Icons/Favicons/favicon`
    - `base64_email_candidate`: `/typo3temp/assets/compressed/merged`
    - `contact_form`: `<form`
    - `typo3`: `typo3conf`
    - `typo3`: `typo3temp`
- Contact links: [('https://www.chuv.ch/fr/disa/disa-home/en-bref/notre-equipe', 5), ('https://www.chuv.ch/fr/disa/disa-home/formulaire-de-contact?tx_chuvforms%5Bcontact%5D=177279&cHash=24612b30306968bccd7266d6de99a27c', 3), ('https://www.chuv.ch/fr/disa/disa-home/en-bref/impressum', 3), ('https://www.chuv.ch/fr/disa/disa-home/formulaire-de-contact', 3)]
- Best contact page: https://www.chuv.ch/fr/disa/disa-home/en-bref/notre-equipe (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'typo3']
      - `base64_email_candidate`: `package/Resources/Public/Icons/Favicons/favicon`
      - `base64_email_candidate`: `/typo3temp/assets/compressed/merged`
      - `contact_form`: `<form`
      - `typo3`: `typo3conf`
      - `typo3`: `typo3temp`

### https://orlzentrum-saratz.ch/
- Section: medClinics · Title: ORL Zentrum – Dr. Med. A. Saratz
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'html_entity_at_dec', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `&#115;ara&#116;&#122;&#064;h&#105;&#110;.c&#104;`
    - `mailto_link`: `isl&#101;&#114;&#064;&#104;in.&#099;&#104;`
    - `html_entity_at_dec`: `&#064;`
    - `plain_email`: `saratz@hin.ch`
    - `plain_email`: `isler@hin.ch`
    - `base64_email_candidate`: `com/wordpress/plugins/seo/`
    - `base64_email_candidate`: `PropertyValueSpecification`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-json`
- Contact links: [('https://orlzentrum-saratz.ch/impressum-datenschutz/', 6), ('https://orlzentrum-saratz.ch/team/', 3), ('https://orlzentrum-saratz.ch/kontakt/', 3)]
- Best contact page: https://orlzentrum-saratz.ch/impressum-datenschutz/ (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `saratz@hin.ch`
      - `mailto_link`: `isler@hin.ch`
      - `plain_email`: `saratz@hin.ch`
      - `plain_email`: `isler@hin.ch`
      - `base64_email_candidate`: `com/wordpress/plugins/seo/`
      - `base64_email_candidate`: `PropertyValueSpecification`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-json`

### https://www.chuv.ch/fr/chirurgie-cardiaque/ccv-home/
- Section: hospitals · Title: CHUV - Chirurgie cardiaque
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'typo3']
    - `base64_email_candidate`: `package/Resources/Public/Icons/Favicons/favicon`
    - `base64_email_candidate`: `/typo3temp/assets/compressed/merged`
    - `contact_form`: `<form`
    - `typo3`: `typo3conf`
    - `typo3`: `typo3temp`
- Contact links: [('https://www.chuv.ch/fr/chirurgie-cardiaque/ccv-home/patients-et-familles/notre-equipe', 5), ('https://www.chuv.ch/fr/chirurgie-cardiaque/ccv-home/patients-et-familles/notre-equipe/pr-matthias-kirsch-chef-de-service', 4), ('https://www.chuv.ch/fr/chirurgie-cardiaque/ccv-home/le-service-en-bref/contacts', 3), ('https://www.chuv.ch/fr/chirurgie-cardiaque/ccv-home/formulaire-de-contact', 3)]
- Best contact page: https://www.chuv.ch/fr/chirurgie-cardiaque/ccv-home/patients-et-familles/notre-equipe (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'typo3']
      - `base64_email_candidate`: `package/Resources/Public/Icons/Favicons/favicon`
      - `base64_email_candidate`: `/typo3temp/assets/compressed/merged`
      - `contact_form`: `<form`
      - `typo3`: `typo3conf`
      - `typo3`: `typo3temp`

### http://hausarztpraxis-duennere.ch/
- Section: groupPractices · Title: Hausarztpraxis Dünnere
- Homepage status: 200 · server: ``
- Homepage patterns: ['base64_email_candidate', 'joomla']
    - `base64_email_candidate`: `/media/system/js/mootools`
    - `base64_email_candidate`: `/templates/system/css/system`
    - `joomla`: `Joomla`
- Contact links: [('http://hausarztpraxis-duennere.ch/index.php/praxis-team', 5), ('http://hausarztpraxis-duennere.ch/index.php/anfahrtswege', 3), ('http://hausarztpraxis-duennere.ch/index.php/impressum', 3), ('http://hausarztpraxis-duennere.ch/index.php/kontakte', 2), ('http://hausarztpraxis-duennere.ch/index.php/dienstleistungen-uebersicht', 1)]
- Best contact page: http://hausarztpraxis-duennere.ch/index.php/praxis-team (status 200)
  - patterns: ['base64_email_candidate', 'joomla']
      - `base64_email_candidate`: `/media/system/js/mootools`
      - `base64_email_candidate`: `/templates/system/css/system`
      - `joomla`: `Joomla`

### https://ova-ivf.ch/
- Section: hospitals · Title: Ova IVF Clinic Zürich
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'plain_email']
    - `plain_email`: `960db234-eb69e160@581w.webp`
    - `plain_email`: `960db234-eb69e160@1162w2x.webp`
    - `base64_email_candidate`: `/wGlobal/wGlobal/layout/images/site`
    - `base64_email_candidate`: `/wGlobal/wGlobal/layout/styles/optimized/design`
    - `contact_form`: `<form`
- Contact links: [('https://ova-ivf.ch/de/ueber-uns/das-team/', 5), ('https://ova-ivf.ch/de/kontakt/', 3), ('https://ova-ivf.ch/de/impressum/', 3), ('https://ova-ivf.ch/de/datenschutz/', 3), ('https://ova-ivf.ch/de/ueber-uns/qualitaetssicherung-quarts/', 2)]
- Best contact page: https://ova-ivf.ch/de/ueber-uns/das-team/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'plain_email']
      - `plain_email`: `ova-ivf-kinderwunsch-klinik-zuerich-0-525fb8c4-eb69e160@1920w.webp`
      - `plain_email`: `ova-ivf-kinderwunsch-klinik-zuerich-0-525fb8c4-eb69e160@1920w.jpg`
      - `base64_email_candidate`: `/wGlobal/wGlobal/layout/images/site`
      - `base64_email_candidate`: `/wGlobal/wGlobal/layout/styles/optimized/design`
      - `contact_form`: `<form`

### https://kinderarztpraxis-roemerhof.ch/Startseite/
- Section: groupPractices · Title: Kinderarztpraxis Römerhof
- Homepage status: 200 · server: `CM4all Webserver`
- Homepage patterns: ['base64_email_candidate', 'wordpress']
    - `base64_email_candidate`: `com/beng/designs/data/sys/cm`
    - `base64_email_candidate`: `cm4all/e/static/3rdparty/font`
    - `wordpress`: `wp-content`
- Contact links: [('https://kinderarztpraxis-roemerhof.ch/Team/', 3), ('https://kinderarztpraxis-roemerhof.ch/Kontakt/', 3), ('https://kinderarztpraxis-roemerhof.ch/impressum/', 3), ('https://kinderarztpraxis-roemerhof.ch/Datenschutzerklaerung/', 3), ('https://kinderarztpraxis-roemerhof.ch/Datenschutzerklaerung/index.php/', 2)]
- Best contact page: https://kinderarztpraxis-roemerhof.ch/Team/ (status 200)
  - patterns: ['base64_email_candidate', 'wordpress']
      - `base64_email_candidate`: `com/beng/designs/data/sys/cm`
      - `base64_email_candidate`: `cm4all/e/static/3rdparty/font`
      - `wordpress`: `wp-content`

### https://www.angela-rotthoff-nolte.com/
- Section: medClinics · Title: Praxis Dr. med. Rotthoff-Nolte Angela
- Homepage status: 200 · server: `Pepyaka`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wix']
    - `mailto_link`: `dr.rotthoff@gmx.net`
    - `mailto_link`: `dr.rotthoff@gmx.ch`
    - `plain_email`: `dr.rotthoff@gmx.net`
    - `plain_email`: `dr.rotthoff@gmx.ch`
    - `base64_email_candidate`: `componentsLibrariesTopology`
    - `base64_email_candidate`: `isRunningInDifferentSiteContext`
    - `wix`: `static.wixstatic`
- Contact links: [('https://www.angela-rotthoff-nolte.com/datenschutz', 3), ('https://www.angela-rotthoff-nolte.com/impressum', 3), ('https://www.angela-rotthoff-nolte.com', 1)]
- Best contact page: https://www.angela-rotthoff-nolte.com/datenschutz (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wix']
      - `mailto_link`: `dr.rotthoff@gmx.ch`
      - `plain_email`: `dr.rotthoff@gmx.ch`
      - `plain_email`: `dr.rotthoff@gmx.net`
      - `base64_email_candidate`: `componentsLibrariesTopology`
      - `base64_email_candidate`: `isRunningInDifferentSiteContext`
      - `wix`: `static.wixstatic`

### https://www.augenarzt-cham.ch/
- Section: groupPractices · Title: Augenarztpraxis Cham
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate']
    - `base64_email_candidate`: `/view/plugins/flexnav/css/flexnav`
    - `base64_email_candidate`: `/view/plugins/bootstrap/v2/css/bootstrap`
- Contact links: [('https://www.augenarzt-cham.ch/UeBER-UNS.htm', 3), ('https://www.augenarzt-cham.ch/TEAM.htm', 3), ('https://www.augenarzt-cham.ch/KONTAKT-STANDORT.htm', 3), ('https://www.augenarzt-cham.ch/Impressum.htm', 3), ('https://www.augenarzt-cham.ch/Datenschutz.htm', 2)]
- Best contact page: https://www.augenarzt-cham.ch/UeBER-UNS.htm (status 200)
  - patterns: ['base64_email_candidate']
      - `base64_email_candidate`: `/view/plugins/flexnav/css/flexnav`
      - `base64_email_candidate`: `/view/plugins/bootstrap/v2/css/bootstrap`

### https://www.klinik-gut.ch/fachgebiete/allgemeine-chirurgie.html
- Section: clinics · Title: Klinik Gut St. Moritz - Chirurgie Allgemein
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
    - `mailto_link`: `flaesch@klinik-gut.ch`
    - `mailto_link`: `stmoritz@klinik-gut.ch`
    - `plain_email`: `flaesch@klinik-gut.ch`
    - `plain_email`: `stmoritz@klinik-gut.ch`
    - `base64_email_candidate`: `/sites/default/files/favicons/favicon`
    - `base64_email_candidate`: `//sites/default/files/faviconsapple`
- Contact links: [('https://www.klinik-gut.ch/de/ueber-uns', 3), ('https://www.klinik-gut.ch/de/kontakt-standorte', 3), ('https://www.klinik-gut.ch/de/datenschutz', 3), ('https://www.klinik-gut.ch/de/impressum', 3), ('https://www.klinik-gut.ch/de/aerzteteam', 2)]
- Best contact page: https://www.klinik-gut.ch/de/ueber-uns (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
      - `mailto_link`: `flaesch@klinik-gut.ch`
      - `mailto_link`: `stmoritz@klinik-gut.ch`
      - `plain_email`: `flaesch@klinik-gut.ch`
      - `plain_email`: `stmoritz@klinik-gut.ch`
      - `base64_email_candidate`: `/sites/default/files/favicons/favicon`
      - `base64_email_candidate`: `//sites/default/files/faviconsapple`

### https://www.medispine.ch/
- Section: medicalCenters · Title: MediSpine WirbelsäulenZentrum Biel-Seeland
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'wordpress']
    - `base64_email_candidate`: `content/uploads/2019/11/Spine`
    - `base64_email_candidate`: `PropertyValueSpecification`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-json`
- Contact links: [('https://www.medispine.ch/leistungen/sprechstunden/', 3), ('https://www.medispine.ch/praxis/ueber-uns/', 3), ('https://www.medispine.ch/praxis/team/', 3), ('https://www.medispine.ch/kontakt/', 3), ('https://www.medispine.ch/kontakt/kontaktieren-sie-uns/', 3)]
- Best contact page: https://www.medispine.ch/leistungen/sprechstunden/ (status 200)
  - patterns: ['base64_email_candidate', 'wordpress']
      - `base64_email_candidate`: `ch/leistungen/sprechstunden/`
      - `base64_email_candidate`: `ch/fr/prestations/consultations/`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-json`

### https://www.clienia.ch/de/standorte/clienia-maennedorf/
- Section: hospitals · Title: Psychiatriezentrum Männedorf - Psych. Ambulatorium
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'wordpress']
    - `base64_email_candidate`: `content/uploads/elementor/thumbs/clienia`
    - `base64_email_candidate`: `piuy8rooi3v5tuomrosozb3cz3bwn28pw4cxieey40`
    - `contact_form`: `<form`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-includes`
    - `cookiebot_etc`: `usercentrics`
    - `cookiebot_etc`: `Usercentrics`
- Contact links: [('https://www.clienia.ch/de/impressum/', 3), ('https://www.clienia.ch/de/datenschutz/', 3), ('https://www.clienia.ch/de/standorte/clienia-maennedorf-psychiatriezentrum-zuerichsee/kontakt/', 2)]
- Best contact page: https://www.clienia.ch/de/impressum/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'plain_email', 'wordpress']
      - `plain_email`: `info@clienia.ch`
      - `base64_email_candidate`: `com/avatar/0b61350bbf24f55c1f577726a2932fe7ed95043a2db19434a3109b424a5d9c5e`
      - `base64_email_candidate`: `content/cache/min/1/vho6lrl`
      - `contact_form`: `<form`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-includes`
      - `cookiebot_etc`: `usercentrics`
      - `cookiebot_etc`: `Usercentrics`

### https://www.praxis-zlonoga.ch/
- Section: medClinics · Title: Praxis Dr. med. Zlonoga Bogdan
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate']
    - `base64_email_candidate`: `files/js/vendor/bootstrap`

### https://www.augenchirurgie.ch/
- Section: groupPractices · Title: Augenchirurgie.ch Winterthur
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'js_email_charcode', 'mailto_link', 'plain_email']
    - `mailto_link`: `info@augenchirurgie.ch`
    - `mailto_link`: `ivoguber@hin.ch`
    - `plain_email`: `info@augenchirurgie.ch`
    - `plain_email`: `ivoguber@hin.ch`
    - `js_email_charcode`: `String.fromCharCode(n>>10|55296,1023&n|56320)`
    - `base64_email_candidate`: `/assets/favicon/browserconfig`
    - `base64_email_candidate`: `stopImmediatePropagation`
    - `contact_form`: `<form`
- Contact links: [('https://www.augenchirurgie.ch/ueber-uns', 3), ('https://www.augenchirurgie.ch/kontakt', 3), ('https://www.augenchirurgie.ch/impressum', 3), ('https://www.augenchirurgie.ch/datenschutz', 3), ('https://www.augenchirurgie.ch/alles-uebers-auge', 1)]
- Best contact page: https://www.augenchirurgie.ch/ueber-uns (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'js_email_charcode']
      - `js_email_charcode`: `String.fromCharCode(n>>10|55296,1023&n|56320)`
      - `base64_email_candidate`: `/assets/favicon/browserconfig`
      - `base64_email_candidate`: `stopImmediatePropagation`
      - `contact_form`: `<form`

### https://www.kinderarztpraxis-kuesnacht.ch/
- Section: groupPractices · Title: Kinderarztpraxis Küsnacht
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'plain_email', 'wordpress']
    - `plain_email`: `kinderarztpraxis-kuesnacht@hin.ch`
    - `base64_email_candidate`: `com/wordpress/plugins/seo/`
    - `base64_email_candidate`: `content/uploads/2018/12/18`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-includes`
- Contact links: [('https://www.kinderarztpraxis-kuesnacht.ch/kontakt', 3), ('https://www.kinderarztpraxis-kuesnacht.ch/team', 3), ('https://www.kinderarztpraxis-kuesnacht.ch/datenschutzerklaerung', 3)]
- Best contact page: https://www.kinderarztpraxis-kuesnacht.ch/kontakt (status 200)
  - patterns: ['base64_email_candidate', 'plain_email', 'wordpress']
      - `plain_email`: `kinderarztpraxis-kuesnacht@hin.ch`
      - `base64_email_candidate`: `com/wordpress/plugins/seo/`
      - `base64_email_candidate`: `content/uploads/2018/12/18`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-includes`

### https://www.ksa.ch/de/gruppe/team/philipp-metzler-3082
- Section: medClinics · Title: Praxis Dr. med. Metzler Philipp
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
    - `mailto_link`: `philipp.metzler@ksa.ch`
    - `plain_email`: `willkommen@2x.ebdcad54.avif`
    - `plain_email`: `willkommen@2x.0756a73e.webp`
    - `base64_email_candidate`: `/static/default/images/favicon/apple`
    - `base64_email_candidate`: `/static/default/images/favicon/favicon`
- Contact links: [('https://www.ksa.ch/de/kantonsspital-aarau/ueber-uns', 3), ('https://www.ksa.ch/de/allgemeine-seiten/kontakt', 3), ('https://www.ksa.ch/de/gruppe/medien/medienkontakt', 3), ('https://www.ksa.ch/de/allgemeine-seiten/impressum', 3), ('https://www.ksa.ch/de/allgemeine-seiten/datenschutz', 3)]
- Best contact page: https://www.ksa.ch/de/kantonsspital-aarau/ueber-uns (status 200)
  - patterns: ['base64_email_candidate', 'plain_email']
      - `plain_email`: `diagnostische_bilder_radiologie@2x.6bb759a2.avif`
      - `plain_email`: `diagnostische_bilder_radiologie@2x.e1ceb583.webp`
      - `base64_email_candidate`: `/static/default/images/favicon/apple`
      - `base64_email_candidate`: `/static/default/images/favicon/favicon`

### https://www.med-adressen.ch/arzt/psychiatrie-und-psychotherapie/djordje-petrovic-30248
- Section: medClinics · Title: Praxis Dr. med. Petrovic Djordje
- **Errors**: ['HTTP 404']
- Homepage status: 404 · server: `cloudflare`

### https://zweichirurgen.ch/
- Section: groupPractices · Title: ZweiChirurgen Zentrum Hernienchirurgie & Proktologie St. Johanns-Vorstadt 44 Bas
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `zweichirurgen@hin.ch`
    - `plain_email`: `zweichirurgen@hin.ch`
    - `base64_email_candidate`: `content/themes/zweichirurgen/img/apple`
    - `base64_email_candidate`: `content/themes/zweichirurgen/img/favicon`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-includes`
- Contact links: [('https://zweichirurgen.ch/impressum-datenschutzerklaerung/', 5), ('https://zweichirurgen.ch/', 1)]
- Best contact page: https://zweichirurgen.ch/impressum-datenschutzerklaerung/ (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'text_at_brackets', 'text_dot_brackets', 'wordpress']
      - `mailto_link`: `info@zweichirurgen.ch`
      - `mailto_link`: `zweichirurgen@hin.ch`
      - `text_at_brackets`: `info(at)zweichirurgen`
      - `text_dot_brackets`: `zweichirurgen(dot)ch`
      - `plain_email`: `info@zweichirurgen.ch`
      - `plain_email`: `zweichirurgen@hin.ch`
      - `base64_email_candidate`: `content/themes/zweichirurgen/img/apple`
      - `base64_email_candidate`: `content/themes/zweichirurgen/img/favicon`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-includes`

### https://www.buchmann-mueller.ch/
- Section: groupPractices · Title: Praxis Dr. Buchmann & Dr. Müller
- Homepage status: 200 · server: `Pepyaka`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wix']
    - `mailto_link`: `buchmann.mueller@hin.ch`
    - `plain_email`: `buchmann.mueller@hin.ch`
    - `plain_email`: `605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com`
    - `base64_email_candidate`: `componentsLibrariesTopology`
    - `base64_email_candidate`: `isRunningInDifferentSiteContext`
    - `wix`: `static.wixstatic`

### https://www.swissmedical.net/en/doctors-directory/bekou-vassiliki
- Section: medicalCenters · Title: Vassiliki Bekou - Praxis Kreuzlingen
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
    - `mailto_link`: `vbek777@gmail.com`
    - `plain_email`: `vbek777@gmail.com`
    - `base64_email_candidate`: `/site/templates/public/img/favicon/apple`
    - `base64_email_candidate`: `/site/templates/public/img/favicon/favicon`
    - `contact_form`: `<form`
- Contact links: [('https://www.swissmedical.net/en/about', 3), ('https://www.swissmedical.net/en/legal-notice', 3), ('https://www.swissmedical.net/en/contact', 2), ('https://www.swissmedical.net/fr/hopitaux/moutier/a-propos/philosophie', 2), ('https://www.swissmedical.net/en/about/bee-sustainable', 2)]
- Best contact page: https://www.swissmedical.net/en/about (status 200)
  - patterns: ['base64_email_candidate', 'contact_form']
      - `base64_email_candidate`: `/site/templates/public/img/favicon/apple`
      - `base64_email_candidate`: `/site/templates/public/img/favicon/favicon`
      - `contact_form`: `<form`

### https://www.swissmedical.net/de/spitaeler/obach
- Section: clinics · Title: Privatklinik Obach - Gynäkologische Klinik
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
    - `mailto_link`: `obach@obach.ch`
    - `mailto_link`: `physiotherapie@obach.ch`
    - `plain_email`: `obach@obach.ch`
    - `plain_email`: `physiotherapie@obach.ch`
    - `base64_email_candidate`: `/site/templates/public/img/favicon/apple`
    - `base64_email_candidate`: `/site/templates/public/img/favicon/favicon`
    - `contact_form`: `<form`
- Contact links: [('https://www.swissmedical.net/de/spitaeler/obach/ueber-uns', 3), ('https://www.swissmedical.net/de/spitaeler/obach/impressum', 3), ('https://www.swissmedical.net/de/impressum', 3), ('https://www.swissmedical.net/de/datenschutz', 3), ('https://www.swissmedical.net/de/spitaeler/obach/kontakt', 2)]
- Best contact page: https://www.swissmedical.net/de/spitaeler/obach/ueber-uns (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
      - `mailto_link`: `obach@obach.ch`
      - `plain_email`: `obach@obach.ch`
      - `base64_email_candidate`: `/site/templates/public/img/favicon/apple`
      - `base64_email_candidate`: `/site/templates/public/img/favicon/favicon`
      - `contact_form`: `<form`

### https://eulachklinik.ch/start/
- Section: clinics · Title: Eulach Klinik - Ophthalmologische Klinik
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `disposition@eulachklinik.ch`
    - `mailto_link`: `info@eulachklinik.ch`
    - `plain_email`: `disposition@eulachklinik.ch`
    - `plain_email`: `info@eulachklinik.ch`
    - `base64_email_candidate`: `com/wordpress/plugins/seo/`
    - `base64_email_candidate`: `PropertyValueSpecification`
    - `contact_form`: `Kontaktformular`
    - `contact_form`: `id='contact`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-json`
- Contact links: [('https://eulachklinik.ch/kontakt/', 3), ('https://eulachklinik.ch/ueber-uns/', 3), ('https://eulachklinik.ch/datenschutz/', 3), ('https://eulachklinik.ch/impressum/', 3), ('https://eulachklinik.ch/datenschutz', 3)]
- Best contact page: https://eulachklinik.ch/kontakt/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `info@eulachklinik.ch`
      - `mailto_link`: `disposition@eulachklinik.ch`
      - `plain_email`: `info@eulachklinik.ch`
      - `plain_email`: `disposition@eulachklinik.ch`
      - `base64_email_candidate`: `com/wordpress/plugins/seo/`
      - `base64_email_candidate`: `PropertyValueSpecification`
      - `contact_form`: `Kontaktformular`
      - `contact_form`: `id='contact`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-json`

