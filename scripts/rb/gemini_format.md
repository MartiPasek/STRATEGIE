# RB Gemini platák — kompletní formát (převzato 1:1 z DB_EC, 6.7.2026)

Zdroj: `EC_Banka_RB_Gemini_Tuz` (CZK `.p11`) + `EC_Banka_RB_Gemini_Zahr` (EUR `.f84`).
Čisté procedury: `uploads/*RB Tuz.sql`, `*RB Zah.sql`. Jeden řádek/blok = jedna platba.
**Kódování CP1250, konec řádku CR+LF.** `@PoradCislo` = pořadí řádku (dispečer loopuje).

---
## TUZ `.p11` — `@PayTxt` (per řádek `TabPlatTuzR Pol`), fixní šířka
| # | pole | výraz | šíře |
|---|------|-------|------|
| 1 | číslo řádky | `RIGHT('000000'+@PoradCislo,6)` | 6 |
| 2 | druh plat. styku CNB | `'11'` | 2 |
| 3 | datum vytvoření | `convert(getdate(),12)` = **YYMMDD** | 6 |
| 4 | kód naší banky | `'5500'` (Raiffeisen) | 4 |
| 5 | mezery | `'   '` | 3 |
| 6 | kód banky příjemce | `Ustav.KodUstavu` (TabPenezniUstavy) | 4 |
| 7 | mezery | `'   '` | 3 |
| 8 | částka | `RIGHT('00000000000000'+CONVERT(int,Castka*100),15)` = **haléře, BEZ tečky** | 15 |
| 9 | datum splatnosti | `convert(Hlav.DatumSplatnosti,12)` YYMMDD | 6 |
| 10 | KS | `RIGHT('0000000000'+KonstantniSymbol,10)` | 10 |
| 11 | VS | `RIGHT('0000000000'+VariabilniSymbol,10)` | 10 |
| 12 | SS | `RIGHT('0000000000'+SpecifickySymbol,10)` | 10 |
| 13 | předčíslí NAŠEHO účtu | `'000000'` | 6 |
| 14 | číslo NAŠEHO účtu | `RIGHT('000000000'+BankSpojKlient.CisloUctu,10)` | 10 |
| 15 | předčíslí účtu příjemce | `CASE CHARINDEX('-',BankSpoj.CisloUctu)=0 → '000000' ELSE RIGHT('0000000000'+substr(před '-'),6)` | 6 |
| 16 | číslo účtu příjemce | `CASE '-'=0 → RIGHT('0000000000'+CisloUctu,10) ELSE RIGHT('0000000000'+substr(po '-'),10)` | 10 |
| 17 | avizo kreditní | `LEFT(UcelPlatby+spaces,140)` (doplněno mezerami vpravo) | 140 |
| 18 | název účtu plátce | 20 mezer | 20 |
| 19 | název účtu příjemce | 20 mezer | 20 |
| 20 | VS debetní | `RIGHT('000000000000'+VariabilniSymbol,10)` | 10 |
| 21 | SS debetní | `'0000000000'` | 10 |
| 22 | avizo debetní | `LEFT(UcelPlatby,140)` **BEZ paddingu** (jen text) | ≤140 |

**FROM** `TabPlatTuzR Pol` ⟕ `TabPlatTuz Hlav`(Pol.IDHlavaPP) ⟕ `TabPenezniUstavy Ustav`(Pol.IDBankUstavu)
⟕ `TabBankSpojeni BankSpoj`(Pol.IDBankSpojeni=příjemce) ⟕ `TabBankSpojeni BankSpojKlient`(Hlav.IDBankSpojeni=náš).
**WHERE** `Hlav.RealizaceExport=0 AND Hlav.DatumVystaveni>getdate()-8 AND Pol.ID=@ID`.

---
## ZAHR `.f84` — `@PayTxt` (per platba `TabPlatZahr Hlav`)
| # | pole | výraz | šíře |
|---|------|-------|------|
| 1 | druh | `'INT'` | 3 |
| 2 | číslo řádky | `RIGHT('000000'+@PoradCislo,6)` | 6 |
| 3 | datum vytvoření | `convert(getdate(),112)` = **YYYYMMDD** | 8 |
| 4 | název banky příjemce | `LEFT(UstavPrij.NazevUstavu+sp,35)` | 35 |
| 5 | ulice banky příjemce | `LEFT(UstavPrij.Ulice+sp,35)` | 35 |
| 6 | město banky příjemce | `LEFT(UstavPrij.Misto+sp,35)` | 35 |
| 7 | stát banky příjemce | `LEFT(ZemeUstavPrij.Nazev+sp,35)` | 35 |
| 8 | název příjemce | `LEFT(OrgPrij.Firma+sp,35)` | 35 |
| 9 | ulice příjemce | `LEFT(OrgPrij.UliceSCisly+sp,35)` | 35 |
| 10 | město příjemce | `LEFT(OrgPrij.Misto+sp,35)` | 35 |
| 11 | stát příjemce | `LEFT(ZemeOrgPrij.Nazev+sp,35)` | 35 |
| 12 | částka | `RIGHT('00000000000000'+CONVERT(numeric(19,2),Castka),16)` = **S DESETINNOU TEČKOU** (např. `0000000003506.94`) | 16 |
| 13 | měna platby | `Hlav.Mena` (ISO) | 3 |
| 14 | číslo NAŠEHO účtu | `RIGHT('000000000'+BankSpPlatce.CisloUctu,10)` | 10 |
| 15 | IBAN příjemce | `LEFT(BankSpPrij.IBANElektronicky+sp,34)` | 34 |
| 16 | poplatky | `LEFT(Hlav.Poplatky+'   ',3)` (BEN/OUR/SHA) | 3 |
| 17 | platební titul | `RIGHT('000'+PlatebniTitul,3)` (nepoužívá se) | 3 |
| 18 | ISO země příjemce | `LEFT(BankSpPrij.CilovaZeme+'  ',2)` | 2 |
| 19 | ID hlavičky | `'ID:'+RIGHT('00000'+Hlav.ID,6)+':'` (např `ID:003435:`) | 10 |
| 20-22 | popis platby 1-3 | `LEFT(PopisPlatby{1,2,3}+sp,35)` | 35×3 |
| 23 | popis platby 4 | `LEFT(PopisPlatby4+sp,25)` (zkráceno o 10 kvůli ID) | 25 |
| 24 | název účtu příkazce | 20 mezer | 20 |
| 25 | priorita | `CASE Priorita=0 → '01' ELSE '02'` | 2 |
| 26 | ISO měna účtu klienta | `LEFT(BankSpPlatce.Mena+'   ',3)` | 3 |
| 27 | VS klienta | `RIGHT('0000000000'+Hlav.ID,10)` | 10 |
| 28 | formát čísla účtu | `'02'` (IBAN) | 2 |
| 29 | účtování platby | `'02'` (Europlatba) | 2 |
| 30 | rezerva | 123 mezer | 123 |
| 31 | SWIFT příjemce | `LEFT(UstavPrij.SWIFTUstavu+sp,11)` | 11 |
| 32 | předčíslí účtu klienta | `'000000'` | 6 |
| 33 | datum splatnosti | `convert(Hlav.DatumSplatnosti,12)` YYMMDD | 6 |

**FROM** `TabPlatZahr Hlav` ⟕ `TabPenezniUstavy Ustav`(IDBankUstavuPlatce) ⟕ `TabBankSpojeni BankSpPlatce`(IDBankSpojeniPlatce=náš)
⟕ `TabPenezniUstavy UstavPrij`(IDBankUstavuPrijemce) ⟕ `TabZeme ZemeUstavPrij`(substr(SWIFT,5,2)=ISOKod)
⟕ `TabBankSpojeni BankSpPrij`(IDBankSpojeniPrijemce) ⟕ `TabCisOrg OrgPrij`(BankSpPrij.IDOrg) ⟕ `TabZeme ZemeOrgPrij`(BankSpPrij.CilovaЗ=ISOKod).
**WHERE** `Hlav.RealizaceExport=0 AND Hlav.DatumVystaveni>getdate()-8 AND Hlav.ID=@ID`.

**Pozn.:** EUR platby = **`TabPlatZahr`** (samostatná tabulka, ne TabPlatTuz). Částka na hlavičce (1 platba = 1 řádek).

---
## Gotchy pro replikaci
- **Datum „vytvoření" = den generování** → při diffu injektovat datum ze jména souboru (jinak nesedne).
- **TUZ částka = int haléře** (×100, bez tečky, 15); **ZAHR částka = numeric(19,2) S tečkou** (16).
- **Účet = `předčíslí-číslo`** (CisloUctu s `-`); bez `-` → předčíslí 000000.
- **CP1250 + CRLF**; text pole doplněná mezerami VPRAVO (LEFT+spaces), čísla/symboly nulami VLEVO (RIGHT).
- **Párování souboru↔platák přes ID** (2.7. jsou 3: 8088=12ř, 8089, 8090) — NE od oka.
- Filtr proc: `RealizaceExport=0`, `DatumVystaveni>getdate()-8`.
