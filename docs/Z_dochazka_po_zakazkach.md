# Docházka po zakázkách — přehled v ERP + zarovnání činností na Centrálu

> Peťa + Claude‑26, 22. 7. 2026. Zrcadlo Delphi přehledu **109** („Docházka") do
> STRATEGIE ERP, postavené nad NAŠIMI daty (PG), a jednorázové **zarovnání číselníku
> činností na Centrálu** (přehledy 1046 režie / 1047 dílna). Konzultováno s Marti.

## Co to je a kde ve stromu
- Složka **🕒 Docházka** v kořeni stromu (uzel 188), viditelnost `restricted` pro 11 lidí
  (HR skupina + Dušan Havlát + Michelle Šafránková). Pod ní:
  - **🛠 Opravy docházky** (uzel 183, jádro `dochazka.opravy`) — přesunuto z HR & LIDÉ.
  - **🏭 Docházka po zakázkách** (uzel 189, jádro `dochazka.centrala`,
    data_source/data_set `dochazka.zakazky_vse_list`) — hlavní přehled, jen do dneška.
  - **⏭ Naplánovaná budoucnost** (uzel 190, jádro `dochazka.zakazky_budoucnost`,
    data_set `dochazka.zakazky_budoucnost_list`) — stejné sloupce, datum > dnes, vzestupně.

## Zdroj dat (NENÍ živě z Centrály — vše je v PG)
Přehled je běžný framework grid (ne vlastní stránka — první pokus `/dochazka-centrala`
+ `modules/erp/api/dochazka_zakazky.py` byl SMAZÁN). Data_set spojuje `UNION ALL`:
1. **tenant.vyroba_work** — segmenty práce na zakázce + skutečná činnost, od–do
   (`source_system IN ('app','centrala1')`). To je správný „po‑zakázkách" model
   (1:1 s EC_Dochazka), NE `att_entry` (ta je jen docházka/přítomnost). Centrála se
   do `vyroba_work` průběžně importuje (`_sync_vyroba_work_ec`), takže „tablet/ručně/
   z Centrály" i „aplikace" jsou v jedné tabulce.
2. **tenant.att_entry** kde `att_entry_type.category='absence'` — dovolená/nemoc/lékař…
   BEZ přestávek (`category='break'` vynecháno), bez `plan_ec`, bez `superseded`.
   Absencím se v přehledu doplňuje **zakázka `Rezie`** (jako v Centrále) a centrálské
   číslo činnosti dle typu (Dovolená 20, Lékař 21, Nemoc 22, OČR 23, Sickday 31,
   Nepřítomnost OSVČ 37, Neplacené volno 39).

## Sloupce (dle Centrály 109, vědomé odchylky)
`PraceAktivni` (první, ✓ = úsek nemá konec = člověk je zrovna píchnutý), CisloZakazky,
JmenoPrijmeni, CisloZam, **DruhCinnosti = centrálské číslo (ec_cislo)**, CinnostText,
DenVTydnu, CasZacatek, CasKonec, CasCelkem, Odkud (aplikace/z Centrály/ČSSZ), Smlouva
(HPP/OSVC/DPP z `engagement`), Poznamka, DatumPripadu, Rok, Mesic.
**Vynecháno na pokyn Peti:** interní ID, `CasBlbost`, `CasRezie` a trvale prázdné
sloupce Centrály (schválení, pauza, poznámka vedoucího).

## ⭐ Zarovnání číselníku činností na Centrálu (jádro téhle znalosti)
**Problém:** import z Centrály ukládal `vyroba_work.cinnost_id = EC_Dochazka.DruhCinnosti`
(natvrdo `WHERE id=:cin`). Náš `tenant.vyroba_cinnost` ale s Centrálou zarovnaný NENÍ —
sedí jen čísla **1–5** (Přípravné, Mechanické, Zámečnické, Drátování, Zkoušení), od 6 výš
se rozcházejí (u nás 11=Gravírování, v Centrále 11=Kabely). → importované řádky s číslem
≥6 ukazovaly ŠPATNOU činnost (~1 641 řádků).

**Řešení (Marti: „udělejte si záložní sloupec, jak jsme to ve STRATEGII měli"):**
NErenumerovávat PK (5 návazných tabulek + mobil na `id` stojí), místo toho PŘIDAT sloupce:
- `tenant.vyroba_cinnost.strategie_cislo` = **záloha** našeho původního čísla (= `id`).
- `tenant.vyroba_cinnost.ec_cislo` = **centrálské** číslo (1046/1047), napárováno dle názvu.
- `tenant.vyroba_work.cinnost_id_orig` = **záloha** původního `cinnost_id` před přepočtem.

**Kroky (vše přes bridge write + schválení Peti):**
1. Přidat sloupce, zálohovat `strategie_cislo=id`, naplnit `ec_cislo` dle mapy názvů.
2. Přepočítat `centrala1` řádky: `cinnost_id = (SELECT MIN(id) FROM vyroba_cinnost WHERE
   ec_cislo = cinnost_id_orig)` — protože pro import platí `cinnost_id_orig` = centrálské
   číslo. Opraveno 1 462 řádků (VR10609 už ukazuje Kabely, ne Gravírování). Vratné přes
   `cinnost_id = cinnost_id_orig`.
3. Přehled zobrazuje `DruhCinnosti = vc.ec_cislo` (u absencí CASE dle typu, viz výše).
4. **Oprava importu** `router.py` (`_sync_vyroba_work_ec`, ~ř.25850): mapuje přes
   `(SELECT MIN(id) FROM tenant.vyroba_cinnost WHERE tenant_id=:t AND ec_cislo=:cin)`.
   Aplikační import (`_sync_vyroba_work_app`) NEMĚNIT — tam je `:cin` už naše `id`.

**Doplněná činnost:** „Odměny fin.zakázek" (Centrála 27) u nás chyběla → založena
`tenant.vyroba_cinnost` id=50, `ec_cislo=27`, `strategie_cislo=NULL` (v S dřív nebyla),
179 řádků na ni přemapováno.

**Bez centrálského protějšku (ec_cislo NULL, správně):** Režie (id 14) a Bez rozlišení
činnosti (id 43) — Centrála je jako činnost nemá (je to zakázka „Rezie"); a mrtvá
„ostatní – kanceláře" (id 45, 0 použití).

## Gotchy / na co pozor
- **Naše čísla ≠ Centrála** mimo 1–5. Vždy překládej přes `ec_cislo`/`strategie_cislo`,
  nikdy nepředpokládej, že `vyroba_cinnost.id` = číslo z Centrály.
- **Absence NEJSOU ve `vyroba_cinnost`** — žijí v `att_entry_type` (category='absence');
  jejich centrálská čísla jsou namapovaná přímo v data_setu přehledu (CASE dle `code`).
- **Rezie bez diakritiky** — sjednoceno na tvar `Rezie` (viz znalost o sjednocení režie);
  práce na zakázce „Rezie" je běžná práce na zakázce, ne overhead.
- Kolize `ec_cislo=116` (id 13 dílenská + id 40 režijní „Ostatní – výroba") — v přepočtu
  neaktivní (Centrála 116 je režie, import ji nechával NULL), proto `MIN(id)` bezpečné.
