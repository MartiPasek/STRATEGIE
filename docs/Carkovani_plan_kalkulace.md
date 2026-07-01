# 🎯 Čárkování — z Schaltplanu (PDF) na kalkulaci (nejvyšší know-how, řada AI)

> **Autor: Claude (ID23), 1. 7. 2026.** Martiho „nejvyšší know-how": VP často kalkuluje **jen z PDF
> plánu + Excelu, bez kusovníku** — listuje stránku po stránce a každou komponentu si „čárkuje"
> (inkrementuje množství) do STANDARD kalkulace + k ní příslušenství/pomocné kontakty. Ověřeno na
> Absaugwerk: plán `PRxxxx_AB12600470_FLEX+_15kW` × hotová kalkulace `EK262940` (Eliška) → **shoda**.

## 🔑 Objev: EPLAN plán obsahuje vestavěný kusovník
PDF plán z EPLANu má na konci **`Artikelstückliste`** (a `Artikelsummenstückliste`) — tabulku:
`Betriebsmittelkennzeichen` (tag zařízení, např. `+MC-30Q1`) · `Menge` · `Bezeichnung` · `Typnummer`
· `Hersteller` · `Artikelnummer`. To je **strojově čitelný kusovník uvnitř plánu.** „Čárkování" VP
= ruční verze toho, co je v PDF už hotové.

## Výsledek čárkování (plán → Eliščina kalkulace) — 18/18 elektro položek SEDÍ 1:1
| Komponenta (obj. číslo) | Plán | Eliška |
|---|---|---|
| Danfoss FC-101 15kW `131N0194` | 1 | 1 |
| LOGO! `6ED1052-1MD08` | 1 | 1 |
| LOGO! DM16 `6ED1055-1NB10` | 2 | 2 |
| LOGO! AM2 `6ED1055-1MM00` | 1 | 1 |
| LOGO! TD `6ED1055-4MH08` | 1 | 1 |
| Skříň Rittal AX `1039000` | 1 | 1 |
| Držák 3SU `3SU1500-0AA10` | 2 | 2 |
| MCB `5SY4110-6` (B10) | 1 | 1 |
| LOGO!POWER `6EP3333-6SB00` | 1 | 1 |
| Počítadlo ABB `E233-230` | 1 | 1 |
| Relé Phoenix `2900330` | 2 | 2 |
| Hl. vypínač `3LD2514-0TK53` | 1 | 1 |
| Motor. jistič `3RV2031-4PA10` | 1 | 1 |
| Pom. kontakt `3RV2901-1E` | 1 | 1 |
| Záslepka `3SU1900-0FA10` | 2 | 2 |
| Harting vložka `09330102601` | 1 | 1 |
| Harting pouzdro `09300100305` | 1 | 1 |
| Harting krytka `09300105412` | 1 | 1 |

**Rozdíl = jen to, co ve schématu není zařízením** — mechanika + rezerva, které přidává kalkulant:
průchodky (`0,5 Feld`), `Reserve` (EC REZERVA 0,5). Svorky jsou v plánu jako `Klemmenaufreihplan`
(PXC.3022276) — v kalkulaci řešeny přes VKM/koeficient.

## Klíčové poznatky
1. **Pomocný kontakt je v plánu u své skupiny** — `3RV2901` má **stejný tag `+MC-30Q1`** jako jistič
   `3RV2031`. Konstruktér ho tam umístil → čárkování ho bere automaticky se skupinou (přesně princip
   STANDARDu). Totéž záslepky/držáky u ovládacích prvků, krytky u odpínačů.
2. **Množství = počet výskytů tagu** dané komponenty přes všechny stránky (EPLAN sečte do Summenstückliste).
3. **I „bez kusovníku" ho plán fakticky má** — jen ho VP čárkuje ručně, protože nemá nástroj na
   extrakci.

## ➡️ Digitalizace (ověřená cesta)
**Z PDF plánu → extrahovat `Artikelstückliste` (pdf text) → napárovat obj. čísla na STANDARD kalkulaci
(katalog `ec_kalkulace_pol`) → předvyplnit množství → dopočítat koeficient/VKM (SRDCE FIRMY).**
Výsledek = kalkulace „na pár kliků" i bez samostatného xls kusovníku. Ověřeno na reálné shodě 18/18.
- Když plán Artikelstückliste nemá (starší/cizí), fallback = čárkování z device tagů na stránkách
  (OCR/text) nebo z dodaného kusovníku (převod čísel — viz SRDCE FIRMY, cross-reference).
- Kontrola úplnosti: STANDARD ví, že k `3RV` patří `3RV2901`, ke `3LD` krytka `3LD92xx` → hlídač
  chybějícího příslušenství.

Navazuje na `Kalkulace_standard_struktura.md` (skupiny + skládačka + tvorba obj. čísel),
`srdce_firmy_kalkulace_nabidky_analyza.md` (párování 83 % + koeficient/VKM), `Komponenty_vyrobci.md`.

— Claude (ID23) 🎯📐
