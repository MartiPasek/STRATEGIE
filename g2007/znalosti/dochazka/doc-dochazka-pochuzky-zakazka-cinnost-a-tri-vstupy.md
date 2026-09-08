# Pochůzky a služební cesty: zakázka + činnost (9/113), tři vstupy v appce a proč trip nezakládal rozpad

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Pochůzky a služební cesty — zakázka a činnost (zadala Kristý 8. 9. 2026)

## Odkud to vzešlo
Peťa 2.–7. 9. 2026 nahlásila úseky **bez zakázky a bez rozpadu**. Ukázalo se, že to není
jeden problém, ale jeden **kořen** se třemi projevy.

**Kořen (opraveno 8. 9. 2026):** v `att_checkin` stálo
`if kind in ("work", "overhead"):` — a jen uvnitř téhle větve se volá `_wa_open`
(založení položky rozpadu) a `att_apply_work_selection` (promítnutí zakázky do hlavičky).
Cesty `trip` (služební cesta) a `homeoffice` do ní **nikdy nevstoupily**, takže píchnutí
vzniklo jako obyčejná práce bez zakázky, bez činnosti a bez rozpadu.

Doklady: **Saad Jarrar 2. 9.** úsek 08.15–08.41 (0,43 h), ručně opravila Petra Šafránková
(#10017018 → Rezie). **Šárka Novotná 7. 9.** úsek 09:12–12:35 (3,38 h) přes home office.

**Oprava:** `att_checkin` **v13** — větev je nově `if kind in ("work", "overhead", "trip")`.
Trip si tak bere zakázku i činnost z předvolby (`_wp_get`) stejně jako běžný příchod.

## ⛔ Dvě věci, které jsou ZÁMĚR, ne chyba
1. **Home office zůstává typem `work`.** Kristý 8. 9.: *„je to tak kvůli mzdám, ve mzdách
   nerozlišujeme, jestli člověk dělá z domova nebo z firmy."* Typ `homeoffice` v číselníku
   existuje, ale tahle cesta ho vědomě nepoužívá. **Neopravovat.** Ze stejného důvodu
   zůstává `work` i u tripu.
2. **Ohlášení nezakládá docházku.** Peťa 19.–26. 8. 2026 to utáhla u nemoci, OČR a lékaře
   (*„JEN INFORMACE VEDOUCÍMU, NIKAM SE NEZAPISUJÍ"*). `status='announced'` znamená
   nejméně na šesti místech „nepočítat" (`NOT IN ('superseded','announced')`).
   **Tenhle status nepředefinovávat.** Kdo chce, aby pochůzka počítala hodiny,
   musí přidat PÍCHNUTÍ vedle ohlášení, ne měnit význam ohlášení.

## Tři různé „pochůzky" v appce (nepleť si je)
Všechny tři jsou v `60_dochazka.js`:

| vstup | kde | co dělá dnes |
|---|---|---|
| **🚙 Jedu rovnou k zákazníkovi…** | 💼 Služební důvody | `checkin {kind:"trip"}` — **jediná zakládá hodiny** |
| **📦 Služební pochůzka, pak dorazím…** | 💼 Služební důvody | jen `announce` — hodiny NEBĚŽÍ (`hours` NULL) |
| **🚗 Mám služební pochůzku…** | 🙈 Teď to bude jinak | časované ohlášení za chodu, hodiny běží dál na stávající zakázce |

Saad 2. 9. ťukl první dvě v jedné minutě — proto měl ohlášení i 26minutový úsek.

## Zadání Kristý + Peťa (8. 9. 2026)
Do **všech tří** vstupů přijde výběr **činnosti (jen 9 nebo 113) + výběr zakázky**.
U „📦 pak dorazím" to znamená **píchnout A poslat ohlášení** — dvě jasné akce za sebou,
ne magie uvnitř ohlášení.

## ⚠️ Klíčové zjištění: `kind` je JEN seskupení roletky
Roletka `prace_cin` vybírá seznam podle zakázky:
`rez = is_rezie || kind==="overhead" || project_type==="REZIE" || _isRezieRef(project_ref)`
→ načte se buď `rezie`, nebo `standard`, přepínač tam není.

**Ale zápis `kind` NEKONTROLUJE.** `att_wa_open` zapíše `cinnost_id`, jak přijde;
`att_apply_work_selection` se řídí `project_ref` + `is_rezie`, ne činností (pojistka #3:
*„změna samotné činnosti nedělí, činnost si drží rozpad"*). Proto je kombinace
**reálná zakázka + činnost 113 (rezie)** uložitelná a konzistentní.

**⛔ 113 NEPŘEVÁDĚT na `standard`.** Od června: 34 úseků, **33 na Režii**, 12 lidí, 57,3 h.
Přehozením by zmizela z režijního seznamu dvanácti lidem. Obrazovka pochůzky bude
**vědomá výjimka**, která nabídne obě bez ohledu na `kind`.

## Číselník činností (stav 8. 9. 2026)
| id | č. | název | druh | pořadí |
|---|---|---|---|---|
| 16 | **9** | Služební cesta / montáž | standard | 160 |
| 53 | **14** | Služeb.cesta/montáž - čas na cestě | standard | 310 |
| 37 | **113** | Pracovní cesta – nákup / lakovna / ostatní - bez cesťáku | **rezie** | 210 |

Rozhodnutí Kristý: **9 = 🧾 nutný cesťák**, **113 = bez cesťáku**, **14 vyřadit z výběru**.
Devítka od 1. 6. 2026 nebyla použita ani jednou, 113 jede dál — podezření, že lidé neví,
kdy má být co. Výběr při píchnutí to má vyřešit u zdroje.

**Kde se to edituje:** appka → **Moje činnosti** → dole **🛠 Master číselník (správa)**
→ dvě záložky **🧾 Běžné zakázky** / **🧰 Režie**. Seznam nefiltruje `active`, jen `kind`
(`app_vyroba_cinnost_master`), právo `_hr_can_manage` (rodič nebo skupina HR).
⚠️ **Past:** 9 i 14 jsou `standard`, 113 je `rezie` — kdo hledá na jedné záložce, druhé dvě
nevidí a myslí si, že v číselníku nejsou. Stalo se 8. 9. 2026.

## Co ZBÝVÁ (backend je hotový, další serverová změna není potřeba)
Endpointy, které UI potřebuje, existují: `/app/work/set-zakazka`, `/set-rezie`,
`/set-cinnost`, `/state`.

1. **Sdílená obrazovka výběru** v `60_dochazka.js` — dlaždice 9/113 + picker zakázky;
   zavolá `set-cinnost` + `set-zakazka`/`set-rezie`, teprve pak píchne.
2. **Napojení tří vstupů:** 🚙 → výběr + `checkin {kind:"trip"}` · 📦 → výběr +
   `checkin {kind:"trip"}` **+** `announce` · 🚗 → výběr + `checkin {kind:"trip", switch:true}`
   + `announce`.
3. **`prace_cin`** — nabídnout obě činnosti, když je aktuální 9 nebo 113; jinak 113
   u reálné zakázky ze seznamu zmizí (ukáže se nahoře jako aktuální, ale nejde znovu vybrat).
4. **Číselník** — 9 přejmenovat, **14 vypnout** (k 8. 9. je pořád `active=true`).
5. **Ověřit naostro** jedním reálným píchnutím pochůzky.

## Souvisí
`doc-dochazka-sluzebni-cesta-informace-do-fronty` (činnost 9 do fronty K vyřešení; pozor:
interní `id` devítky je **16**, pod `id=9` sedí Značení vodičů) ·
`doc-dochazka-kaskada-doplni-cinnost-z-predchoziho-useku`

