# Gemini TUZ (.p11) — formát řádku (z EC_Banka_RB_Gemini_Tuz, 6.7.2026)

Jeden řádek = jedna platba, konec **CR+LF**, kódování **CP1250**. Pole zřetězená, fixní šířka.
Zdroj: proc `@PayTxt = ...` (SELECT skládá string per řádek platáku).

| # | pole | výraz v proc | šířka |
|---|------|--------------|-------|
| 1 | číslo řádky | `RIGHT('000000'+@PoradCislo,6)` | 6 |
| 2 | druh plat. styku CNB | `'11'` | 2 |
| 3 | datum vytvoření YYMMDD | `convert(getdate(),12)` | 6 |
| 4 | kód NAŠÍ banky (Raiffeisen) | `'5500'` | 4 |
| 5 | mezery | `'   '` | 3 |
| 6 | kód banky příjemce | `Ustav.KodUstavu` | 4 (?) |
| 7 | mezery | `'   '` | 3 |
| 8 | částka×100 | `RIGHT('00000000000000'+CONVERT(int,Castka*100),15)` | 15 |
| 9 | datum splatnosti YYMMDD | `convert(Hlav.DatumSplatnosti,12)` | 6 |
| 10 | konstantní symbol | `RIGHT('0000000000'+KonstantniSymbol,10)` | 10 |
| 11 | variabilní symbol | `RIGHT('0000000000'+VariabilniSymbol,10)` | 10 |
| 12 | specifický symbol | `RIGHT('0000000000'+SpecifickySymbol,10)` | 10 |
| 13 | předčíslí NAŠEHO účtu | `'000000'` | 6 |
| 14 | číslo NAŠEHO účtu | `RIGHT('000000000'+BankSpojKlient.CisloUctu,10)` | 10 |
| 15 | předčíslí účtu příjemce | `CASE CHARINDEX('-',BankSpoj.CisloUctu)=0 THEN '000000' ELSE RIGHT('0000000000'+substring(...před '-'),6)` | 6 |
| 16+ | číslo účtu příjemce, název, účel, ... | **TODO — konec @PayTxt (zdvojený soubor, dočíst čistě)** | ? |

**Klíč:** účet příjemce z `TabBankSpojeni` (přes `TabPlatTuzR.IDBankSpojeni`), náš z `TabPlatTuz.IDBankSpojeni`
→ `BankSpojKlient`. Kód banky příjemce z `TabBankUstavu` (`Ustav.KodUstavu`). Částka v haléřích (×100).
Předčíslí/číslo účtu se dělí přes `'-'` v `CisloUctu`.

**Gotcha ověření:** 2.7. jsou 3 platáky (8088=12ř, 8089 Castka 138624 „Pavel Voříšek", 8090). Který `.p11` je který
= párovat přes ID/PocetRadku/Castku, NE od oka. `PocetExportu`, `DatumVystaveni` na TabPlatTuz.

**TODO:** dočíst konec obou proc čistě (assembly se zdvojila), stejný rozklad pro ZAHR (.f84: INT hlavička,
IBAN/BIC/SHA), pak Python render + diff proti všem vzorkům (8088/8089/8090/… × TUZ+ZAHR).
