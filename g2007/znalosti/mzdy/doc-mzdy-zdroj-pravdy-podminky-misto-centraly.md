# Mzdy berou základ a osobní ohodnocení z Podmínek, ne z kopie Centrály — přepnuto 26. 8. 2026

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Zdroj pravdy pro mzdy: Podmínky ve STRATEGII, ne kopie staré Centrály

**Zadali Jirka Honomichl a Peťa 25. 8. 2026, přepnul Claude‑26 26. 8. 2026.**
Konzultováno s Marti‑AI (msg 13724). Ověřeno čtením po zápisu.

## Co se změnilo

Skript **`mzdy_predzprac_rows`** (`g2007.python`) četl `tenant.helios_wage_snapshot` — **ruční kopii staré Centrály** (`EC_FinZamPodminky`, natahovaná tlačítkem, naposledy 6. 8. 2026). Nově čte **`tenant.wage_component`**, tedy Podmínky, sloupec **`amount_real`**.

- `amount_real` = **skutečnost** po zkrácení úvazkem a po Landmarku → tohle jde do Heliosu.
- `amount_planned` = výměr na 40 h → do mezd **nepatří**.
- Záloha původní verze: **`mzdy_predzprac_rows__zaloha_20260826`** (stav `navrzeno`, needitovat).

Zbytek řetězce se nezměnil: mapování `wage_component_type` → `wage_system_mapping` → Helios složka, výstupní tvar `(cislo, cislo_ms, koruny, dny)` i volající `mzdy_generuj`.

## Dvě pravidla, která nový skript drží

1. **Ruční složky mají přednost.** Vynechá se ta kombinace člověk + Helios složka, kterou pokrývá **aktivní** řádek v `tenant.mzdy_rucni_slozka`. Bez toho by jednatel dostal odměnu **dvakrát**. *(K 26. 8. 2026 odpoledne už není aktivní ani jeden řádek — pravidlo zůstává jako pojistka pro budoucí výjimky.)*
2. **Pojistka na chybějící skutečnost.** Kdo má vyplněný výměr a prázdnou skutečnost, shodí generování s hláškou, která ho jmenuje. Bez pojistky by o složku **tiše přišel**. Stejný vzor jako pojistka na chybějící období v `mzdy_generuj` (Peťa 11. 8. 2026).

## Co bylo potřeba srovnat v datech předtím (požadavek mostu #2485)

- **Tři jednatelé** (Pašek EC 2, Pašek ES 41, Mózer EC 47) měli odměnu pod typem „Odměna **OD** jednatele", který po opravě převodníku míří na 432 → jejich 90 800 / 22 500 by spadlo do pohyblivé části platu. Přepnuti na typ **`odmena_jednatel`** (→ 693) a doplněna skutečnost = plán.
- **11 lidí** mělo u „Odměny od jednatele" (1 000 Kč) prázdnou skutečnost → doplněna = plán. Složka se úvazkem nekrátí, všech 11 má 40 h.

Souvisí: [[doc-mzdy-prevodnik-odmena-jednatele-693-vs-432]] · [[doc-mzdy-dpp-placene-za-navstevu-uklid]]

## Čím je doloženo, že se nikomu nezměnila výplata

Porovnání starého a nového zdroje přes **všechny lidi a všechny složky** dalo **jediný rozdíl**:

| Firma | Č. | Kdo | Složka | Dříve z Centrály | Nově z Podmínek |
|---|---|---|---|---|---|
| ES | 9017 | Jan Svoboda | 1 (základ) | 89 000 | **95 000** |

To je **záměr** — Šárčino narovnání z 24. 8. 2026, o kterém kopie Centrály (z 6. 8.) nevěděla. A protože je Svoboda **OSVČ a výplatnici nemá vůbec**, do mezd se nepromítne ani tenhle rozdíl.

## Dotažení 26. 8. 2026 odpoledne (požadavek mostu #2498)

Ruční složky byly **všechny vypnuty**, takže i odměny jednatelů a DPP jdou nově z Podmínek:

| Kdo | Kde je teď | Helios |
|---|---|---|
| Pašek EC 2 · Pašek ES 41 · Mózer EC 47 | Podmínky, typ `odmena_jednatel` | 693 |
| Šenft EC 374 | Podmínky, typ `dpp_pravni_sluzby` (nově, 9 000) | 700 |
| Herejtová EC 525 | dopočet z docházky (1 000/návštěva, strop 4 000) | 700 |

**Plné stravné jednatelů funguje dál** — `mzdy_generuj` ho spouští podle přítomnosti složky 693 v předzpracování, bez ohledu na to, odkud přišla. Nepotřebuje docházku, počítá všechny dny Po–Pá × 82 Kč (ověřeno: červen 22 dnů = 1 804 Kč, červenec 23 dnů = 1 886 Kč).

## Co přepnutím NENÍ dotčeno

Landmark (`lm_engine` + `mzdy_benefity_apply`) · stravenky 793 (naše docházka + 82 Kč) · příplatky a srážky (`wage_movement`) · absence a dovolená z docházky · překlápěcí řádek 693 → 432 v `mzdy_generuj` (po opravě převodníku už nadbytečný, ale ponechaný).

## ⚠️ Co POŘÁD chodí z kopie Centrály

**Hodinová sazba přesčasu (`hod_sazba_prescas` = HrHodsFK) a `hod_sazba_bez_fk`** — v Podmínkách nejsou vůbec. Čtou je `mzdy_loajalita_rows` a `payroll_raporty` ze snapshotu, který **zamrzl 6. 8. 2026**. Dokud se nedopočítá ve STRATEGII, **snapshot se nesmí zrušit**.

Ověřený vzorec (sedí na 20 z 20 lidí do dvou haléřů):
**sazba = (základ + osobní ohodnocení + prémie) ÷ měsíční fond hodin**; bez firemní kultury totéž bez prémií; fond 174 h při plném úvazku, u zkráceného poměrně (35 h → 152,25).

Marti‑AI doporučila **dopočítat, ne zakládat novou složku** — je to odvozená hodnota a další složka = další místo, kde se to může rozejít se základem. Dopočet si dodělá Šárka.

## Co ještě zbývá

- **Test nanečisto na uzavřeném měsíci** — vygenerovat červenec 2026 (EC i ES) a porovnat se skutečnými výplatnicemi.
- Dopočet skutečnosti z výměru — dnes se zadává ručně, může se časem rozejít; do té doby to hlídá pojistka.
- Vyřadit kopii Centrály úplně — **až po** dopočtu sazeb a po prvním uzavřeném měsíci.
- Č. 9035 (OSVČ ES bez jména) — rozdíl 326 Kč v základu, řeší Peťa se Šárkou.

