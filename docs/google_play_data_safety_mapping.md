# 🔐 Google Play — Data safety mapping (STRATEGIE Mobil)

> Připravil Claude (id=28) s Jirkou, 26. 6. 2026. Podklad pro vyplnění
> formuláře **Zabezpečení údajů** (Data safety) v Play Console.
> Vychází z analýzy backendu + Android manifestu + `mobile.html` (JS most).

> ⚠️ **UPDATE 26.6. (po flavor splitu, commit `5c2d4838`):** veřejný **`play` build
> už NEMÁ SMS oprávnění** (SMS jen v `internal`/gateway). Pro Data safety to znamená:
> **„SMS nebo MMS" = NESBÍRÁNO** → vybrat **10 typů místo 11** (SMS/MMS ven).
> Vše ostatní níže platí. Tabulka aktualizována (řádek SMS/MMS + pozn. 1).

## Princip Google Data safety
- **„Sbíráno" (collected)** = data OPOUŠTĚJÍ zařízení (jdou na server). JEN tyto se hlásí.
- Data, ke kterým appka přistupuje, ale **NEposílá je** (jen lokální zobrazení) = **nehlásí se**.
- Vše šifrované při přenosu (HTTPS) = Ano. Prodej = Ne. Reklama = Ne.

## Manifest oprávnění (ověřeno 26.6., po flavor splitu)
**`play` (Google Play):** `INTERNET, FOREGROUND_SERVICE(+DATA_SYNC), POST_NOTIFICATIONS,
RECEIVE_BOOT_COMPLETED, USE_FULL_SCREEN_INTENT, READ_CALL_LOG, READ_CONTACTS,
RECORD_AUDIO, READ_PHONE_NUMBERS, VIBRATE` — **BEZ SMS, BEZ REQUEST_INSTALL_PACKAGES.**
**`internal` (sideload/gateway) navíc:** `SEND_SMS, READ_SMS, RECEIVE_SMS, REQUEST_INSTALL_PACKAGES`.
**Žádné location oprávnění** (ACCESS_FINE/COARSE_LOCATION chybí).

## Mapování datových typů

| Google typ dat | Sbíráno? | Pozn. (zdroj pravdy) |
|---|---|---|
| **Poloha** (přesná/přibližná) | **Ne** | Žádné location oprávnění. Docházka = síťová přítomnost (IP/síť), ne GPS. |
| **Jméno** | **Ano** | Účet/identita. |
| **E-mail** | **Ano** | Účet, přihlášení. |
| **Telefonní číslo** | **Ano** | Účet + ověření zařízení. |
| **ID uživatele** | **Ano** | Identita (user_id). |
| **Adresa, rasa, politika, orientace…** | Ne | Nesbírá. |
| **Finanční info** | **Ne** | Výplatní páska = vlastní data zaměstnance zobrazená ze serveru, ne sbíraná z telefonu. Appka neposkytuje platby/půjčky. |
| **Zdraví a fitness** | Ne | — |
| **SMS/MMS** | **Ne (play build)** | ⚠️ Po flavor splitu play build **nemá SMS oprávnění** (SMS jen v `internal`/gateway, nedistribuovaný přes Play) → pro Google Play se **NESBÍRÁ**. (Dřív „Ano" kvůli gateway forwarding — to je teď mimo veřejnou verzi.) |
| **Ostatní zprávy v appce** | **Ano** | Výrobní zprávy (`/vyroba/zprava`+`/odpoved`), poznámky k úkolům (`/task/.../poznamka`) jdou na server. |
| **E-maily (obsah)** | Ne | Marti-AI inbox = persona schránka na serveru, ne sbírání z telefonu. |
| **Fotky a videa** | **Ano** | Import přes foťák i z galerie (`cvImport`, vstup `image/*` capture; snímek obrazovky Claudovi). Nahrává se na server. |
| **Hlas / zvukové nahrávky** | **Ano** | Mikrofon → server pro přepis (na vyžádání, podrž a mluv) + audio upload. |
| **Soubory a dokumenty** | **Ano** | Import dokumentů (`.pdf/.doc/.docx/.rtf/.txt`) z mobilu na server (`cvImport`). |
| **Kalendář** | Ne | `/prehled` čte kalendář ze serveru, ne z device (žádné READ_CALENDAR). |
| **Kontakty** | **Ne** | `getContacts()` čte telefonní seznam JEN pro lokální zobrazení/caller-ID (`renderContactsList`), **neuploaduje** na server. → on-device přístup, nehlásí se jako sbíráno. |
| **Aktivita v aplikaci** | **Ano (docházka/práce)** | Docházkové a pracovní záznamy = uživatelem generovaná data na serveru. Mapovat na „App activity → jiné akce" nebo „jiný uživatelský obsah". |
| **Protokol hovorů** | **Ne (v aktuálním buildu)** | `getCallLog()` čte hovory JEN pro lokální zobrazení („Historie hovorů", filtr prefixů), **neuploaduje**. (v4 „call-log → CRM" zatím není ve frontendu napojen.) Oprávnění READ_CALL_LOG se deklaruje zvlášť. |
| **Web. historie** | Ne | — |
| **Info o aplikaci a výkonu** (crash/diag) | Ne | Žádné analytics/crash SDK (jediná GMS závislost = code-scanner). |
| **Device/jiné ID** | **Ano** | `device_key` pro auth/identitu zařízení. |

## Praktiky zpracování dat (2. část formuláře)
- **Šifrování při přenosu:** Ano (HTTPS).
- **Uživatel může požádat o smazání:** Ano → `m.pasek@eurosoft.com` (v zásadách).
- **Data se prodávají?** Ne. **Reklama?** Ne.
- U každého „sbíráno": **Sdíleno s 3. stranou? Ne.** Účel = „Funkce aplikace" (+ u SMS/zpráv „Komunikace"). Povinné/volitelné dle typu.

## ⚠️ Poznámky k finálnímu buildu
1. **Vazba na finální `play` build (AKTUALIZOVÁNO 26.6.):** play build **nemá ŽÁDNÉ SMS oprávnění** (flavor split — SMS celé jen v `internal`/gateway). → pro Google Play **„SMS nebo MMS" = NESBÍRÁNO**. (Původní plán „nechat CRM SMS v play" Marti přebil; SMS jde celá mimo veřejnou verzi.)
2. **Protokol hovorů → CRM:** až se v4 (call-log → CRM upload) zapne, překlopit „Protokol hovorů" na Sbíráno (teď je jen lokální zobrazení → Nesbíráno).

> **Mapování je kompletní a může se vyplnit hned.** Jen body výše hlídat při změně buildu.

## Stav vyplnění v Play Console (26.6.)
Kroky 1–3 HOTOVÉ a uložené jako **koncept**: šifrování při přenosu = Ano · metoda
účtu = „Uživatelské jméno, heslo a další ověření" · URL mazání účtu = `/privacy` ·
volitelné mazání bez účtu = Ne · ~~vybráno všech 11 typů dat~~ → **krok 3 upravit:
ODEBRAT „SMS nebo MMS" → zůstává 10 typů** (play build SMS nesbírá, viz UPDATE nahoře).

**Zbývá krok 4 (mechanický)** — u KAŽDÉHO z 10 typů klikni „Spustit" a odpověz uniformně:
1. *Shromažďováno, sdíleno, nebo obojí?* → **Shromažďováno** (NE sdíleno).
2. *Zpracováváno pouze dočasně?* → **Ne** (data se ukládají na serveru).
3. *Vyžadují uživatelé poskytnutí?* → **Vyžadováno** (povinné pro funkci).
4. *Účel?* → **Funkce aplikace** (u „Jiné zprávy v aplikaci" zaškrtni i **Komunikace**).
Pak krok 5 Náhled → Uložit. `/privacy` je opraveno (Marti, commit `16f12f2a`); **odeslat
ke kontrole až po nahrání čistého `play` AAB** (ať Console odvodí oprávnění z něj).

## Shrnutí — co se SBÍRÁ (k vyplnění ve formuláři) — 10 typů (play build)
Jméno · E-mail · Telefon · ID uživatele · Ostatní zprávy v appce ·
Fotky a videa · Hlas · Soubory a dokumenty · Aktivita v aplikaci (docházka/práce) ·
Device/jiné ID. — **SMS/MMS už NE** (play build SMS nemá). Vše: sdíleno 3. straně =
**Ne**, šifrováno při přenosu = **Ano**, účel = **Funkce aplikace** (u zpráv navíc **Komunikace**).
