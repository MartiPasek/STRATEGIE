# Přijaté poptávky (od zákazníka) — přehled, doklad, generování nabídky

> Autor: Claude ID24, 19. 7. 2026 (na pokyn Marti „obdobně jako u vydaných poptávek — vysosej a ulož do znalostí veškeré know-how: co v přehledu za sloupečky a v jakém pořadí, co je v detailu, automat na generování nabídky, procedury na založení poptávky a mazání").
> Stav: **know-how vytěženo** z živého přehledu 504 + detailu dokladu **EP26306** (ABSAUGWERK, Flex 11 kW) + procedur, které dal Marti. Generování nabídky = mechanika popsána, přesná gen-procedura = doostřit naostro (jako u RFQ).
> Sourozenec: [Vydané poptávky RFQ](Z_vydane_poptavky_rfq.md) (druhá strana — my poptáváme dodavatele). Architektura: [230 — Automaty dokladů](Z_230-automaty-dokladu.md). Kontext funnelu: [222 — Trychtýř zakázek](222-go-vp-trychtyr-zakazek.md).

## 1. K čemu to je

**Přijatá poptávka = zákazník poptává NÁS** (Anfrage). Přední hrana obchodního trychtýře: zákazník pošle poptávku → my ji **založíme** jako doklad → **začneme zpracovávat** (řešitel, položky/BOM) → **založíme kalkulaci** → **vygenerujeme nabídku (Angebot)** → odešleme. To je ta „mraky práce", co Marti pojmenoval.

Tohle je **druhá vertikála** dokladového automatu (Z_230) — protisměr RFQ. A **spotřebovává RFQ smyčku**: nenaceněné díly z položek přijaté poptávky poptáme u dodavatelů přes vydané poptávky (RFQ), ceny se vrátí do kalkulace, z kalkulace se draftne nabídka.

## 2. Číselné soustavy (identifikátory podle fáze)

| fáze | řada | prefix dokladu | příklad |
|---|---|---|---|
| **přijatá poptávka** | **900** | **EP** | EP26306, EP26308 |
| navazný doklad = **nabídka** (Angebot) | *(řada nabídek — doostřit)* | **EN** | EN263430, EN263460 |
| zakázka (výroba/projekt) | — | VR / CW / SW / PR | VR10712, CW30-37, SW8063, PR4015 |

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
- **Výběr oblasti** = „Rozvaděč - VR" (číselník oblasti/druhu — *přesný field doostřit; kandidát `TabDruhDokZbo.DoplnkovyKod`*).

**Adresář:** dokumentová složka poptávky s přílohami zákazníka (zde `zadání.pdf`). Stejný princip jako RFQ adresář (`D:\Data\…\<doklad>` na EC-SERVER2, lokální kořen ne UNC) — *přesnou cestu pro přijaté poptávky doostřit.*

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

## 8. Automat na generování NABÍDKY (Angebot) — mechanika

Cíl: z přijaté poptávky (EP, 900) **vygenerovat nabídku (EN)** jako **navazný doklad** — to je ta „automat na generování nabídky", co má odlehčit ruční práci.

**Co je jisté z dat:**
- `TabDokladyZbozi.NavaznyDoklad` na poptávce ukazuje na **nabídku EN######** (sloupec 6 přehledu má u živých poptávek vyplněno EN…).
- Vazba se drží v **`EC_DokladyVazby`** a je to **dvojskok** (potvrzeno SQL přehledu): poptávka → nabídka → zakázka:
  ```sql
  FROM EC_DokladyVazby V                                   -- V.id_odkud = poptávka
  LEFT JOIN EC_DokladyVazby V2 ON V.id_kam = V2.id_odkud    -- V.id_kam   = nabídka
  LEFT JOIN TabDokladyZbozi Nab ON V2.id_kam = Nab.ID       -- V2.id_kam  = zakázka (Nab.CisloZakazky)
  WHERE V.id_odkud = <poptávka>
  ```
  → odtud se skládá sloupec **SeznamZakazek** (přehled §3, #10).

**Co doostřit naostro (další krok, jako jsme dělali RFQ):**
- Přesná **gen-procedura nabídky** (kandidát `EC_GenNabidku` / „Akce → generovat navazný doklad") + jaká je **řada nabídek (EN)**.
- Zda generátor přenese **položky (BOM)** z poptávky do nabídky a napojí kalkulaci.
- Jak se nastaví `NavaznyDoklad` + zapíše vazba `EC_DokladyVazby`.

## 9. Napojení na automat dokladů (Z_230) a kalkulaci

Mapování na stavový stroj (Z_230 §3–4):

| stav / událost | u přijaté poptávky |
|---|---|
| **NOVÝ** | `EC_GenPoptavku` založí doklad EP (řada 900), guard na období |
| **ZPRACOVÁVÁ SE** | řešitel, organizace, kontakt, oblast, **položky/BOM** (RegCis) |
| **kalkulace** | položky (RegCis→RegCisHeo) → nacenit přes `find_price` + poslední nákupka; kalkulace `ec_kalkulace_hlav` (engine 2014) |
| **generuj nabídku** | navazný doklad **EN** + vazba `EC_DokladyVazby` (§8) |
| **UZAVŘENO / nezrealizováno** | `Splneno` + heslo **„důvod nezrealizování"** v poznámce splněno |

Kontext dok 222: přední hrana obchodu **JE** trackovaná v Centrále (přehled 504 = přesně tahle kniha přijatých poptávek; 6607 poptávek historicky), prázdný je jen **most e-mail → strukturní `vp_poptavka`** s AI triáží. Přijatá poptávka + kalkulace je tedy vertikála, na které se ten most a nabídkový automat postaví naostro.

## 10. Zítřejší/další kroky (naostro)

1. Vzít reálnou přijatou poptávku z přehledu 504 a projít celý řetěz naostro (jako EVP260231 u RFQ).
2. **Založit kalkulaci** k poptávce (`ec_kalkulace_hlav`) + nacenit položky (RegCisHeo → `find_price` + poslední nákupka z příjemky).
3. Doostřit **gen-proceduru nabídky** (EN) + řadu nabídek + přenos BOM.
4. Doplnit přesné fieldy: „Výběr oblasti", adresář přijatých poptávek, uzavírací pole „důvod nezrealizování".

---

## Odkazy
- Sourozenec (druhá strana): [Vydané poptávky RFQ](Z_vydane_poptavky_rfq.md).
- Architektura automatu: [230 — Automaty dokladů](Z_230-automaty-dokladu.md).
- Ceny do kalkulace: [Kalkulace / ceníky Vize 1](Z_kalkulace_ceniky_vize1.md) (RegCisHeo, `find_price`, poslední nákupka).
- Funnel/kontext: [222 — Trychtýř zakázek](222-go-vp-trychtyr-zakazek.md).

*Know-how vytěženo z přehledu 504 + detailu EP26306 + procedur (Marti 19. 7. 2026). Gen-procedura nabídky a 4 přesné fieldy = doostřit naostro. — Claude C24.*
