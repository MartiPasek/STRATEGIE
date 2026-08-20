# Podklad fakturace OSVC: co jeste chybi do plne parity s Centralou (stav 19.8.2026)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Podklad fakturace OSVC — co jeste chybi (19. 8. 2026)

Claude-24 (Kristy). Vychazi z kompletniho precteni procedur Centraly
`EC_Zakazky_GenPodkladFakturace_Priprava` (561 radku) a `EC_Zakazky_GenPodkladFakturace` (437 radku).
Navazuje na `doc-mzdy-podklad-osvc-faze1-stav` a `doc-mzdy-podklad-osvc-pausaliste`.

## A. Vypocet — rozdily proti Centrale

**1. Premie a srazky za zakazku (`fix_premie`) — CHYBI ÚPLNĚ.**
Centrala u zakazky, ktera uz ma radek v `EC_ZakazkyFinanceZam` (temp `#TmpUzavrene`, typ 1),
NEPOCITA hodiny znovu — bere hotovou castku `Vyplatit`, a ta = hodiny x sazba + `FixPremie`.
Overeno na datech (Vasyl 464, VR10605: 190,94 h x 350 + 3 000 = 69 829 = `vyplatit`;
VR10503: 37,21 x 350 - 250 = 12 773). Nas vypocet (i stary interim v8) premie ignoruje —
sloupec "Premie" v PDF je vzdy "0". Objem k 19.8.2026 u 7 hodinaru: **26 380 Kc** na zakazkach
s nefakturovanymi hodinami, z toho **1 270 Kc** na radcich, ktere se prave ted tisknou
(327 = 325, 372 = 820, 425 = 125). Reseni: kdyz zakazka ma radek v `ec.zakazky_finance_zam`
(bez `id_pol_vobj`/`id_pol_pf`), pouzit `vyplatit` misto vlastniho prepoctu hodin.

**2. Tri stavy zakazky misto jednoho — CHYBI.**
Centrala deli zakazky do tri skupin a lisi se i tim, jestli je vysledek ZALOHA nebo doplatek:
- `#TmpUzavrene` (typ 1) — ma radek v `EC_ZakazkyFinanceZam` -> castka = `Vyplatit`.
- `#TmpOtevrene` (typ 2) — NEMA radek ve financich, `_Uzavreno=0` a `_VyhodnoceniUzavreno=0`
  -> pocita se z dochazky (`SUM(KC_Celkem)`, hodiny `CasCelkemInterni`), a v hlavni procedure
  dostane **`JsemZaloha = 1`** (`CASE WHEN max(TYP)=2 THEN 1 ELSE 0 END`).
- `#TmpMeziStav` (typ 4) — totez, ale `_VyhodnoceniUzavreno=1` -> uz to NENI zaloha (doplatek).
Vsechny tri maji podminku `not exists (radek v EC_ZakazkyFinanceZam)` u typu 2 a 4, aby se
hodiny nezapocitaly dvakrat. Nas vypocet ma jen jednu vetev (hodiny z `vyroba_work`) a stav
zakazky neresi vubec. **Data uz ve STRATEGII jsou**: `ec.tab_zakazka_ext.uzavreno` a
`.vyhodnoceniuzavreno` (zrcadlo TabZakazka_EXT), pripadne `tenant.zakazka_meta`.

**3. "Uz objednano" se pocita jinak.**
Centrala: `SUM(TabPohybyZbozi.CCSDPHKC)` pres `EC_Zakazky_PlatbyZam.IDPolVobj` (resp. `IDPolPF`
pro fakturovano), a navic umi **sloucene zakazky** pres `TabZakazka_EXT._IDSkupiny` (zalohy
ve slouceni se scitaji za celou skupinu). My: `SUM(vyplaceno)` ze zrcadla `osvc_zaloha_zakazek`,
skupiny neresime. U hodinaru to zatim sedelo, ale je to prvni misto, kde hledat rozdil v korunach.

**4. Odmeny — mame prisnejsi filtr nez Centrala.**
Centrala bere `IDPolVObj IS NULL AND DatVyplaceni IS NULL` (podminka na `IDPolPF` je v kodu
zakomentovana, `Schvaleno` se neresi vubec). My filtrujeme navic `schvaleno` a `id_pol_pf IS NULL`.
Rozhodnout, co je spravne — a sjednotit.

**5. Zadrzne / koeficient** — v Centrale existuje (`@Koeficient`, `@ZadrzneDef`), ale je VYPNUTE
(Swobi 26.3.2025 na zadost Peti a Martina: koeficient 1, zadrzne 0). U `PR%` zakazek bylo
vzdy 1. Neimplementovat, jen o tom vedet.

## B. Zapis zpet (Faze 2) — cely chybi

Dnes umime jen SPOCITAT a vytisknout. Centrala navic pri generovani podkladu:
- zalozi polozku objednavky (VOBJ) a jeji ID zapise do `EC_Zakazky_PlatbyZam.IDPolVobj`,
- vlozi radek do `EC_Zakazky_PlatbyZam` (`Vyplaceno`, `Zaloha`, `JsemZaloha`, `HodSazba`,
  `PocetHodin`) — to je to, co pak nas vypocet odecita jako "uz objednano",
- u rezie a odmen orazitkuje primo radky dochazky (`SET D.IDPolVObj = @Ident`) — nas ekvivalent
  je razitko `fakturace_obj_id` na `vyroba_work` / `att_entry`.
Bez tohohle kroku by nas podklad nabizel tytez hodiny znovu a znovu.

## C. Data a provoz

- **Razitka z Faze 0 nejsou uplna** — nefakturovana rezie z minulych mesicu: 327 = 24,93 h,
  425 = 21,63 h, 346 = 3,40 h, 370 = 2,18 h, 464 = 0,51 h. Pred ostrym prepnutim overit,
  jestli uz nebyla proplacena jinak (jinak by se fakturovala podruhe).
- **Jen 8 z 24 dilenskych OSVC** ma aktivni kartu s `user_id` — pro ostatnich 16 (v `att_employee`
  neaktivni, vedeni jako HPP) podklad vygenerovat nejde.
- **Lev 371, 23.-24. 7. 2026** (16 h / 5 600 Kc) — otevrene, viz `doc-mzdy-podklad-osvc-faze1-stav`.

