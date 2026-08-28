# HR moduly: E‑learning + Aktuality — návrh

> Zakládá **Claude‑25** (instance Šárky Novotné) na žádost Šárky, 24. 7. 2026.
> **Účel:** návrhový podklad pro dva nové moduly HR sekce — **E‑learning** (vzdělávání /
> školení) a **Aktuality** (interní nástěnka). Po vzoru Pinya HR a stávající HR sekce
> (`hr_hub` v `mobile.html`). Čti shora dolů; sekce **„OTEVŘENÉ OTÁZKY"** a **„CO DÁL"**
> jsou nejdůležitější. **Nic z toho zatím není nasazené** — je to návrh ke schválení.

---

## 0. Kontext a mantinely (než se sáhne na kód)

- **Kam to patří:** HR sekce Šárky (`hr_hub`), postavená po vzoru Vedení — bloky
  (`s("NÁZEV")` + `appgrid` s `appCell(emoji, popisek, 0, fn)`), obrazovky registrované
  do objektu `SCREENS` v `mobile.html`.
- **Kdo co schvaluje** (model Marti 23. 6.): **DDL** (nové tabulky, indexy, GRANTy) →
  **rodič** přes oranžový banner. **Šárčin vlastní HR obsah** (kurzy, aktuality, přiřazení,
  konfigurace) → **schvaluje si Šárka sama** v appce (CRUD bez banneru).
- **Data:** PostgreSQL `data_db`, schéma `tenant`, tenant **2 = EUROSOFT** (+ tenant
  **14 = INTERSOFT** — návrh je multi‑tenant ready, stejně jako docházka/režimy).
- **ACL:** admin strana `_hr_can_manage` (rodiče + skupina HR). Zaměstnanecká strana =
  vidí a plní jen **svoje** záznamy.
- **Konvence** (z docházky): `snake_case`, `source_system`, idempotentní zápisy,
  `created_at`/`updated_at`, `id GENERATED ALWAYS`, ACL na endpointu, audit do
  `tenant.att_audit` u citlivých změn.
- **GDPR:** vzdělávací a „přečteno" záznamy = **zaměstnanecké** (drží se kvůli auditu /
  ISO / doložení školení). U uchazečů se to neřeší (E‑learning i Aktuality jsou interní).

---

## 1. E‑LEARNING

### 1.1 K čemu to je (rozsah)
Interní vzdělávání a školení zaměstnanců: **kurzy** (materiály + volitelný test) →
**přiřazení** lidem/skupinám s termínem → **průchod** (sledování dokončení) →
**certifikát**. Tři hlavní scénáře, které to musí pokrýt:

1. **Povinná periodická školení** (BOZP, PO, ISO 27001, GDPR) — s **platností** (např.
   12/24 měsíců), po expiraci se **automaticky znovu přiřadí**. Napojení na
   `ZAZ‑13‑01 Školení bezpečnosti` a ISO cockpit (doložitelnost pro audit/TISAX).
2. **Onboarding nováčka** — sada kurzů se přiřadí automaticky při nástupu
   (napojení na Nábor → Nástupy).
3. **Odborný rozvoj** (elektrotechnika, měkké dovednosti) — dobrovolné i řízené kurzy;
   navazuje na `Elektrotechnika_AI_kurikulum_navrh.docx`, metodu učení (Hubbard podklady).

### 1.2 Datový model (návrh tabulek, schéma `tenant`)

| Tabulka | Klíčové sloupce | Poznámka |
|---|---|---|
| `elearning_kurz` | `id, tenant_id, kod, nazev, popis, kategorie, povinny, platnost_mesicu, autor_user_id, stav, created_at, updated_at` | `kategorie` ∈ {bozp, po, iso, gdpr, onboarding, odborny, mekke}; `stav` ∈ {draft, aktivni, archiv}; `platnost_mesicu` NULL = bez expirace |
| `elearning_lekce` | `id, kurz_id, poradi, nazev, typ, obsah, url, povinne` | `typ` ∈ {text, video, pdf, odkaz, scorm}; `obsah` = markdown/HTML nebo cesta na dokument |
| `elearning_test` | `id, kurz_id, nazev, min_uspesnost_pct, pocet_pokusu, casovy_limit_min` | volitelný — kurz nemusí mít test |
| `elearning_otazka` | `id, test_id, poradi, text, typ, body` | `typ` ∈ {single, multi, true_false} |
| `elearning_odpoved` | `id, otazka_id, text, spravne` | možnosti k otázce |
| `elearning_prirazeni` | `id, kurz_id, cil_typ, cil_id, termin_do, povinny, prirazeno_kym, prirazeno_kdy` | `cil_typ` ∈ {osoba, skupina, tenant}; hromadné přiřazení |
| `elearning_pruchod` | `id, kurz_id, att_employee_id, stav, procento, skore_pct, pokus, zahajeno_at, dokonceno_at, platnost_do, source_system` | jádro sledování; `stav` ∈ {nezahajeno, probiha, dokonceno, po_terminu, expirovano} |
| `elearning_certifikat` | `id, pruchod_id, cislo, vydano_at, platnost_do, pdf_path` | generuje se po dokončení (viz 1.5) |

**Vazby na identitu:** `att_employee_id` (ne holý user_id) — kvůli multi‑angažmá /
multi‑tenant, konzistentní s docházkou a režimy. Person‑resolution agreguj na `user_id`
(doctrine #24), školení se ale eviduje per angažmá/firma.

### 1.3 Obrazovky (do `hr_hub` + `SCREENS`)

**Admin (HR):**
- 🎓 **E‑learning** (`hr_elearning`) — seznam kurzů (stav, kategorie, počet přiřazených,
  % dokončení), editace kurzu (lekce + test), tlačítko **„➕ Přiřadit"** (osoba/skupina/
  tenant + termín).
- 📊 **Přehled školení** (`hr_elearning_prehled`) — matice lidé × povinné kurzy: kdo má
  hotovo / probíhá / po termínu / expiruje. Filtr „expiruje do 30 dní" pro periodická.

**Zaměstnanec:**
- 📚 **Moje kurzy** (`moje_kurzy`) — přiřazené kurzy, termín, stav, „Spustit"; průchod
  lekcemi → test → dokončení. Odkaz i z osobní karty.

### 1.4 Endpointy (vzor `/app/hr/...`)
```
# Admin (ACL _hr_can_manage)
GET  /app/hr/elearning                     # seznam kurzů + agregace
POST /app/hr/elearning/kurz/save           # upsert kurz + lekce + test
POST /app/hr/elearning/prirazeni/save      # přiřadit (osoba/skupina/tenant)
GET  /app/hr/elearning/prehled?obdobi=...  # matice dokončení, expirace

# Zaměstnanec (ACL = vlastní záznamy)
GET  /app/elearning/mine                   # moje přiřazené kurzy + stav
POST /app/elearning/lekce/complete         # {pruchod_id, lekce_id}
POST /app/elearning/test/submit            # {pruchod_id, odpovedi[]} → skóre, stav
```
Route ordering gotcha: literální cesty (`/prehled`, `/mine`) registrovat **před** `/{id}`.

### 1.5 Napojení (reuse, ať nestavíme dvakrát)
- **Certifikáty:** znovu použít `HR_sablony/certifikaty/gen_certifikat.py` (už umí
  generovat certifikát, viz „Certifikát 10 let"). Po `stav=dokonceno` → PDF do
  `elearning_certifikat.pdf_path`.
- **Notifikace:** modul `notifications` — připomínka X dní před termínem, upozornění na
  expiraci povinného školení, potvrzení o dokončení.
- **ISO / BOZP:** povinné kurzy s `platnost_mesicu` = doložitelnost školení pro ISO 27001
  / TISAX; přehled feedovat do ISO cockpitu. `ZAZ‑13‑01` jako první reálný kurz.
- **Onboarding:** při nástupu (Nábor → Nástupy) auto‑přiřadit onboarding sadu.

---

## 2. AKTUALITY (interní nástěnka)

### 2.1 K čemu to je (rozsah)
Interní **novinky / oznámení** pro zaměstnance: firemní sdělení, změny směrnic, události.
Klíčové vlastnosti: **připnutí** důležitého příspěvku, **cílení** (všichni / skupina /
tenant), a **potvrzení přečtení** u důležitých sdělení (compliance — např. seznámení se
směrnicí ISO 27001; „kdo četl" je doložitelné).

### 2.2 Datový model (schéma `tenant`)

| Tabulka | Klíčové sloupce | Poznámka |
|---|---|---|
| `aktualita` | `id, tenant_id, titulek, perex, obsah, kategorie, autor_user_id, stav, dulezitost, pripnuto, vyzaduje_potvrzeni, cil_typ, cil_id, publikovano_od, publikovano_do, created_at, updated_at` | `stav` ∈ {draft, publikovano, archiv}; `dulezitost` ∈ {normal, dulezite}; `cil_typ` ∈ {all, skupina, tenant} |
| `aktualita_priloha` | `id, aktualita_id, nazev, path, typ` | přílohy (PDF, obrázek, odkaz) |
| `aktualita_precteni` | `id, aktualita_id, user_id, precteno_at, potvrzeno` | read receipt; `potvrzeno=true` u `vyzaduje_potvrzeni` |
| `aktualita_reakce` | `id, aktualita_id, user_id, typ, created_at` | volitelné (👍/❤️), lze vypustit z v1 |

### 2.3 Obrazovky
**Admin (HR):** 📣 **Aktuality** (`hr_aktuality`) — správa příspěvků (napsat/upravit/
publikovat/archivovat, připnout, cílit, „vyžaduje potvrzení"), u každého **statistika
přečtení** (kolik z cílové skupiny přečetlo / potvrdilo).

**Zaměstnanec:** 📰 **Nástěnka** (`nastenka`) — feed publikovaných aktualit (připnuté
nahoře), detail, tlačítko **„Beru na vědomí"** u těch, co vyžadují potvrzení. Badge
s počtem nepřečtených.

### 2.4 Endpointy
```
# Admin (ACL _hr_can_manage)
GET  /app/hr/aktuality                 # správa + statistiky přečtení
POST /app/hr/aktuality/save            # upsert (draft/publish/archiv, pin, cíl)
GET  /app/hr/aktuality/{id}/precteni   # kdo četl / potvrdil

# Zaměstnanec
GET  /app/aktuality/feed               # publikované pro mě (dle cílení)
POST /app/aktuality/{id}/read          # {potvrdit: bool} → read receipt
```

### 2.5 Napojení
- **Notifikace:** nová důležitá aktualita → push/e‑mail přes `notifications`.
- **ISO 27001:** „vyžaduje potvrzení" = doložitelné seznámení se směrnicí (napojení na
  `MAPA_smernic.md`, ISO cockpit).
- **Osobní karta / Kdo kde dnes:** badge nepřečtených, ať to lidé vidí při přihlášení.

---

## 3. Společné pro oba moduly

### 3.1 Nový blok v HR hubu (návrh)
Do `hr_hub` přidat blok **„🎓 VZDĚLÁVÁNÍ & KOMUNIKACE"**:
```
🎓 E‑learning (hr_elearning) · 📊 Přehled školení (hr_elearning_prehled)
📣 Aktuality (hr_aktuality)
```
Zaměstnanecké obrazovky (`moje_kurzy`, `nastenka`) míří i z hlavní appky / osobní karty,
ne jen z HR hubu.

### 3.2 Cílení (společný pattern)
`cil_typ` + `cil_id` (osoba / skupina / tenant / all) používají obě agendy stejně —
jedna pomocná funkce `_resolve_cil(cil_typ, cil_id) → [att_employee/user]`.

### 3.3 Bezpečnost / audit
- DDL (CREATE TABLE) → rodič přes banner.
- Admin akce (publish, přiřazení, změna povinného kurzu) → audit řádek.
- Read receipts a skóre testů = citlivější → nedávat do G2007 / RAG (osobní).

---

## 4. OTEVŘENÉ OTÁZKY (na tebe / Martiho)

1. **E‑learning obsah lekcí:** stačí text/PDF/video‑odkaz (v1), nebo chceš i **SCORM**
   import (standard e‑learning balíčků)? SCORM = víc práce, ale kompatibilní s hotovými kurzy.
2. **Testy:** potřebuješ je hned v v1, nebo napřed „přečetl jsem / beru na vědomí" a testy
   až v druhé vlně?
3. **Periodická školení:** kdo je „zdroj pravdy" pro platnosti (BOZP 12 měs.? PO? ISO ročně?)
   — ať `platnost_mesicu` nastavíme reálně.
4. **Aktuality — komentáře/reakce:** chceš je (interakce), nebo držet nástěnku jen jako
   jednosměrné oznámení (jednodušší, méně moderování)?
5. **Cílení:** stačí „všichni / skupina / tenant", nebo i podle střediska / pozice / vedoucího?
6. **Kde žijí přílohy a videa** (dokumentový modul / úložiště) — navázat na existující
   `doc_gen` / media modul?

## 5. CO DÁL (návrh pořadí implementace)

1. **Odsouhlasit tento návrh** + zodpovědět otevřené otázky (rozsah v1).
2. **DDL** (tabulky výše) → připravím SQL, půjde přes **banner** (rodič).
3. **Aktuality v1** (jednodušší, rychlá výhra): tabulky + `hr_aktuality` + `nastenka` +
   read receipts. Hned použitelné pro reálná sdělení.
4. **E‑learning v1:** kurz + lekce + přiřazení + průchod + přehled; test a certifikát
   jako druhá vlna, pokud je nechceš hned.
5. **Napojení:** notifikace, ISO cockpit (doložitelnost), onboarding auto‑přiřazení.
6. **Zápis rozhodnutí do G2007** (oblast: nová `hr`/`vzdelavani`) po odsouhlasení —
   ať to příští instance nestaví znovu.

> **Poznámka k prioritě:** Aktuality doporučuji jako **první** (menší, rychle nasaditelné,
> okamžitá hodnota), E‑learning jako druhý (větší datový model + certifikáty). Ale klidně
> vezmeme oba naráz, když chceš.
