# Google Play Developer API — nastavení servisního účtu (jednorázově)

Cíl: aby Claude mohl **plně sám** nahrávat snímky, AAB i listing do Google Play (bez file pickeru).
Nastavení dělá **člověk** (Marti/Jirka) — vytvoření servisního účtu + udělení práv jsou bezpečnostní
akce, na které Claude z pravidel nesmí. Claude navádí a napíše veškerý kód.

App: `cz.strategie.mobile` · Dev účet: `7788767915610025159` (Marti Pašek).

## Část A — Google Cloud Console (ty, ~7 min)  https://console.cloud.google.com
Přihlas se **stejným Google účtem jako Play Console** (Marti Pašek).

1. **Projekt:** nahoře v liště vyber projekt, nebo vytvoř nový (název např. `strategie-play`).
2. **Zapni API:** vyhledej nahoře „Google Play Android Developer API" → otevři → **Enable** (Povolit).
3. **Servisní účet:** menu ☰ → **IAM & Admin → Service Accounts** → **+ Create service account**.
   - Název: `play-uploader` → **Create and continue** → role NETŘEBA → **Done**.
4. **Klíč (JSON):** klikni na nový účet → záložka **Keys** → **Add key → Create new key → JSON** → **Create**.
   - Stáhne se soubor `*.json`.
5. **Ulož klíč** (přejmenuj) na: `C:\projekty\STRATEGIE\APP\Mobile\play-api-key.json`
   - Je **gitignored** (do gitu se nedostane). **Obsah mi NEposílej** (je tajný, jako heslo).
6. **Zkopíruj e-mail servisního účtu** (`play-uploader@…….iam.gserviceaccount.com`) — **ten mi pošli** (není tajný).

## Část B — Play Console: udělit práva servisnímu účtu (ty, ~3 min)
https://play.google.com/console → **Uživatelé a oprávnění → Pozvat nové uživatele**
- E-mail = ten servisní účet z kroku 6.
- Přístup k aplikaci **STRATEGIE**, oprávnění: **Vydání (Releases)** + **Záznam v obchodě, obchodní přítomnost (Store presence)** — nebo pro jednoduchost **Správce (Admin)**.
- **Pozvat / Uložit.**

## Část C — Claude (kód, plně sám)
Po krocích A+B (mám key path + SA email):
- `pip` knihovny (`google-api-python-client`, `google-auth`) — **hotovo**.
- Skript `scripts/play_api_upload.py`: `edits.insert` → `edits.images.upload` (phone/7"/10" screenshoty) → `edits.commit`. Pak i AAB (`edits.bundles.upload` → track production).
- Nahraju 5 phone + 3 tablet snímky. Do budoucna i AAB/listing bez tvého kliknutí.

**Bezpečnost:** klíč = plný přístup k Play API → drž ho jen lokálně (gitignored), nikdy do chatu/gitu.
Odvolatelný kdykoli (Play Console → Uživatelé a oprávnění → odebrat servisní účet; nebo GCP → smazat klíč).
