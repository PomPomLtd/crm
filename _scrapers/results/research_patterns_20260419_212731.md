# Email Pattern Reconnaissance — 20260419_212731

Sampled **40** clinic sites.

## Coverage

- Sites with any plaintext email (home or contact page): **27/40**  (67.5%)
- Plaintext email visible on homepage: **25/40**
- Plaintext email on contact page: **23/40**
- Contact link discoverable from homepage: **35/40**

## Patterns detected (sites where pattern appears on any page)

| Pattern | Count | Homepage | Contact page |
|---|---|---|---|
| `base64_email_candidate` | 68 | 34 | 34 |
| `plain_email` | 48 | 25 | 23 |
| `contact_form` | 41 | 21 | 20 |
| `mailto_link` | 36 | 21 | 15 |
| `wordpress` | 22 | 11 | 11 |
| `cookiebot_etc` | 14 | 7 | 7 |
| `typo3` | 10 | 5 | 5 |
| `wix` | 6 | 3 | 3 |
| `recaptcha` | 5 | 2 | 3 |
| `text_at_brackets` | 3 | 3 | 0 |
| `joomla` | 2 | 1 | 1 |
| `html_entity_at_dec` | 2 | 1 | 1 |
| `html_entity_dot_dec` | 1 | 1 | 0 |

## Status codes

- 200: 36
- 404: 3
- 403: 1

## Top servers

- Apache: 16
- nginx: 8
- cloudflare: 4
- Pepyaka: 3
- openresty: 1
- Netlify: 1

## Per-URL details

### https://www.chirurgiemaxillo-faciale.ch/
- Section: medClinics · Title: Cabinet Dr. Dojcinovic Ivan
- **Errors**: ['HTTP 403']
- Homepage status: 403 · server: `nginx`

### https://www.klinik-seeschau.ch/fachbereiche/plastische-aesthetische-und-rekonstruktive-chirurgie-handchirurgie-1/
- Section: clinics · Title: Klinik Seeschau Kreuzlingen - Chirurgie Plastische
- **Errors**: ['HTTP 404']
- Homepage status: 404 · server: ``

### https://www.hno-uster.ch/
- Section: medClinics · Title: Praxis Dr. med. Doebeli Peter
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'recaptcha']
    - `mailto_link`: `\`
    - `base64_email_candidate`: `AIzaSyCgKDdLe8v1Zww0FckSH0THf5zVmvCUnhA`
    - `recaptcha`: `g-recaptcha`
    - `recaptcha`: `grecaptcha`
- Contact links: [('https://www.hno-uster.ch/team', 3), ('https://www.hno-uster.ch/kontakt', 3), ('https://www.hno-uster.ch/impressum', 3)]
- Best contact page: https://www.hno-uster.ch/team (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'recaptcha']
      - `mailto_link`: `\`
      - `base64_email_candidate`: `E7YsDnOlmRotzUQ/0HvTiSa4g`
      - `base64_email_candidate`: `AIzaSyCgKDdLe8v1Zww0FckSH0THf5zVmvCUnhA`
      - `recaptcha`: `g-recaptcha`
      - `recaptcha`: `grecaptcha`

### https://www.sro.ch/patienten-und-angehoerige/psychiatrische-dienste/standorte/
- Section: hospitals · Title: Psychiatrische Dienste SRO - Psych. Ambulatorium
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'text_at_brackets', 'typo3']
    - `text_at_brackets`: `psychiatrie(at)sro.ch`
    - `base64_email_candidate`: `assets/6a90b896e8b394507bc352c9788034b1/Images/favicon`
    - `base64_email_candidate`: `ch/typo3temp/assets/compressed/08c57bae30430ca890a72bc7493bcb69`
    - `contact_form`: `<form`
    - `typo3`: `typo3temp`
    - `cookiebot_etc`: `Cookiebot`
    - `cookiebot_etc`: `cookiebot`
- Contact links: [('https://www.sro.ch/patienten-und-angehoerige/psychiatrische-dienste/ueber-uns/', 3), ('https://www.sro.ch/patienten-und-angehoerige/angehoerige-und-besucher/anfahrtsweg/', 3), ('https://www.sro.ch/fachbereiche/spezialsprechstunden-und-ambulatorien/', 3), ('https://www.sro.ch/impressum/', 3), ('https://www.sro.ch/datenschutz/', 3)]
- Best contact page: https://www.sro.ch/patienten-und-angehoerige/psychiatrische-dienste/ueber-uns/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'typo3']
      - `base64_email_candidate`: `assets/6a90b896e8b394507bc352c9788034b1/Images/favicon`
      - `base64_email_candidate`: `assets/6a90b896e8b394507bc352c9788034b1/Css/toggle`
      - `contact_form`: `<form`
      - `typo3`: `typo3temp`
      - `cookiebot_etc`: `Cookiebot`
      - `cookiebot_etc`: `cookiebot`

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

### https://www.hausaerzte-binningen.ch/
- Section: medClinics · Title: HZB – Hausärzte Zentrum Binningen
- Homepage status: 200 · server: ``
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `hausaerzte-binningen@hin.ch`
    - `plain_email`: `hausaerzte-binningen@hin.ch`
    - `base64_email_candidate`: `content/uploads/2024/12/IMG`
    - `base64_email_candidate`: `PropertyValueSpecification`
    - `contact_form`: `id="contact`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-json`
- Contact links: [('https://www.hausaerzte-binningen.ch/ueber-uns/', 3), ('https://www.hausaerzte-binningen.ch/impressum/', 3), ('https://www.hausaerzte-binningen.ch/datenschutz/', 3)]
- Best contact page: https://www.hausaerzte-binningen.ch/ueber-uns/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `hausaerzte-binningen@hin.ch`
      - `plain_email`: `hausaerzte-binningen@hin.ch`
      - `base64_email_candidate`: `content/uploads/2024/11/Thomas`
      - `base64_email_candidate`: `PropertyValueSpecification`
      - `contact_form`: `id="contact`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-json`

### https://arzt-winkeln.ch/
- Section: groupPractices · Title: Praxisgemeinschaft Mövenstrasse
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'wordpress']
    - `base64_email_candidate`: `content/themes/praxis/img/icons/favicon`
    - `base64_email_candidate`: `content/themes/praxis/img/icons/apple`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-includes`
- Contact links: [('https://arzt-winkeln.ch/team', 3), ('https://arzt-winkeln.ch/kontakt/', 3)]
- Best contact page: https://arzt-winkeln.ch/team/ (status 200)
  - patterns: ['base64_email_candidate', 'wordpress']
      - `base64_email_candidate`: `content/themes/praxis/img/icons/favicon`
      - `base64_email_candidate`: `content/themes/praxis/img/icons/apple`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-includes`

### https://kinderwunschbaden.ch/
- Section: clinics · Title: Kinderwunschzentrum AG - Gynäkologische Klinik
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'wordpress']
    - `base64_email_candidate`: `PropertyValueSpecification`
    - `base64_email_candidate`: `content/themes/kinderwunschbaden`
    - `contact_form`: `<form`
    - `contact_form`: `id="contact`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-includes`
- Contact links: [('https://kinderwunschbaden.ch/ueber-uns/', 3), ('https://kinderwunschbaden.ch/kontakt/', 3), ('https://kinderwunschbaden.ch/das-team/', 2), ('https://kinderwunschbaden.ch/privacy-policy/', 1)]
- Best contact page: https://kinderwunschbaden.ch/ueber-uns/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'wordpress']
      - `base64_email_candidate`: `PropertyValueSpecification`
      - `base64_email_candidate`: `content/themes/kinderwunschbaden`
      - `contact_form`: `<form`
      - `contact_form`: `id="contact`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-includes`

### https://www.linkedin.com/company/laser-beaute-med
- Section: groupPractices · Title: Laser Beauté Med
- Homepage status: 200 · server: `cloudflare`
- Homepage patterns: ['base64_email_candidate', 'contact_form']
    - `base64_email_candidate`: `v1/sc/h/80ndnja80f2uvg4l8sj2su82m`
    - `base64_email_candidate`: `v1/sc/h/al2o9zrvru7aqj8e1x2rzsrca`
    - `contact_form`: `<form`
- Contact links: [('https://www.linkedin.com/legal/privacy-policy?trk=d_org_guest_company_overview_footer-privacy-policy', 3), ('https://www.linkedin.com/legal/privacy-policy?trk=linkedin-tc_auth-button_privacy-policy', 3), ('https://www.linkedin.com/legal/cookie-policy', 2), ('https://www.linkedin.com/legal/user-agreement?trk=d_org_guest_company_overview_footer-user-agreement', 2), ('https://www.linkedin.com/legal/cookie-policy?trk=d_org_guest_company_overview_footer-cookie-policy', 2)]
- Best contact page: https://de.linkedin.com/legal/privacy-policy?trk=d_org_guest_company_overview_footer-privacy-policy (status 200)
  - patterns: ['base64_email_candidate']
      - `base64_email_candidate`: `v1/sc/h/al2o9zrvru7aqj8e1x2rzsrca`
      - `base64_email_candidate`: `com/dms/image/v2/C5608AQHtHOx13KD3DQ/croft`

### https://www.h-och.ch/gynaekologie-geburtshilfe/fachbereiche/gynaekologie/
- Section: hospitals · Title: Spital Grabs - Gynäkologische Klinik
- Homepage status: 200 · server: `cloudflare`
- Homepage patterns: ['base64_email_candidate', 'cookiebot_etc', 'mailto_link', 'plain_email']
    - `mailto_link`: `gyn-geb.kssg@h-och.ch`
    - `mailto_link`: `gyn-geb.grabs@h-och.ch`
    - `plain_email`: `gyn-geb.kssg@h-och.ch`
    - `plain_email`: `gyn-geb.grabs@h-och.ch`
    - `base64_email_candidate`: `org/scripttemplates/otSDKStub`
    - `base64_email_candidate`: `geburtshilfe/fachbereiche/gynaekologie/`
    - `cookiebot_etc`: `OneTrust`
- Contact links: [('https://www.h-och.ch/ueber-uns/team/rene-hornung/', 4), ('https://www.h-och.ch/ueber-uns/team/seraina-schmid/', 4), ('https://www.h-och.ch/ueber-uns/team/stefanie-huggle/', 4), ('https://www.h-och.ch/ueber-uns/team/henrik-lutz/', 4), ('https://www.h-och.ch/ueber-uns/', 3)]
- Best contact page: https://www.h-och.ch/ueber-uns/team/rene-hornung/ (status 200)
  - patterns: ['base64_email_candidate', 'cookiebot_etc', 'mailto_link', 'plain_email']
      - `mailto_link`: `gyn-geb.kssg@h-och.ch`
      - `mailto_link`: `kontakt@h-och.ch`
      - `plain_email`: `gyn-geb.kssg@h-och.ch`
      - `plain_email`: `kontakt@h-och.ch`
      - `base64_email_candidate`: `org/scripttemplates/otSDKStub`
      - `base64_email_candidate`: `2F93722f5bad7a66ecbff1521f14f7772b`
      - `cookiebot_etc`: `OneTrust`

### https://www.moncucco.ch/chirurgia_plastica_ricostruttiva_estetica.asp
- Section: clinics · Title: Clinica Luganese Moncucco - Chirurgia Plastica
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
    - `mailto_link`: `info@moncucco.ch`
    - `plain_email`: `info@moncucco.ch`
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

### https://www.solothurnerspitaeler.ch/unsere-spitaeler/buergerspital-solothurn/medizinisches-angebot/notfall/notfallzentrum
- Section: hospitals · Title: Notfallzentrum Bürgerspital - Telemedizin
- Homepage status: 200 · server: `cloudflare`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'typo3']
    - `base64_email_candidate`: `qwv6adkqi8qvbut2q4wkged777sacr`
    - `base64_email_candidate`: `/assets/images/accordion/arrow`
    - `contact_form`: `<form`
    - `contact_form`: `kontaktformular`
    - `typo3`: `typo3conf`
    - `cookiebot_etc`: `usercentrics`
- Contact links: [('https://www.solothurnerspitaeler.ch/system/e-mail-kontaktformular?addressType=department&addressUid=25&cHash=60f115c3177d9ad3ef3ff0da10c1209e', 3), ('https://www.solothurnerspitaeler.ch/system/e-mail-kontaktformular?addressType=manual&addressUid=8&cHash=4498b3d3f8ade59252b0033ab03ee669', 3), ('https://www.solothurnerspitaeler.ch/organisation/kontakt-fuer-lieferanten-versicherungen', 3), ('https://www.solothurnerspitaeler.ch/footer/impressum', 3), ('https://www.solothurnerspitaeler.ch/footer/disclaimerdatenschutz', 3)]
- Best contact page: https://www.solothurnerspitaeler.ch/system/e-mail-kontaktformular?addressType=department&addressUid=25&cHash=60f115c3177d9ad3ef3ff0da10c1209e (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'recaptcha', 'typo3']
      - `base64_email_candidate`: `qwv6adkqi8qvbut2q4wkged777sacr`
      - `base64_email_candidate`: `/assets/images/accordion/arrow`
      - `contact_form`: `Kontaktformular`
      - `contact_form`: `kontaktformular`
      - `recaptcha`: `g-recaptcha`
      - `typo3`: `typo3conf`
      - `typo3`: `typo3temp`
      - `cookiebot_etc`: `usercentrics`

### https://www.psychologie-laxdal.ch/
- Section: medClinics · Title: Praxis Dr. med. Laxdal Katerina
- Homepage status: 200 · server: `Pepyaka`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'text_at_brackets', 'wix']
    - `mailto_link`: `katerina.laxdal@psychologie.ch`
    - `text_at_brackets`: `katerina.laxdal(at)psychologie.ch`
    - `plain_email`: `katerina.laxdal@psychologie.ch`
    - `plain_email`: `605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com`
    - `base64_email_candidate`: `fe64e1838603460aa4342b5b64f5e82c`
    - `base64_email_candidate`: `componentsLibrariesTopology`
    - `wix`: `static.wixstatic`
- Contact links: [('https://www.psychologie-laxdal.ch/datenschutz', 3), ('https://www.psychologie-laxdal.ch/impressum', 3), ('https://www.psychologie-laxdal.ch', 1), ('https://www.psychologie-laxdal.ch/agb', 1)]
- Best contact page: https://www.psychologie-laxdal.ch/datenschutz (status 200)
  - patterns: ['base64_email_candidate', 'plain_email', 'wix']
      - `plain_email`: `605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com`
      - `plain_email`: `dd0a55ccb8124b9c9d938e3acf41f8aa@sentry.wixpress.com`
      - `base64_email_candidate`: `fe64e1838603460aa4342b5b64f5e82c`
      - `base64_email_candidate`: `componentsLibrariesTopology`
      - `wix`: `static.wixstatic`

### https://kinderarzt-arbon.ch/das-team
- Section: medClinics · Title: Praxis Dr. med. Boyacioglu Abdullah
- Homepage status: 200 · server: `openresty`
- Homepage patterns: ['base64_email_candidate', 'plain_email']
    - `plain_email`: `info@kinderarztpraxis-arbon.ch`
    - `base64_email_candidate`: `ch/7f506288bb/compiled/photo`
    - `base64_email_candidate`: `ch/7f506288bb/compiled/cookie`
- Contact links: [('https://kinderarzt-arbon.ch/impressum-datenschutz/index', 4), ('https://kinderarzt-arbon.ch/das-team', 3), ('https://kinderarzt-arbon.ch/kontakt', 3), ('https://kinderarzt-arbon.ch/privacy-policy', 1)]
- Best contact page: https://kinderarzt-arbon.ch/impressum-datenschutz/index (status 200)
  - patterns: ['base64_email_candidate', 'plain_email']
      - `plain_email`: `info@Kinderarztpraxis-Arbon.ch`
      - `base64_email_candidate`: `ch/7f506288bb/compiled/photo`
      - `base64_email_candidate`: `ch/7f506288bb/compiled/cookie`

### https://www.albisdocs.ch/lukas-nietlispach
- Section: medClinics · Title: Praxis Dr. med. Nietlispach Lukas
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'joomla', 'mailto_link', 'plain_email']
    - `mailto_link`: `sven.baeuerle@hin.ch`
    - `mailto_link`: `praxisln@hin.ch`
    - `plain_email`: `sven.baeuerle@hin.ch`
    - `plain_email`: `praxisln@hin.ch`
    - `base64_email_candidate`: `sppagebuilder/assets/css/animate`
    - `base64_email_candidate`: `0621ff1d1a7a69c31fa9c0bd192756a5`
    - `joomla`: `Joomla`
    - `joomla`: `joomla`
- Contact links: [('https://www.albisdocs.ch/index.php/component/sppagebuilder/page/55', 1)]
- Best contact page: https://www.albisdocs.ch/index.php/component/sppagebuilder/page/55 (status 200)
  - patterns: ['base64_email_candidate', 'joomla', 'plain_email']
      - `plain_email`: `holger.voigt@hin.ch`
      - `base64_email_candidate`: `php/component/sppagebuilder/page/55`
      - `base64_email_candidate`: `sppagebuilder/assets/css/animate`
      - `joomla`: `Joomla`
      - `joomla`: `joomla`

### https://plastischechirurgie-winterthur.ch/
- Section: medClinics · Title: Chirurgische Praxis, Dipl. Arzt Lars Kern
- Homepage status: 200 · server: ``
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `kern-chirurgie@hin.ch`
    - `plain_email`: `kern-chirurgie@hin.ch`
    - `base64_email_candidate`: `styles/c4706421f1ebb84e5b1f3a5c3f38bc86`
    - `base64_email_candidate`: `includes/js/jquery/jquery`
    - `wordpress`: `wp-json`
    - `wordpress`: `wp-includes`
- Contact links: [('https://plastischechirurgie-winterthur.ch/impressum/', 3), ('https://plastischechirurgie-winterthur.ch/datenschutz/', 3)]
- Best contact page: https://plastischechirurgie-winterthur.ch/impressum/ (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `kern-chirurgie@hin.ch`
      - `mailto_link`: `mail@medicus-solutions.ch`
      - `plain_email`: `kern-chirurgie@hin.ch`
      - `plain_email`: `mail@medicus-solutions.ch`
      - `base64_email_candidate`: `styles/eeff9d731bfe75ee880f3ea44c6c09eb`
      - `base64_email_candidate`: `includes/js/jquery/jquery`
      - `wordpress`: `wp-json`
      - `wordpress`: `wp-includes`

### https://www.valaishospital.ch/specialities-from-a-to-z/specialities-from-a-to-z/nephrology/visp
- Section: hospitals · Title: Spital Wallis - Dialysestation
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'plain_email', 'text_at_brackets', 'typo3']
    - `text_at_brackets`: `szo.dialyse(at)hopitalvs.ch`
    - `plain_email`: `szo.dialyse@hopitalvs.ch`
    - `base64_email_candidate`: `/typo3temp/assets/css/7015c8c4ac5ff815b57530b221005fc6`
    - `base64_email_candidate`: `assets/e799cca3073eabb617dfebf5f7cabc53/StyleSheets/Frontend/results`
    - `contact_form`: `<form`
    - `typo3`: `typo3temp`
    - `cookiebot_etc`: `onetrust`
    - `cookiebot_etc`: `OneTrust`
- Contact links: [('https://www.valaishospital.ch/valais-hospital/contact', 3), ('https://www.valaishospital.ch/valais-hospital/legal-information', 3)]
- Best contact page: https://www.valaishospital.ch/valais-hospital/contact (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'plain_email', 'typo3']
      - `plain_email`: `szo.telefonzentrale.brig@hopitalvs.ch`
      - `plain_email`: `st-ame.reception@hopitalvs.ch`
      - `base64_email_candidate`: `/typo3temp/assets/css/7015c8c4ac5ff815b57530b221005fc6`
      - `base64_email_candidate`: `assets/e799cca3073eabb617dfebf5f7cabc53/StyleSheets/Frontend/results`
      - `contact_form`: `<form`
      - `typo3`: `typo3temp`
      - `cookiebot_etc`: `onetrust`
      - `cookiebot_etc`: `OneTrust`

### https://praxis-bestetti.ch/
- Section: medClinics · Title: Praxis Dr. med. Bestetti Valentina
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `praxis.bestetti@hin.ch`
    - `mailto_link`: `valentina.bestetti@hin.ch`
    - `plain_email`: `praxis.bestetti@hin.ch`
    - `plain_email`: `valentina.bestetti@hin.ch`
    - `base64_email_candidate`: `com/wordpress/plugins/seo/`
    - `base64_email_candidate`: `PropertyValueSpecification`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-includes`
- Contact links: [('https://praxis-bestetti.ch/impressum/', 3), ('https://praxis-bestetti.ch/datenschutzerklaerung/', 3), ('https://praxis-bestetti.ch/', 1), ('https://praxis-bestetti.ch/angebot/ganglion-ueberbein-zyste/', 1)]
- Best contact page: https://praxis-bestetti.ch/impressum/ (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `praxis.bestetti@hin.ch`
      - `mailto_link`: `valentina.bestetti@hin.ch`
      - `plain_email`: `praxis.bestetti@hin.ch`
      - `plain_email`: `valentina.bestetti@hin.ch`
      - `base64_email_candidate`: `com/wordpress/plugins/seo/`
      - `base64_email_candidate`: `PropertyValueSpecification`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-includes`

### https://www.paraplegie.ch/spz/de/
- Section: hospitals · Title: Schweizer Paraplegiker-Zentrum - Rehabilitation
- Homepage status: 200 · server: `Netlify`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
    - `mailto_link`: `spz@paraplegie.ch`
    - `plain_email`: `sps@paraplegie.ch`
    - `plain_email`: `spz@paraplegie.ch`
    - `base64_email_candidate`: `/img/favicons/spz/android`
    - `base64_email_candidate`: `/img/favicons/spz/favicon`
    - `contact_form`: `<form`
- Contact links: [('https://www.paraplegie.ch/spz/de/kontakt-spz/', 3), ('https://www.paraplegie.ch/de/ueber-uns/organisation/organisationen-schweizer-paraplegiker-gruppe/', 2), ('https://www.paraplegie.ch/spz/de/ueber-uns/soziale-und-berufliche-integration/soziale-und-berufliche-integration/', 2), ('https://www.paraplegie.ch/spz/de/ueber-uns/forschung/angewandte-klinische-forschung/', 2), ('https://www.paraplegie.ch/spz/de/ueber-uns/qualitaet-und-sicherheit/', 2)]
- Best contact page: https://www.paraplegie.ch/spz/de/kontakt-spz/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
      - `mailto_link`: `spz@paraplegie.ch`
      - `plain_email`: `sps@paraplegie.ch`
      - `plain_email`: `spz@paraplegie.ch`
      - `base64_email_candidate`: `/img/favicons/spz/android`
      - `base64_email_candidate`: `/img/favicons/spz/favicon`
      - `contact_form`: `<form`

### https://enfants-ados.hug.ch/specialites-medicales-chirurgicales/sante-ados
- Section: hospitals · Title: Consultation santé jeunes - Ambulatoire psych.
- Homepage status: 200 · server: ``
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
    - `mailto_link`: `casaa.secretariat@hug.ch`
    - `plain_email`: `casaa.secretariat@hug.ch`
    - `base64_email_candidate`: `ados/files/HDE/Images/accueil`
    - `base64_email_candidate`: `/themes/custom/interhug/favicon`
    - `contact_form`: `<form`
    - `contact_form`: `id="contact`
- Contact links: [('https://enfants-ados.hug.ch/sante-ados/equipe-casaa', 3)]
- Best contact page: https://enfants-ados.hug.ch/sante-ados/equipe-casaa (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
      - `mailto_link`: `casaa.secretariat@hug.ch`
      - `plain_email`: `casaa.secretariat@hug.ch`
      - `base64_email_candidate`: `ados/files/HDE/Images/accueil`
      - `base64_email_candidate`: `/themes/custom/interhug/favicon`
      - `contact_form`: `<form`
      - `contact_form`: `id="contact`

### https://www.handchirurgie-seefeld.ch/
- Section: medClinics · Title: Handchirurgie Seefeld
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `handchirurgie-seefeld@hin.ch\`
    - `mailto_link`: `handchirurgie-seefeld@hin.ch`
    - `plain_email`: `handchirurgie-seefeld@hin.ch`
    - `plain_email`: `info@handchirurgie-seefeld.ch`
    - `base64_email_candidate`: `com/wordpress/plugins/seo/`
    - `base64_email_candidate`: `content/uploads/2020/06/handchirurgie`
    - `contact_form`: `Kontaktformular`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-includes`
- Contact links: [('https://www.handchirurgie-seefeld.ch/kontakt/', 3), ('https://www.handchirurgie-seefeld.ch/impressum/', 3), ('https://www.handchirurgie-seefeld.ch/datenschutzbestimmungen/', 3), ('https://www.handchirurgie-seefeld.ch/kontakt', 2)]
- Best contact page: https://www.handchirurgie-seefeld.ch/kontakt/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `handchirurgie-seefeld@hin.ch\`
      - `mailto_link`: `handchirurgie-seefeld@hin.ch`
      - `plain_email`: `handchirurgie-seefeld@hin.ch`
      - `plain_email`: `info@handchirurgie-seefeld.ch`
      - `base64_email_candidate`: `com/wordpress/plugins/seo/`
      - `base64_email_candidate`: `content/uploads/2020/06/handchirurgie`
      - `contact_form`: `id='contact`
      - `contact_form`: `kontaktformular`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-includes`

### https://www.praxisschwegler.ch/team.html
- Section: medClinics · Title: Praxis Dr. med. Schwegler Christian
- **Errors**: ['HTTP 404']
- Homepage status: 404 · server: `Apache`

### https://www.hirslanden.ch/en/klinik-birshof/home.html
- Section: clinics · Title: Hirslanden Klinik Birshof
- Homepage status: 200 · server: ``
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'mailto_link', 'plain_email']
    - `mailto_link`: `%20klinik-birshof@hirslanden.ch`
    - `plain_email`: `20klinik-birshof@hirslanden.ch`
    - `base64_email_candidate`: `pZf8AJotu170CGkRficPEOidJhcZ6k6qj5qNg9hEb45oKkrPeRoKUlzfSoB6ULW8vLGLdSDqmQgYd9vc3vxTRA`
    - `base64_email_candidate`: `clientlibs/hirslanden/clientlibs/frontend`
    - `contact_form`: `<form`
    - `cookiebot_etc`: `OneTrust`
- Contact links: [('https://www.hirslanden.ch/en/klinik-birshof/contact.html', 3), ('https://www.hirslanden.ch/en/corporate/impressum.html', 3), ('https://www.hirslanden.ch/en/corporate/the-hirslanden-group/contact/healthline.html', 2), ('https://www.hirslanden.ch/en/corporate/assurance/invoice-copy.html', 1)]
- Best contact page: https://www.hirslanden.ch/en/klinik-birshof/contact.html (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'mailto_link', 'plain_email']
      - `mailto_link`: `%20klinik-birshof@hirslanden.ch`
      - `plain_email`: `20klinik-birshof@hirslanden.ch`
      - `base64_email_candidate`: `pZf8AJotu170CGkRficPEEobvnqibX9bkWWq63Jdarz8HozMWWfUe6`
      - `base64_email_candidate`: `clientlibs/hirslanden/clientlibs/frontend`
      - `contact_form`: `<form`
      - `cookiebot_etc`: `OneTrust`

### https://www.lindenhofgruppe.ch/de/unsere-aerzte/aerzte/mark-kleinschmidt.php
- Section: medClinics · Title: Praxis Dr. med. Kleinschmidt Mark
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'plain_email']
    - `plain_email`: `db0779e1-3e16c5a5@560w.jpg`
    - `plain_email`: `db0779e1-3e16c5a5@1120w2x.jpg`
    - `base64_email_candidate`: `ch/wAssets/img/aerzte/weblication/wThumbnails/0d4e9b45fe3c620gc4c143ad7b96dbcc`
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

### https://www.medecinsduchablais.ch/dr-nicolas-connebert/
- Section: medClinics · Title: Cabinet Dr. Connebert Nicolas
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'wordpress']
    - `base64_email_candidate`: `com/s/opensans/v44/memQYaGs126MiZpBA`
    - `base64_email_candidate`: `UFUIcVXSCEkx2cmqvXlWq8tWZ0Pw86hd0Rk5hkWV4exQ`
    - `contact_form`: `id='contact`
    - `contact_form`: `id="contact`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-json`
- Contact links: [('https://www.medecinsduchablais.ch/contact/', 3)]
- Best contact page: https://www.medecinsduchablais.ch/contact/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'plain_email', 'wordpress']
      - `plain_email`: `cabinet.mdc@hin.ch`
      - `base64_email_candidate`: `com/s/opensans/v44/memQYaGs126MiZpBA`
      - `base64_email_candidate`: `UFUIcVXSCEkx2cmqvXlWq8tWZ0Pw86hd0Rk5hkWV4exQ`
      - `contact_form`: `id='contact`
      - `contact_form`: `<form`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-json`

### https://www.praxismuehleberg.ch/
- Section: groupPractices · Title: Gemeinschaftspraxis PuB Mühleberg
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'html_entity_at_dec', 'html_entity_dot_dec', 'mailto_link', 'wordpress']
    - `mailto_link`: `&#112;r&#97;xis&#109;&#117;ehl&#101;&#98;erg&#64;h&#105;&#110;&#46;&#99;h`
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
  - patterns: ['base64_email_candidate', 'contact_form', 'html_entity_at_dec', 'mailto_link', 'plain_email', 'wordpress']
      - `mailto_link`: `p&#114;&#97;&#120;ismu&#101;hl&#101;b&#101;&#114;g&#64;&#104;i&#110;.ch`
      - `html_entity_at_dec`: `&#64;`
      - `plain_email`: `praxismuehleberg@hin.ch`
      - `base64_email_candidate`: `content/uploads/2018/09/favicon`
      - `base64_email_candidate`: `PropertyValueSpecification`
      - `contact_form`: `id='contact`
      - `contact_form`: `id="contact`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-json`

### https://www.kinderkardiologie-burkamp.ch/
- Section: medClinics · Title: Praxis Dr. med. Burkamp Antje
- Homepage status: 200 · server: `Apache`

### https://www.upk.ch/
- Section: clinics · Title: Basel, Univ. Psych. Kliniken Basel (UPK) - Psychiatrie - Stationär
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'typo3']
    - `base64_email_candidate`: `/typo3temp/assets/compressed/merged`
    - `base64_email_candidate`: `5e14b4f08fde6be4d2cf7f6bb154ef51`
    - `contact_form`: `<form`
    - `typo3`: `typo3temp`
    - `typo3`: `typo3conf`
    - `cookiebot_etc`: `usercentrics`
- Contact links: [('https://www.upk.ch/ueber-uns/datenschutz', 5), ('https://www.upk.ch/ueber-uns/standorte-und-lageplan/anfahrt', 5), ('https://www.upk.ch/ueber-uns/kontakt-und-feedback', 5), ('https://www.upk.ch/ueber-uns/kliniken-zentren-und-abteilungen/klinik-fuer-erwachsene/zentrum-fuer-diagnostik-und-krisenintervention/adhs-asperger-sprechstunde', 5), ('https://www.upk.ch/header/angehoerige/telefonsprechstunde-und-e-mail-beratung', 3)]
- Best contact page: https://www.upk.ch/ueber-uns/datenschutz (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'typo3']
      - `base64_email_candidate`: `/typo3temp/assets/compressed/merged`
      - `base64_email_candidate`: `6ac4e39f44411d20e007cfb9113bc84d`
      - `contact_form`: `<form`
      - `typo3`: `typo3temp`
      - `typo3`: `typo3conf`
      - `cookiebot_etc`: `usercentrics`

### https://www.lups.ch/erwachsene/ambulatorien/ambulatorium-sursee-erwachsenenpsychiatrie/
- Section: hospitals · Title: Gemeindeintegr. Akutbehandlung - Psych. Ambulatorium
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'plain_email', 'wordpress']
    - `plain_email`: `ambulatorium.sursee@lups.ch`
    - `base64_email_candidate`: `ch/app/cache/autoptimize/css/autoptimize`
    - `base64_email_candidate`: `d06656f8ec4a21ecc941a16275dedf90`
    - `contact_form`: `<form`
    - `contact_form`: `id="contact`
    - `wordpress`: `wp-json`
    - `wordpress`: `wp-includes`
- Contact links: [('https://www.lups.ch/portrait/kontakt/', 3), ('https://www.lups.ch/kinder-jugendliche/fachsprechstunden-kinder-jugendliche/', 3), ('https://www.lups.ch/erwachsene/fachsprechstunden-erwachsene/', 3), ('https://www.lups.ch/erwachsene/fachsprechstunden-erwachsene/psychiatrische-sprechstunde-fuer-schwangere-und-muetter/', 3), ('https://www.lups.ch/kontakt/', 3)]
- Best contact page: https://www.lups.ch/portrait/kontakt/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'wordpress']
      - `base64_email_candidate`: `ch/app/cache/autoptimize/css/autoptimize`
      - `base64_email_candidate`: `f79869c9898e96e07e6bc2c0e09a7238`
      - `contact_form`: `<form`
      - `contact_form`: `Kontaktformular`
      - `wordpress`: `wp-json`
      - `wordpress`: `wp-includes`

### https://www.consiliaris.ch/
- Section: medClinics · Title: Praxis Dr. med. Zellweger Claudine
- Homepage status: 200 · server: ``
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
    - `mailto_link`: `consiliaris@hin.ch`
    - `plain_email`: `consiliaris@hin.ch`
    - `base64_email_candidate`: `17mGh5NztWzQXCxGnTjBvd9jOvomLwt3UKa9G7omRwM`
    - `base64_email_candidate`: `/assets/images/favicon/apple`
- Contact links: [('https://consiliaris.ch/impressum', 3), ('https://consiliaris.ch/datenschutz', 3), ('https://www.consiliaris.ch/', 1)]
- Best contact page: https://www.consiliaris.ch/impressum (status 200)
  - patterns: ['base64_email_candidate', 'mailto_link', 'plain_email']
      - `mailto_link`: `consiliaris@hin.ch`
      - `plain_email`: `consiliaris@hin.ch`
      - `base64_email_candidate`: `17mGh5NztWzQXCxGnTjBvd9jOvomLwt3UKa9G7omRwM`
      - `base64_email_candidate`: `/assets/images/favicon/apple`

### https://www.cliniqueoeil-ono.ch/centre/servette/
- Section: medClinics · Title: Centre de L'Oeil Servette
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wordpress']
    - `mailto_link`: `servette@cliniqueoeilgeneve.ch`
    - `plain_email`: `servette@cliniqueoeilgeneve.ch`
    - `base64_email_candidate`: `content/uploads/2024/03/Hero`
    - `base64_email_candidate`: `content/uploads/2024/03/servette`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-includes`
- Contact links: [('https://www.cliniqueoeil-ono.ch/mentions-legales/', 4), ('https://www.cliniqueoeil-ono.ch/contact/', 3), ('https://www.cliniqueoeil-ono.ch/equipe/', 3), ('https://www.cliniqueoeil-ono.ch/prestations/bilans-visuels/adaptation-lentille-de-contact/', 3), ('https://www.cliniqueoeil-ono.ch/a-propos/carriere/', 2)]
- Best contact page: https://www.cliniqueoeil-ono.ch/mentions-legales/ (status 200)
  - patterns: ['base64_email_candidate', 'wordpress']
      - `base64_email_candidate`: `content/uploads/2023/10/hero`
      - `base64_email_candidate`: `PropertyValueSpecification`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-includes`

### https://www.med-adressen.ch/arzt/psychiatrie-und-psychotherapie/mathias-berger-21161
- Section: medClinics · Title: Praxis Dr. med. Berger Mathias
- **Errors**: ['HTTP 404']
- Homepage status: 404 · server: `cloudflare`

### https://www.praxis-roemer.ch/kontakt.html
- Section: medClinics · Title: Praxis Dr. med. Römer-Henke Constanze
- Homepage status: 200 · server: ``
- Homepage patterns: ['contact_form', 'plain_email']
    - `plain_email`: `info@praxis-roemer.ch`
    - `plain_email`: `constanze.roemer@hin.ch`
    - `contact_form`: `<form`
- Contact links: [('https://www.praxis-roemer.ch/kontakt.html', 3)]
- Best contact page: https://www.praxis-roemer.ch/kontakt.html (status 200)
  - patterns: ['contact_form', 'plain_email']
      - `plain_email`: `info@praxis-roemer.ch`
      - `plain_email`: `constanze.roemer@hin.ch`
      - `contact_form`: `<form`

### https://www.swissmedical.net/en/hospitals/generale-ste-anne
- Section: clinics · Title: Clinique Générale Ste-Anne - Médecine du sport
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
    - `mailto_link`: `info@cliniquegenerale.ch`
    - `mailto_link`: `Info@cliniquegenerale.ch`
    - `plain_email`: `info@cliniquegenerale.ch`
    - `plain_email`: `Info@cliniquegenerale.ch`
    - `base64_email_candidate`: `/site/templates/public/img/favicon/apple`
    - `base64_email_candidate`: `/site/templates/public/img/favicon/favicon`
    - `contact_form`: `<form`
- Contact links: [('https://www.swissmedical.net/en/hospitals/generale-ste-anne/about', 3), ('https://www.swissmedical.net/en/legal-notice', 3), ('https://www.swissmedical.net/en/hospitals/generale-ste-anne/contact', 2), ('https://www.swissmedical.net/en/hospitals/generale-ste-anne/about/medical-infrastructure', 2), ('https://www.swissmedical.net/en/hospitals/generale-ste-anne/about/organization', 2)]
- Best contact page: https://www.swissmedical.net/en/hospitals/generale-ste-anne/about (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
      - `mailto_link`: `info@cliniquegenerale.ch`
      - `plain_email`: `info@cliniquegenerale.ch`
      - `base64_email_candidate`: `/site/templates/public/img/favicon/apple`
      - `base64_email_candidate`: `/site/templates/public/img/favicon/favicon`
      - `contact_form`: `<form`

### https://www.praxisgemeinschaft-franklinstrasse.ch/christoph-walder
- Section: medClinics · Title: Praxis Dr. med. Walder Christoph
- Homepage status: 200 · server: `Pepyaka`
- Homepage patterns: ['base64_email_candidate', 'mailto_link', 'plain_email', 'wix']
    - `mailto_link`: `christoph.walder@hin.ch`
    - `plain_email`: `christoph.walder@hin.ch`
    - `plain_email`: `605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com`
    - `base64_email_candidate`: `componentsLibrariesTopology`
    - `base64_email_candidate`: `isRunningInDifferentSiteContext`
    - `wix`: `static.wixstatic`
- Contact links: [('https://www.praxisgemeinschaft-franklinstrasse.ch/team', 3), ('https://www.praxisgemeinschaft-franklinstrasse.ch/kontakt-und-lage', 3), ('https://www.praxisgemeinschaft-franklinstrasse.ch/impressum', 3)]
- Best contact page: https://www.praxisgemeinschaft-franklinstrasse.ch/team (status 200)
  - patterns: ['base64_email_candidate', 'plain_email', 'wix']
      - `plain_email`: `605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com`
      - `plain_email`: `dd0a55ccb8124b9c9d938e3acf41f8aa@sentry.wixpress.com`
      - `base64_email_candidate`: `componentsLibrariesTopology`
      - `base64_email_candidate`: `isRunningInDifferentSiteContext`
      - `wix`: `static.wixstatic`

### https://www.urologie-wipkingen.ch/
- Section: medClinics · Title: Praxis Dr. med. Schulz Christian
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'cookiebot_etc', 'mailto_link', 'plain_email']
    - `mailto_link`: `wipkingen@uroversum.ch`
    - `plain_email`: `wipkingen@uroversum.ch`
    - `base64_email_candidate`: `rDy1suor7L2konGPfJwXD9yMRLGjYTSkO4oAL2pDgiU`
    - `base64_email_candidate`: `schwerpunkte/harnsystem/`
    - `cookiebot_etc`: `Cookiebot`
    - `cookiebot_etc`: `cookiebot`
- Contact links: [('https://www.urologie-wipkingen.ch/praxis/kontakt-and-anfahrt/', 6), ('https://www.urologie-wipkingen.ch/praxis/kontakt-and-anfahrt', 5), ('https://www.urologie-wipkingen.ch/impressum', 3), ('https://www.urologie-wipkingen.ch/datenschutz', 3)]
- Best contact page: https://www.urologie-wipkingen.ch/praxis/kontakt-and-anfahrt/ (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'cookiebot_etc', 'mailto_link', 'plain_email']
      - `mailto_link`: `wipkingen@uroversum.ch`
      - `plain_email`: `wipkingen@uroversum.ch`
      - `base64_email_candidate`: `rDy1suor7L2konGPfJwXD9yMRLGjYTSkO4oAL2pDgiU`
      - `base64_email_candidate`: `/resources/vendor/silverstripe/userforms/client/dist/styles/userforms`
      - `contact_form`: `Kontaktformular`
      - `contact_form`: `<form`
      - `cookiebot_etc`: `Cookiebot`
      - `cookiebot_etc`: `cookiebot`

### https://www.medcentervolta.ch/
- Section: groupPractices · Title: MedCenter Volta
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email', 'recaptcha', 'wordpress']
    - `mailto_link`: `medcentervolta@hin.ch`
    - `plain_email`: `medcentervolta@hin.ch`
    - `base64_email_candidate`: `content/uploads/2025/11/64DE3E62`
    - `base64_email_candidate`: `PropertyValueSpecification`
    - `contact_form`: `<form`
    - `recaptcha`: `g-recaptcha`
    - `wordpress`: `wp-content`
    - `wordpress`: `wp-json`
- Contact links: [('https://medcentervolta.ch/ueber-uns/', 3), ('https://medcentervolta.ch/kontakt-und-anreise/', 3), ('https://medcentervolta.ch/datenschutzerklarung/', 3), ('https://medcentervolta.ch/impressum/', 3)]
- Best contact page: https://medcentervolta.ch/ueber-uns/ (status 200)
  - patterns: ['base64_email_candidate', 'wordpress']
      - `base64_email_candidate`: `Endokrinologie/Diabetologie`
      - `base64_email_candidate`: `PropertyValueSpecification`
      - `wordpress`: `wp-content`
      - `wordpress`: `wp-json`

### https://www.swissmedical.net/de/aerztezentren/valere/zentren/policlinique
- Section: clinics · Title: Policlinique de Valère
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'mailto_link', 'plain_email']
    - `mailto_link`: `reception@cliniquevalere.ch`
    - `plain_email`: `reception@cliniquevalere.ch`
    - `base64_email_candidate`: `/site/templates/public/img/favicon/apple`
    - `base64_email_candidate`: `/site/templates/public/img/favicon/favicon`
    - `contact_form`: `<form`
- Contact links: [('https://www.swissmedical.net/de/impressum', 3), ('https://www.swissmedical.net/de/datenschutz', 3), ('https://www.swissmedical.net/de/aerztezentren/valere/kontakt', 2), ('https://www.swissmedical.net/de/aerztezentren/valere/ueber-uns', 2)]
- Best contact page: https://www.swissmedical.net/de/impressum (status 200)
  - patterns: ['base64_email_candidate', 'contact_form']
      - `base64_email_candidate`: `/site/templates/public/img/favicon/apple`
      - `base64_email_candidate`: `/site/templates/public/img/favicon/favicon`
      - `contact_form`: `<form`

### http://www.augendoktor.ch/
- Section: medClinics · Title: Augenpraxis Spanweid Bülach
- Homepage status: 200 · server: `nginx`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'plain_email']
    - `plain_email`: `support@webador.de`
    - `plain_email`: `augendoktor@hin.ch`
    - `base64_email_candidate`: `cb8bbfe0508eeb6a938f4ccf69073ae8`
    - `base64_email_candidate`: `shippingDisclaimerVisible`
    - `contact_form`: `<form`
- Contact links: [('https://www.augenzentrum.ch/team', 3), ('https://www.augenzentrum.ch/impressum', 3), ('https://www.augenzentrum.ch/_downloads/cdc84050b6d6488e3a6411068b7faffb', 1)]
- Best contact page: https://www.augenzentrum.ch/team (status 200)
  - patterns: ['base64_email_candidate', 'plain_email']
      - `plain_email`: `support@webador.de`
      - `plain_email`: `augendoktor@hin.ch`
      - `base64_email_candidate`: `e67ffc75c82c99f787682c8b897a76d7`
      - `base64_email_candidate`: `shippingDisclaimerVisible`

### https://www.chuv.ch/fr/otr/otr-home/
- Section: hospitals · Title: CHUV - Chirurgie Orthopédique
- Homepage status: 200 · server: `Apache`
- Homepage patterns: ['base64_email_candidate', 'contact_form', 'typo3']
    - `base64_email_candidate`: `package/Resources/Public/Icons/Favicons/favicon`
    - `base64_email_candidate`: `/typo3temp/assets/compressed/merged`
    - `contact_form`: `<form`
    - `typo3`: `typo3conf`
    - `typo3`: `typo3temp`
- Contact links: [('https://www.chuv.ch/fr/otr/otr-home/le-service-en-bref/nous-contacter', 5), ('https://www.chuv.ch/fr/otr/otr-home/le-service-en-bref/notre-equipe', 5), ('https://www.chuv.ch/fr/otr/otr-home/le-service-en-bref/notre-equipe/notre-equipe-administrative', 5), ('https://www.chuv.ch/fr/otr/otr-home/le-service-en-bref/notre-equipe/nos-medecins-cadres', 4), ('https://www.chuv.ch/fr/otr/otr-home/le-service-en-bref/notre-equipe/nos-chefs-de-clinique', 4)]
- Best contact page: https://www.chuv.ch/fr/otr/otr-home/le-service-en-bref/nous-contacter (status 200)
  - patterns: ['base64_email_candidate', 'contact_form', 'typo3']
      - `base64_email_candidate`: `package/Resources/Public/Icons/Favicons/favicon`
      - `base64_email_candidate`: `/typo3temp/assets/compressed/merged`
      - `contact_form`: `<form`
      - `typo3`: `typo3conf`
      - `typo3`: `typo3temp`

