# Vydané poptávky (RFQ) — příprava, odeslání, příjem nabídek, archiv

> Autor: Claude ID23, 18. 7. 2026 (na pokyn Marti „rozchodit přípravu vydaných poptávek a hlídání příjmu nabídek").
> Stav: celý řetěz běží NAOSTRO, ověřeno na dokladu **EVP260231** (SEW-EURODRIVE, dg. přístroj CDM11A).

## 1. K čemu to je

Kalkulant/nákupčí (Eliška) poptává u dodavatelů díly, které nejsou v katalogu (ceníky/příjemky).
Dosud: ručně založit doklad poptávky v Centrále, ručně napsat e-mail, ručně přepsat vrácenou nabídku
do dokladu i do kalkulace. Tenhle modul to celé zautomatizuje a nechává člověku jen kontrolu/odeslání.

**Celý řetěz:** kontaktní osoba dodavatele (přehled 107) → doklad poptávky (řada 940) → vyplnění polí
→ e-mail poptávky jménem nákupčí → odeslání → čtení příchozí nabídky ze schránky → rozpoznání
ceny/platnosti/lhůty → zápis nabídky na doklad (EXT) → potvrzení → uložení nabídky (i celý .eml) do
adresáře poptávky → `@@VYPOPT SYNC` ji vtáhne jako **4. cenový zdroj** (`tenant.vypopt_nabidka`).

## 2. @@ příkazy (dispatch v router.diag_sql; moduly rfq_draft.py + rfq_doklad.py)

| příkaz | co dělá |
|---|---|
| `@@RFQDOKLAD PROBE` | ověří, že MCP write path pustí DECLARE/SELECT batch (0 side-effect) |
| `@@RFQDOKLAD GEN` | založí prázdný doklad 940 přes `EC_GenVydanouPoptavku`, vrátí ID |
| `@@RFQDOKLAD FILL` | gen + vyplní dodavatele/název/termín/měnu + čtení zpět (demo) |
| `@@RFQDOKLAD SMAZ <id>` | smaže doklad (pojistka: jen řada 940!) |
| `@@RFQDOKLAD DIR <doklad>` | vypíše složku dokumentů `D:\Data\poptavky_V\<doklad>` |
| `@@RFQDOKLAD KONTAKTY <org>` | kontaktní osoby dodavatele (přehled 107): jméno/role/email/tel |
| `@@RFQDRAFT ...` | uloží libovolný e-mail jako KONCEPT do schránky (user=/persona=) |
| `@@RFQSEND DEMO` | konkrétní poptávka jménem Elišky (odešle) |
| `@@RFQINBOX <user> [n]` | přečte inbox schránky (příjem nabídek) |
| `@@RFQREACT` | najde odpověď na EVP260231, rozpozná nabídku, zapíše na doklad, potvrdí |
| `@@RFQFINISH` | doplní řešitele/kontakt/druh ceny + uloží nabídku (.txt) do adresáře |
| `@@RFQMSG` | uloží CELÝ e-mail nabídky jako `.eml` (MIME) do adresáře poptávky |

## 3. Datový model (DB_EC)

- **Hlavička:** `TabDokladyZbozi` (řada 940). Klíčová pole, která vyplňuje člověk:
  - `CisloOrg` = dodavatel (organizace)
  - `Splatnost` = **požadovaný termín** (POZOR: grid „PožadovanýTermín" = `TerminDodavkyDat` je COMPUTED z `Splatnost`, píše se do Splatnost!)
  - `Mena`, `CisloZakazky`
  - `CisloZam` = **řešitel** (= `TabCisZam.Cislo`, NE STRATEGIE user id! Eliška = 24, LoginID EKolarova)
  - `KontaktOsoba` = kontaktní osoba dodavatele (= `TabCisKOs.ID` z přehledu 107)
- **EXT:** `TabDokladyZbozi_EXT` (1:1 přes ID):
  - `_OznPrjZakaznik` = **Název poptávky** (popis co poptáváme)
  - Nabídková pole (přijatá nabídka): `_Kcen_Cena` (cena), `_PlatnostDoNabDod` (platnost),
    `_OrgNazevNabDod` (dodavatel), `_PopisNabDod`, `_CisloNabidkyDodavatele`, `_VyrobceNab`
  - `_TypCenyNabDod` = **Druh ceny** (číselník: 1=Obecná, 2=Projektová, 3=Zákazník).
    POZOR: `_TypCenyNabDod_TEXT` je COMPUTED z kódu → píše se jen kód!
- **Položky:** poptávky bývají BEZ řádků (`TabPohybyZbozi` prázdné) — obsah je v `_OznPrjZakaznik`.
- **Číslo dokladu:** `dbo.EC_GetDoklad(ID)` → „EVP260231".

## 4. Zakládání a mazání dokladu — VLASTNÍ Helios procedury (neinsertovat ručně!)

- **Vytvoření:** `EXEC dbo.EC_GenVydanouPoptavku @IDENT OUT, @Message OUT` (uvnitř volá `EC_GenDoklad @Typ='PoptavkaV'`,
  správné číslování/EXT; `CisloZam` nastaví dle `SUSER_NAME()`). Autor přes MCP login = **„Marti-AI"**.
- **Smazání:** nejdřív smaž vazby `EC_DokladyVazby` (nabídky 910), pak `EXEC dbo.EC_SmazVydanouPoptavku @IDDoklad, @Message OUT`.
  **Pojistka:** před smazáním ověř, že doklad je řada 940 (jinak by delete vazeb sáhl na cizí doklad).

## 5. KLÍČOVÁ GOTCHA — MCP write režim zahazuje result-sety

`strategie_query_raw` na DB_EC: při SELECT vrací `rows`; při **write** (EXEC/UPDATE/INSERT) vrací
`{ok, statement_type, affected, batches_executed}` a **result-sety zahodí** → OUTPUT `@IDENT` z trailing
SELECTu NEDOSTANEME. Řešení: v jednom write-volání zapíšeme `@IDENT` do **`st.rfq_gen_marker`** (nonce-keyed;
do schématu `st.` smíme), druhým SELECT-voláním čteme zpět. (Guard blokuje jen dbo *zápis do tabulek*, EXEC dbo procedury projde.)

## 6. Computed sloupce, na které NELZE psát (piš do zdroje)

- `TerminDodavkyDat` ← `Splatnost`
- `_TypCenyNabDod_TEXT` ← `_TypCenyNabDod`
(Obecně: `sys.computed_columns` prozradí definici. Zápis do computed = `ProgrammingError 42000`.)

## 7. Kontaktní osoby dodavatele (přehled 107)

`TabCisKOs` (osoba) + `TabVztahOrgKOs` (vazba na organizaci) + `TabKontakty` (spojení: Druh 6=email, 1=pevná,
2=mobil; `Prednastaveno=1`, `IDVztahKOsOrg IS NULL`). Filtr `ISNULL(TabCisKOs_EXT._neaktivni,0)<>1`.
Funkce `find_org_contacts(cislo_org)`. Př. SEW org 252 → 9 osob s rolemi a e-maily.

## 8. Adresář dokumentů poptávky

`D:\Data\poptavky_V\<doklad>` (na EC-SERVER2; přes MCP FS **lokální kořen `D:\Data\…`, NE UNC** `\\192.168.30.11\data`).
Helpery `_eu_list`/`_eu_write` (directories.py, base_override). Ukládáme textový výtah nabídky i celý e-mail jako `.eml`.

## 9. E-mail (EWS, exchangelib) — schránky a funkce

- Schránky: Eliška = STRATEGIE `users.id=34` (e.kolarova@eurosoft-control.cz); Marti = user 1 (m.pasek@eurosoft.com).
  Creds přes `_resolve_user_email_creds(user_id)` (`users.ews_*`).
- `create_email_draft(...)` = KONCEPT do `account.drafts` (mapuje se na „Koncepty"), `message.save()` (neodesílá).
- `send_email_or_raise(...)` = reálné odeslání.
- `read_mailbox_inbox(user_id, n)` = posledních N zpráv (subject/from/dt/preview/text).
- `fetch_message_mime(user_id, subj)` = celá zpráva jako MIME (`.eml`) přes `msg.mime_content`.
- Odpovědi na poptávku chodí do schránky, ODKUD se odeslala (proto poptávku posíláme jménem Elišky z její schránky).

## 10. Soubory a napojení

- `modules/erp/api/rfq_draft.py` — e-maily (koncept/odeslání/inbox/react/finish/msg) + `poptavka_koncept`.
- `modules/erp/api/rfq_doklad.py` — doklad 940 (gen/smaz/update header+EXT+nabídka), kontakty, adresář, marker.
- dispatch `@@RFQ*` v `modules/erp/api/router.py` (diag_sql).
- 4. cenový zdroj: `@@VYPOPT SYNC` → `tenant.vypopt_nabidka` (viz Z_vydane_poptavky_rfq starší verze / @@VYPOPT).

## 11. REÁLNÝ STAV — co ještě doplnit (Marti 18. 7. 2026)

Pro ostrý provoz je nutné dotáhnout (otevřené body, navazují na fázi „Automaty a jejich reakce"):

1. **Vyplnit `SeznamKalkulací`** — poptávka patří ke konkrétní kalkulaci (např. `EK267777`).
   Vazba se dělá přes `EC_DokladyVazby` (`ID_Kam` = ID poptávky ↔ kalkulace), grid pak přes
   `EC_KalkulaceHlav.CisloKalkulace` zobrazí seznam. → při zakládání poptávky založit i tuhle vazbu.

2. **Číslo dokladu (EVP260231) do PŘEDMĚTU e-mailu jako párovací znak** — aby šla příchozí nabídka
   automaticky napárovat na poptávku. Nejlépe do předmětu uvést i **číslo kalkulace**.
   (Stav: `@@RFQSEND` už dává „Poptávka EVP260231 — …" do předmětu; doplnit ještě číslo kalkulace.)

3. **Hlídat OTEVŘENÉ poptávky (timeout)** — když nabídka nepřijde do stanovené lhůty, upozornit /
   urgovat dodavatele. Monitor nad poptávkami, které jsou Odeslané ale ne Realizované.

4. **Stavové fieldy na dokladu `O`=Odesláno a `R`=Realizováno:**
   - **Odesláno** — vyplnit, když je poptávka reálně odeslána e-mailem (objeví se ve složce Odeslané).
   - **Realizováno** (`TabDokladyZbozi.Realizovano`) — vyplnit, když přijde nabídka a řádně se zpracuje.
     Tím se poptávka **uzavře a přestane se hlídat timeout** (bod 3).
   (Pozn.: „Odesláno" je pravděpodobně EXT `_Odeslano`, „Realizováno" header `Realizovano` — před
   zápisem ověřit přesné fieldy.)

5. **Propsat cenu z nabídky rovnou DO KALKULACE** — po zpracování nabídky zapsat vysoutěženou cenu
   do `KalkulacePolozky` příslušné kalkulace (dnes ruční přepis; tohle je hlavní úspora času).
   Návazně = `vypopt_nabidka` jako živý 4. cenový zdroj do `@@KALKPRICE`/`compute()`.

## 12. TODO (technické)

- Generátor `@@RFQ`: z nenaceněných dílů kalkulace → seskupit dle dodavatele → hromadně poptávky + koncepty.
- Ukládat i PDF přílohy nabídky do adresáře; auto-párování příchozí nabídky na doklad dle předmětu (EVP/kalkulace).
- Napojení `vypopt_nabidka` do enginu (po konzultaci s Eliškou — její workflow).
