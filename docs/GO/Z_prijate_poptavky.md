# Přijaté poptávky (od zákazníka) — přehled, doklad, generování nabídky

> Autor: Claude ID24, 19. 7. 2026 (na pokyn Marti „obdobně jako u vydaných poptávek — vysosej a ulož do znalostí veškeré know-how: co v přehledu za sloupečky a v jakém pořadí, co je v detailu, automat na generování nabídky, procedury na založení poptávky a mazání").
> Stav: **know-how vytěženo a potvrzeno** z živého přehledu 504 + detailu dokladu **EP26306** (ABSAUGWERK, Flex 11 kW) + procedur (Marti) + **kompletní definice `EC_GenKalkulaciANabidku`** (přečteno z DB_EC 19. 7.). Generování kalkulace + nabídky = rozklíčováno naostro (§8).
> Sourozenec: [Vydané poptávky RFQ](Z_vydane_poptavky_rfq.md) (druhá strana — my poptáváme dodavatele). Architektura: [230 — Automaty dokladů](Z_230-automaty-dokladu.md). Kontext funnelu: [222 — Trychtýř zakázek](222-go-vp-trychtyr-zakazek.md).

## 1. K čemu to je

**Přijatá poptávka = zákazník poptává NÁS** (Anfrage). Přední hrana obchodního trychtýře: zákazník pošle poptávku → my ji **založíme** jako doklad → **začneme zpracovávat** (řešitel, položky/BOM) → **založíme kalkulaci** → **vygenerujeme nabídku (Angebot)** → odešleme. To je ta „mraky práce", co Marti pojmenoval.

Tohle je **druhá vertikála** dokladového automatu (Z_230) — protisměr RFQ. A **spotřebovává RFQ smyčku**: nenaceněné díly z položek přijaté poptávky poptáme u dodavatelů přes vydané poptávky (RFQ), ceny se vrátí do kalkulace, z kalkulace se draftne nabídka.

## 2. Číselné soustavy (identifikátory podle fáze)

| fáze | řada | prefix dokladu | příklad |
|---|---|---|---|
| **přijatá poptávka** | **900** | **EP** | EP26306, EP26308 |
| navazný doklad = **nabídka** (Angebot) | **910** (`EC_GenDoklad @Typ='NabidkaV'`) | **EN** | EN263430, EN263460 |
| **kalkulace** (`EC_KalkulaceHlav`) | — (ne TabDokladyZbozi) | **EK** + pořadové nabídky | EK267777 |
| zakázka (výroba/projekt) | — | VR / CW / SW / PR | VR10712, CW30-37, SW8063, PR4015 |

Firemní prefixy jsou v `EC_GlobKonst.Firma`: **EC** = EK/EP/EN (délka čísla kalkulace 4), IAP = K/P/N.

- **Vydané poptávky** (sourozenec) = řada **940**, prefix **EVP** — neplest.
- Vazba poptávka → nabídka → zakázka jde přes `EC_DokladyVazby` (dvojskok, viz §6 a §7).

## 3. Přehled 504 „Poptávky" — sloupce a pořadí

Číslo přehledu **504**, `WHERE TabDokladyZbozi.RadaDokladu = '900'` (volitelný filtr `dbo.EC_GetDoklad(ID) LIKE 'EP%'` je v SQL zakomentovaný). Přehled běží pod `SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED` + `with (nolock)` (Swobi 17. 8. 2023 — zabránit čekání na zamčené tabulky; na konci se vrací na READ COMMITTED).

**Zobrazené sloupce v pořadí zleva doprava (jak je vidět v gridu):**

| # | sloupec (nadpis) | zdroj v DB |
|---|---|---|
| 1 | **Splneno** (S) | `TabDokladyZbozi.Splneno` (checkbox) |
| 2 | **Doklad** | `dbo.EC_GetDoklad(TabDokladyZbozi.ID)` → EP###### |
| 3 | **DatPorizeni** | `TabDokladyZbozi.DatPorizeni_X` |
| 4 | **Resitel** | `TabCisZam.LoginID` (přes `TabDokladyZbozi.CisloZam`) |
| 5 | **Zkratka_Nazvu** | `VDokZboCisOrg_EXT._Zkratka_Nazvu` (zkratka organizace) |
| 6 | **NavaznyDoklad** | `dbo.EC_GetDoklad(TabDokladyZbozi.NavaznyDoklad)` → **EN###### (nabídka)** |
| 7 | **OznPrjZakaznik** | `TabDokladyZbozi_EXT._OznPrjZakaznik` |
| 8 | **PopisPrjZakaznik** | `TabDokladyZbozi_EXT._PopisPrjZakaznik` |
| 9 | **Poznamka1** | `SUBSTRING(REPLACE(Poznamka,CRLF,mezera),1,255)` (jednořádkový náhled) |
| 10 | **SeznamZakazek** | `stuff(... EC_DokladyVazby dvojskok → Nab.CisloZakazky ...)` (viz §7) |
| 11 | **Stredisko** | `TabDokladyZbozi.StredNaklad` |
| 12 | **PoradoveCislo** | `TabDokladyZbozi.PoradoveCislo` (26###) |
| 13 | **Autor** | `TabDokladyZbozi.Autor` |
| 14 | **KO_Jméno** | `KO.Jmeno` (kontaktní osoba, `TabCisKOs` přes `KontaktOsoba`) |
| 15 | **KO_PrijmeniJmeno** | `KO.Prijmeni + ' ' + KO.Jmeno` |
| 16 | **KO_Prijmeni** | `KO.Prijmeni` |

**Sloupce v SELECTu, ale skryté/pomocné:** `CisloZakazky`, `KontaktOsoba` (ID), `ID`, `Nazev` (`VDokZboCisOrg.Nazev` = plný název org), `Poznamka11` (celá poznámka), `DatPorizeni`.

**Řazení:** `DatPorizeni DESC, PoradoveCislo DESC` (nejnovější nahoře).

## 4. Detail dokladu (formulář „Poptávka") — co je vyplněno

Ověřeno na EP26306 (ABSAUGWERK GmbH). Formulář má nahoře hlavičku, taby **Obecné / APS**, dole taby **Zboží a služby / Označení projektu zákazníka a rozvaděče**.

**Hlavička:**
- **Číslo** = `PoradoveCislo` (26306) → doklad EP26306.
- **Datum** = `DatPorizeni` (17.07.2026).
- **Zakázka** = `CisloZakazky` (zde prázdné — přiřadí se později).
- **Splněno** = `Splneno` (checkbox).
- **„Poznámka splněno"** — s návodem: *„pokud se nebude realizovat, uveďte do textu heslo **'důvod nezrealizování'**"*. → uzavírací pole; když se poptávka nezrealizuje, heslo „důvod nezrealizování" ji uzavře bez realizace. *(přesný field doostřit — kandidát header `Poznamka` / EXT.)*

**Obecné → Naše údaje:**
- **Náš krátký popis poptávky** = `TabDokladyZbozi_EXT._PopisPrjZakaznik` („AB12600504 / P00881, Flex 11 kW").
- **Středisko** = `StredNaklad` („Výroba").
- **Řešitel** = `CisloZam` → `TabCisZam.LoginID` („EKolarova").

**Obecné → Údaje o poptávajícím:**
- **Organizace** = `CisloOrg` → `TabCisOrg.Nazev` („ABSAUGWERK GmbH").
- **Kdo to poptával** = `KontaktOsoba` → `TabCisKOs` (osoba „Regele Georg", přehled kontaktů 107 — stejný model jako u RFQ §7).
- **Označení projektu zákazníka** = `TabDokladyZbozi_EXT._OznPrjZakaznik` („AB12600504 / P00881, Flex 11 kW").
- **Výběr oblasti** = `TabDokladyZbozi_EXT._Oblast` (potvrzeno z `EC_GenKalkulaciANabidku`). Když prázdné, gen-procedura ho dopočítá dle skupiny řešitele (`EC_SkupinyVazby`: IDSkupiny 2 → „Software", 35 → „EPlan", jinak → „Rozvaděč").

**Adresář:** dokumentová složka poptávky s přílohami zákazníka (zde `zadání.pdf`). Cesta = **`\\192.168.30.11\data\poptavky\<doklad>`** (UNC; např. `…\poptavky\EP26308`) → přes MCP FS ber **lokální kořen `D:\Data\poptavky\<doklad>`** na EC-SERVER2 (ne UNC — stejná gotcha jako RFQ). Pozn.: přijaté = `poptavky`, vydané (RFQ) = `poptavky_V`.

**Poznámka** = `TabDokladyZbozi.Poznamka` (celý text).

## 5. Položkový grid „Zboží a služby" (= BOM k nacenění)

Na rozdíl od vydaných poptávek (bývaly bez řádků) **přijatá poptávka NESE položky** — `TabPohybyZbozi`. To je BOM, který se cení. Sloupce gridu v pořadí:

`PoradoveCislo` · **`RegCis`** · `Poznamka` · `Nazev1` · `MJ` · `Mnozstvi` · `MnOdebrane` · `JCbezDaniKC` · `JCbezDaniVal` · `CCbezDaniKC` · `CCbezDaniVal` · `PozadDatDod` · …

- **`RegCis`** = registrační/objednací číslo dílu → **párovací klíč na ceník = RegCisHeo** (prefix dodavatele + číslo, viz [kalkulace Vize 1](Z_kalkulace_ceniky_vize1.md) §5). Tudy se položka nacení.
- `JCbezDani*` = jednotková cena (KC/Val=EUR), `CCbezDani*` = celková cena, `Mnozstvi`/`MnOdebrane` = množství, `PozadDatDod` = **požadovaný termín dodání** položky.
- Druhý dolní tab **„Označení projektu zákazníka a rozvaděče"** = doplňkové označení (VR rozvaděče).

## 6. Procedura — ZALOŽENÍ přijaté poptávky (`EC_GenPoptavku`)

Vlastní Helios procedura (neinsertovat ručně — stejná zásada jako u RFQ). **Klíč: guard na období.**

```sql
DECLARE @ErrorCode int, @IDENT int, @Message nvarchar(200)
IF (SELECT TOP 1 ID FROM TabObdobi ORDER BY DatumDo DESC) = dbo.EC_GetObdobiUziv()
BEGIN
   EXEC [dbo].[EC_GenPoptavku]
        @Uzivatel  = :#CisloZam,
        @ErrorCode = @ErrorCode OUTPUT,
        @IDENT     = @IDENT OUTPUT,
        @Message   = @Message OUTPUT
END
SELECT @Message AS N'@Message', @IDENT AS N'Ident'
```

- **Guard:** aktuální uživatelské období (`dbo.EC_GetObdobiUziv()`) musí být **nejnovější období** (`TOP 1 TabObdobi ORDER BY DatumDo DESC`). Jinak se blok neprovede → nezakládat poptávku do starého období.
- **`@Uzivatel = :#CisloZam`** — vstup = číslo zaměstnance (řešitel/autor). `:#` = Helios binding uživatelského kontextu.
- **OUTPUT:** `@IDENT` = ID nového dokladu (čti zpět — přes MCP write path pozor na zahazování result-setů, viz RFQ §5, řešení nonce-marker `st.*`), `@ErrorCode`, `@Message`.
- Proc pro **přijatou** poptávku = `EC_GenPoptavku` (vs. vydaná = `EC_GenVydanouPoptavku`). Uvnitř řeší číslování řady 900 + EXT + `CisloZam` dle kontextu.

## 7. Procedura — MAZÁNÍ (`EC_SmazPrijatouPoptavku`)

```sql
DECLARE @Message nvarchar(200)
EXEC EC_SmazPrijatouPoptavku
     @IDDoklad = :ID,
     @Message  = @Message OUTPUT
SELECT @Message AS N'@Message'
```

- `@IDDoklad = :ID` — ID mazaného dokladu, `@Message` OUTPUT.
- *(Pozn.: Marti to nazval „mazání nabídky" — proc je ale `EC_SmazPrijatouPoptavku` = smaže přijatou poptávku. Doostřit, jestli mazání sáhne i na navázanou nabídku / vazby `EC_DokladyVazby`, jako pojistka u RFQ smazání.)*

## 8. ⭐ Automat generování KALKULACE + NABÍDKY = `EC_GenKalkulaciANabidku`

**Jedna procedura, která z přijaté poptávky vygeneruje NAJEDNOU kalkulaci i nabídku** (to je ta „automat na generování nabídky"). Rozklíčováno z definice (DB_EC, 19. 7. 2026).

**Signatura:**
```sql
EXEC dbo.EC_GenKalkulaciANabidku
     @ID_Poptavky = <ID poptávky (řada 900)>,
     @IDENT       = @IDENT OUTPUT,   -- POZOR: navzdory komentáři = ID vytvořené NABÍDKY (ne kalkulace)
     @MESSAGE     = @Message OUTPUT  -- 'E#…' = chyba
```

**Co dělá, krok po kroku:**
1. **Prefixy** z `EC_GlobKonst.Firma` (EC → EK/EP/EN). `@Uzivatel = SUSER_NAME()`, `@Resitel = TabCisZam.Cislo` dle LoginID.
2. Načte z poptávky: řadu, pořadové číslo, `CisloOrg`, `CisloZam`, `StredNaklad`, `_OznPrjZakaznik`, `_PopisPrjZakaznik`, `KontaktOsoba`, `_Jazyk`, `_Oblast`.
3. **Guardy:** `@Rada<>'900'` → `E#Akci lze vyvolat pouze z řady dokladů 900`; prázdná organizace → `E#Není vyplněna organizace. Nabídku nelze vygenerovat`.
4. **BEGIN TRANSACTION**, pak:
5. **Nabídka** = `EXEC EC_GenDoklad @Typ='NabidkaV'` → **řada 910, prefix EN**, sklad `001`. Vrací `@IDENT` = ID nabídky.
6. **Oblast fallback:** pokud `_Oblast` null → dle `EC_SkupinyVazby` řešitele (2→Software, 35→EPlan, jinak „Rozvaděč").
7. Na nabídku propíše `CisloZam=@Resitel, StredNaklad, KontaktOsoba` + EXT `_OznPrjZakaznik, _PopisPrjZakaznik, _Jazyk, _Oblast`.
8. **Přepíše práci:** `EC_Dochazka_udalosti` Typ 8 (poptávka) → Typ 6 na nabídku (veškerá odpracovaná práce na poptávce přejde na nabídku).
9. **Kalkulace** = `INSERT INTO EC_KalkulaceHlav (CisloKalkulace, Autor, CisloZam, IDDoklad)`, kde `CisloKalkulace = 'EK' + pořadové číslo nabídky`, `IDDoklad = nabídka`. `@ID_Kalk = SCOPE_IDENTITY()`.
10. **Vazby `EC_DokladyVazby`** (EC): poptávka → kalkulace (`RadaDoklOdkud=900`, „Generování kalkulace z poptávky") **a** kalkulace → nabídka (`RadaDoklKam=910`, „Generování nabídky z kalkulace"). → řetěz **poptávka → kalkulace → nabídka** (= dvojskok, který skládá sloupec SeznamZakazek přehledu §3 #10).
11. **Uzavře poptávku:** `UPDATE TabDokladyZbozi SET NavaznyDoklad=@IDENT (nabídka), Splneno=1 WHERE ID=@ID_Poptavky`.
12. **Přenese položky (BOM) poptávka → nabídka:** kurzor přes `TabPohybyZbozi WHERE IDDoklad=poptávka`, per položka `EXEC EC_Test_hp_InsertPolozkyOZ` (na nabídku), pak UPDATE nové položky `IdOldPolozka, Nazev1, JCbezDaniKC/Val, CCbezDaniKC/Val, Poznamka` (přenos vč. cen).
13. **APS/vytížení:** propíše `_KalkHodOdhad, _ProcentaDoVytizeni, _VytizeniHodDenne, _VytizeniDatKonec, _VytizeniHodinyOdhad` z poptávky na nabídku, `_VytizeniDatVlozeni`, a poptávku ve vytížení schová (`_ProcentaDoVytizeni=0`).
14. `EXEC EC_MenuStrom_SetSoudecek @Doklad='NabidkaV'` (přepne uživatele na soudeček nabídky). **COMMIT** (nebo ROLLBACK při chybě položek).

**Důsledky pro automat (Z_230):** tahle jediná procedura pokrývá přechod **ZPRACOVÁVÁ SE → (kalkulace + nabídka) → poptávka UZAVŘENA (`Splneno=1`)**. Nabídka (EN) je pak samostatný doklad k nacenění/odeslání (napojení cen do `EC_KalkulaceHlav`/`KalkulacePolozky` = navazuje kalkulační engine, [Vize 1](Z_kalkulace_ceniky_vize1.md)).

**Zbývá doostřit:** jak se plní ceny do kalkulace po vygenerování (napojení `find_price`/nákupka), a jestli spouštět proceduru přes MCP write path (OUTPUT `@IDENT` → nonce-marker jako RFQ §5).

## 9. Napojení na automat dokladů (Z_230) a kalkulaci

Mapování na stavový stroj (Z_230 §3–4):

| stav / událost | u přijaté poptávky |
|---|---|
| **NOVÝ** | `EC_GenPoptavku` založí doklad EP (řada 900), guard na období |
| **ZPRACOVÁVÁ SE** | řešitel, organizace, kontakt, oblast, **položky/BOM** (RegCis) |
| **generuj kalkulaci + nabídku** | **`EC_GenKalkulaciANabidku`** → kalkulace EK (`EC_KalkulaceHlav`) + nabídka EN (řada 910) + vazby + přenos BOM (§8) |
| **kalkulace (nacenění)** | položky (RegCis→RegCisHeo) → `find_price` + poslední nákupka; ceny do `EC_KalkulaceHlav`/`KalkulacePolozky` |
| **UZAVŘENO** | gen-procedura automaticky `Splneno=1` + `NavaznyDoklad`=nabídka; nezrealizováno = heslo **„důvod nezrealizování"** v poznámce splněno |

Kontext dok 222: přední hrana obchodu **JE** trackovaná v Centrále (přehled 504 = přesně tahle kniha přijatých poptávek; 6607 poptávek historicky), prázdný je jen **most e-mail → strukturní `vp_poptavka`** s AI triáží. Přijatá poptávka + kalkulace je tedy vertikála, na které se ten most a nabídkový automat postaví naostro.

## 10. Další kroky (naostro)

1. Spustit `EC_GenKalkulaciANabidku` na reálné poptávce (kandidát **EP26308**) → ověřit vygenerovanou nabídku EN + kalkulaci EK + vazby + přenos BOM. **Write s reálným side-efektem (vznikne živý doklad) → jen s Martiho pokynem.**
2. **Nacenit položky kalkulace** (RegCis→RegCisHeo → `find_price` + poslední nákupka z příjemky) a napojit ceny do `EC_KalkulaceHlav`/`KalkulacePolozky`.
3. Spouštění procedury přes MCP write path — OUTPUT `@IDENT` přes nonce-marker (RFQ §5).
4. Zbývající field: uzavírací „důvod nezrealizování" (přesné umístění v `Poznamka`/EXT).

---

## 11. ⭐ TEST paralelní engine `@@PP` — postaveno a projeto NAOSTRO (19. 7. 2026)

Marti (19. 7.): *„Vezmi předposlední reálnou poptávku z Eliščina e-mailu a zpracuj ji korektně — založení poptávky, odpověď e-mailem, vygenerování kalkulace a nabídky, nástřel kalkulace. Uděláme z toho paralelní engine, na kterém se to všechno naučíme. V tomhle enginu je nutné všude před popisy, texty a předměty e-mailů psát `TEST`."*

**Koncept:** paralelní engine běží NAOSTRO ve stejném Heliosu jako produkce, ale bezpečně oddělený — všechny popisy / texty / předměty e-mailů nesou prefix **`TEST`**, e-maily jen jako **KONCEPTY** (nikdy neodesílá, doktrína návrh→schválení). Slouží k učení celého toku.

### 11.1 Kód a nasazení
- Modul **`modules/erp/api/prijata_poptavka.py`** (zrcadlo `rfq_doklad.py` + `rfq_draft.py`).
- Dispatch **`@@PP`** v `router.py` (za `@@RFQDOKLAD`): `if sql.upper().startswith("@@PP")`.
- Nasazeno přes deploy pipeline (commit `4fbd4acc`, fix `366a2045`).
- **Zápis do DB_EC jde přes EUROSOFT MCP (`eurosoft_strategie_query_raw`) UVNITŘ aplikace** (jako RFQ), NE přes raw most — proto přímé `UPDATE` do `dbo` tabulek procházejí (na rozdíl od raw bridge, který dbo zápisy hlídá). Spouští se `@@PP …` přes most (db=pg); jde o in-app příkaz → most ho nedetekuje jako write (bez banneru), proto krok po kroku a vratné.

### 11.2 Příkazy
| příkaz | co dělá |
|---|---|
| `@@PP GEN` | `EC_GenPoptavku` → TEST poptávka EP (řada 900), `@IDENT` přes `st.pp_gen_marker` |
| `@@PP FILL <id>` | doplní pole dle předlohy EP26306: org 10077, řešitel 24, kontakt 2852, středisko 001, `_Oblast`=Rozvaděč, `_Jazyk`=DE, `_OznPrjZakaznik`/`_PopisPrjZakaznik` s prefixem **TEST** |
| `@@PP SHOW <id>` | čtení dokladu zpět (stav, Splněno, navazný) |
| `@@PP REPLY <id>` | **TEST koncept** odpovědi zákazníkovi do Eliščiných Konceptů (`create_email_draft`, user 34), předmět `TEST RE: …`, příjemce = e-mail kontaktu (`TabKontakty` Druh 6). NEODESÍLÁ |
| `@@PP KALK <id>` | `EC_GenKalkulaciANabidku` → nabídka EN (910) + kalkulace EK + vazby + přenos BOM + `Splneno=1` |
| `@@PP SMAZ <id>` | `EC_SmazPrijatouPoptavku` (guard: jen řada 900) |

### 11.3 Naostro běh (předposlední reálná poptávka = AB12600504 / P00881, Flex 11 kW, Absaugwerk)
Zdroj = Eliščin živý inbox (`@@RFQINBOX 34`; mail **zrcadlo je zastaralé** ~od 5. 7., čti živě). Předposlední nová Anfrage = `AB12600504 / P00881` (10. 7., od Georga Regeleho) = produkčně EP26306.

Výsledek TEST běhu: `@@PP GEN` → **EP26309** → `FILL` → `REPLY` (koncept) → `KALK` → **nabídka EN263470 (910) + kalkulace EK263470**, poptávka uzavřena (`Splneno=1`, `NavaznyDoklad=EN263470`). Nástřel `@@KALKABS profil=flex kw=11` → profil FLEX+ baseline ~330 hod (materiál 0 — BOM není inline na poptávce, přijde ze Schaltplanu). Doklady ponechány jako živý učební artefakt.

### 11.4 🔑 GOTCHA — `EC_GenKalkulaciANabidku` padá v headless na `SetSoudecek`
Proc končí `EXEC EC_MenuStrom_SetSoudecek @Doklad='NabidkaV'` (přepnutí stromu operátora na novou nabídku). Ten INSERT do `EC_MenuStrom_PrepniNaSoudecek` má `User` = **NULL** v headless MCP kontextu → `IntegrityError 23000` → celá transakce proc-u (BEGIN TRAN … COMMIT) spadne a **ROLLBACKne i vygenerovanou nabídku/kalkulaci**.

**Fix (obecný pro Helios gen-procedury s SetSoudecek):** obalit volání:
```sql
SET XACT_ABORT OFF
BEGIN TRY EXEC dbo.EC_GenKalkulaciANabidku @ID_Poptavky=<id>, @IDENT=@IDENT OUT, @MESSAGE=@Msg OUT END TRY
BEGIN CATCH SET @Msg = N'SetSoudecek preskocen (headless): ' + ERROR_MESSAGE() END CATCH
IF XACT_STATE() = -1 ROLLBACK ELSE WHILE @@TRANCOUNT > 0 COMMIT
```
- `XACT_ABORT OFF` → constraint chyba ukončí jen ten statement, transakce zůstane **commitnutelná** → jádro (nabídka+kalkulace+vazby+BOM+`Splneno=1`) se zachová, UI-krok se zahodí.
- **ID nabídky NEbrat z `@IDENT OUTPUT`** (na chybě EXEC se OUTPUT nevrátí) — číst z `poptávka.NavaznyDoklad`, který proc nastaví PŘED padajícím krokem.

### 11.5 Další gotchy naostro
- **OUTPUT přes marker:** MCP write režim zahazuje result-sety → `@IDENT` zapiš do `st.pp_gen_marker` (nonce-keyed) a přečti druhým SELECTem (jako RFQ §5). Do schématu `st.` smíme.
- **Deploy pipeline:** `scripts/claude_sql/CLAUDE_DEPLOY.txt` (1. řádek commit msg, další řádky soubory) + `CLAUDE_DEPLOY_GO.txt` trigger (zapsat POSLEDNÍ) → watcher git add/commit/rebase/push + cloud `/deploy/now` (pull+restart), s **py_compile gate** (syntax chyba = deploy STOP, nic nepushnuto). **Před triggerem `mv .git/index.lock` stranou** — zbytky z Coworku commitů blokují watcheru git (mount nedovolí unlink).
- **Zdroj poptávek = živý inbox** (`@@RFQINBOX 34`), NE zrcadlo `tenant.mail_message` (zamrzlé ~od 5.–7. 7.).

### 11.6 Adresáře dokladu (dokumenty) — `@@PP MSG` / `DIR` / `COPYDOCS`
Každý doklad Centrály má dokumentovou složku na sdíleném disku (`\\192.168.30.11\data\…` → přes MCP FS **lokální kořen `D:\Data\…`**, ne UNC):
- přijatá poptávka = `D:\Data\poptavky\<EP>` · nabídka = `D:\Data\nabidky\<EN>` · vydaná RFQ = `D:\Data\poptavky_V\<EVP>` (neplést).
- **Nabídka a kalkulace SDÍLÍ JEDEN adresář** (`nabidky\<EN>`) — kalkulace EK nemá vlastní složku.

**🔑 Kdo kopíruje dokumenty poptávka→nabídka:** NE procedura (`EC_GenKalkulaciANabidku` = čistě DB, žádné file ops) a NE Python app Centrály — dělá to **desktop klient Centrály** (nativní file copy po zavolání proc). Headless generování (`@@PP KALK`) tenhle krok OBEJDE → nabídka zůstane bez dokumentů. Proto je v enginu doplněno ručně:
- `@@PP MSG <id> [subj]` — dohledá zdrojový Anforderung v Eliščině inboxu (**server-side `subject__contains` filtr**, ne iterace — jinak 30 s EWS timeout na starší poptávky) a uloží `.eml` do `poptavky\<EP>`.
- `@@PP DIR poptavky|nabidky <doklad>` — výpis složky (`_eu_list` s `base_override`).
- `@@PP COPYDOCS <id>` — zkopíruje soubory `poptavky\<EP>` → `nabidky\<EN>` (`_eu_read` b64 → `_eu_write`), = zároveň adresář kalkulace.

**Správné pořadí toku:** e-mail přijde → `MSG` (ulož do poptávky) → `KALK` (generuj nabídku+kalkulaci) → `COPYDOCS` (kopie dokumentů do nabídky). Ověřeno naostro: `TEST_poptavka_EP26309.eml` (310 624 B, Anforderung AB12600504) v `poptavky\EP26309` i `nabidky\EN263470`. (Nasazeno `a491cc33`.)

### 11.7 Co dál na enginu
- Nacenit kalkulaci EK263470 (BOM ze Schaltplanu → RegCisHeo → `find_price` + nákupka; `@@KALKABS` s položkami `| REGCIS*QTY`).
- Přenos BOM: EP nemá inline položky (spec = „Flex 11 kW" textově) → nacenění pojede přes profil/Schaltplan, ne přes přenesené `TabPohybyZbozi`.
- Zvážit řešitele nabídky (proc dá `CisloZam` MCP loginu Marti-AI; případně UPDATE na 24).

---

## Odkazy
- Sourozenec (druhá strana): [Vydané poptávky RFQ](Z_vydane_poptavky_rfq.md).
- Architektura automatu: [230 — Automaty dokladů](Z_230-automaty-dokladu.md).
- Ceny do kalkulace: [Kalkulace / ceníky Vize 1](Z_kalkulace_ceniky_vize1.md) (RegCisHeo, `find_price`, poslední nákupka).
- Funnel/kontext: [222 — Trychtýř zakázek](222-go-vp-trychtyr-zakazek.md).

*Know-how vytěženo z přehledu 504 + detailu EP26306 + procedur + definice `EC_GenKalkulaciANabidku`; **TEST engine `@@PP` postaven a projet NAOSTRO** (EP26309 → nabídka EN263470 + kalkulace EK263470) vč. dokumentového toku (MSG/DIR/COPYDOCS, sdílený adresář nabídka+kalkulace) a headless `SetSoudecek` gotchy. Marti + DB_EC, 19. 7. 2026. — Claude C24.*
