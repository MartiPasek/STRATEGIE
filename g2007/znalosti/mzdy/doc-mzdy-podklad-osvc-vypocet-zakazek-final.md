# Podklad fakturace OSVC: finalni logika zakazkove casti (19.8.2026) + dva platebni kanaly

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Zakazkova cast podkladu OSVC — finalni logika (19. 8. 2026)

Claude-24 (Kristy). Doplnuje `doc-mzdy-podklad-osvc-faze1-stav`, `-pausaliste`, `-dph-a-parovani-zaloh`.
Kandidat = `g2007.python` **`podklad_vyplaceni_pdf_faze1`** (md5 dffef32756adc269e83d6619d2224182).

## DVA PLATEBNI KANALY (klicove, driv jsme znali jen jeden)

1. **`EC_Zakazky_PlatbyZam`** — objednavky (VOBJ). Zrcadlime v `tenant.osvc_zaloha_zakazek`.
2. **`EC_ZamestPlatby`** — prime platby, plni je `EC_ZamPlatba_VlozVetu`. **NENI prazdna**:
   20 162 radku / 247 mil. Kc celkem. Z ni se aktualizuje `EC_ZakazkyFinanceZam.Vyplaceno`,
   a tim padem `ZbyvaVyplatit` = `Vyplatit - Vyplaceno`.

Stav k 19.8.2026 (narok / uz vyplaceno prime / zbyva):
327 = 6 260 826 / 2 835 861 / 3 424 965 · 346 = 8 918 477 / 5 222 596 / 3 695 881 ·
370 = 6 993 395 / 2 909 891 / 4 083 504 · 371 = 5 989 465 / 2 473 167 / 3 516 298 ·
**372 Erhard = 2 751 669 / 0 / 2 751 669** (jediny bez prime platby — proto na nem vsechno
"nesedelo" a proto u nej drzi jen odecet s DPH) · 425 = 1 539 874 / 48 548 / 1 491 326 ·
464 = 2 844 201 / 980 455 / 1 863 746.

Overeno: u zakazek, ktere jsou KANDIDATY (bez IDPolVobj/IDPolPF, `ZbyvaVyplatit` > 1),
je pocet radku s primou platbou **nula** u vsech 7 hodinaru → `Vyplatit` = `ZbyvaVyplatit`.
Zadny limit ani strop navic proto NENI potreba (navrh stropu ze 19.8. byl zamitnut —
Kristy: *"a je tam ten strop nutny proc? V Centrale nebyl"*, a mereni ji dalo za pravdu).

## Finalni pravidla zakazkove casti (hodinar)

| stav zakazky | podminka | castka |
|---|---|---|
| uzavrena (typ 1) | ma radek v `ec.zakazky_finance_zam`, bez `id_pol_vobj`/`id_pol_pf`, `zbyva_vyplatit` > 1 | `vyplatit` (= hodiny x sazba + `fix_premie`) − objednano |
| otevrena (typ 2) | NEMA zadny radek ve financich, `oz_zakazky._Uzavreno`=0 a `_VyhodnoceniUzavreno`=0 | hodiny x sazba − objednano; je to ZALOHA |
| mezistav (typ 4) | NEMA radek ve financich, `_VyhodnoceniUzavreno`=1 | hodiny x sazba − objednano; uz to NENI zaloha |
| uzavrena bez financi | `_Uzavreno`=1 a zadny radek ve financich | **nefakturuje se** (vypise se do `preskocene`) |

Radek se tiskne jen kdyz vysledek > 1 Kc. Objednano = `COALESCE(obj_bez_dph, vyplaceno)`
ze zrcadla zaloh, parovane **pres skupinu slouceni** (`oz_zakazky._IDSkupiny`), jinak na cislo zakazky.

## CHYBA, KTEROU JE SNADNE UDELAT ZNOVU

`fin_map` (kandidati typ 1) ma filtr `zbyva_vyplatit > 1`. Zakazka, ktera radek ve financich
MA, ale je uz vyporadana (`zbyva_vyplatit` <= 1), pak z `fin_map` vypadne a **propadne do
hodinove vetve — proplati se podruhe**. Centrala proti tomu ma u otevrenych
`not exists (SELECT id FROM EC_ZakazkyFinanceZam WHERE CisloZakazky = D.CisloZakazky AND CisloZam = ...)`.
V kandidatu resi samostatny set `ma_fin` (vsechny zakazky s JAKYMKOLI radkem ve financich).
Bez nej vychazelo Noskovi (425) **54 radku / 133 109 Kc misto 5 radku / 2 984 Kc**.

Kontrola: tataz logika napsana v SQL da Noskovi presne 5 radku a 2 984 Kc — shoda s Centralou
na korunu (VR10561 1 497, VR10682 1 320, VR10653 127, VR10519 35, VR10672 5).

## Vysledky kandidata (19. 8. 2026, vsech 8 aktivnich OSVC)

| c. | jmeno | interim v8 (ostry) | kandidat |
|---|---|---|---|
| 105 | Havlat (pausalista) | 2 991 452 | **0** |
| 327 | Vorisek | 118 863 | 128 945 (15 r.) |
| 346 | Kilberger | 101 437 | 102 557 (5 r.) |
| 370 | Honal | 100 219 | 101 624 (7 r.) |
| 371 | Lev | 83 800 | 80 184 (2 r.) |
| 372 | Erhard | 196 503 | 159 127 (42 r.) |
| 425 | Nosek | 66 684 | 63 689 (31 r.) |
| 464 | Vasyl | 23 520 | 25 656 (3 r.) |

Zakazkova cast typu 1 sedi s Centralou presne (overeno SQL replikou). Otevrena cast se z
principu lisit muze — Centrala ji pocita z `EC_Dochazka`, my z `tenant.vyroba_work`.

## Jediny zamerny rozdil proti Centrale

Objednano odecitame **bez DPH** (`CCBezDaniKc`), Centrala s DPH (`CCSDPHKC`) —
rozhodla Kristy 19.8.2026. Projevi se jen u platcu DPH: 327 Vorisek a 372 Erhard.

