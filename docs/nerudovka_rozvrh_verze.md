# Nerudovka — prohlížeč verzí rozvrhu pro Klárku (návrh)

> Stav 21. 6. 2026: úvazky 2026/2027 spočítané (základ). Čekám na podklady od Marti
> (vygenerované verze rozvrhu) → podle jejich formátu doplním import. Tento dokument
> drží návrh, ať po příchodu podkladů jen zapojím.

## Cíl
Klárka má z generátoru **několik variant rozvrhu** pro 2026/2027. Chce je vidět
v appce, **přepínat mezi verzemi**, prohlížet po **třídách / učitelích / učebnách**
a varianty **porovnat** (která jí sedí líp) → vybere finální.

## Vstupní základ (HOTOVO)
- Úvazky 2026/2027 z úvazkového modulu Bakaláři (ruvazky, PLAT_OD 20260901):
  74 učitelů, hodiny správně (spoj-dedup ÷ 2), třídy (pokračující +1 ročník;
  nové 1. ročníky 2D–2J a 5 nových učitelů zatím bez zveřejněného označení).
- Excel `NERUDOVKA_uvazky_2026-2027.xlsx` (Souhrn + Detail + Poznámky).

## Datový model (návrh — vytvořím po podkladech)
- **`tenant.rozvrh_verze`** — jedna řada na variantu: `id, tenant_id, plat_od,
  nazev (např. „Varianta A"), zdroj, poznamka, je_finalni bool, created_by/at`.
- **`tenant.rozvrh_bunka`** — buňky rozvrhu (univerzální tvar nezávislý na zdroji):
  `verze_id, den (1-5), hodina (1-N), kod_trida, kod_ucitel, kod_pred, kod_ucebna,
  kod_cykl (lichý/sudý/každý), kod_skup (skupina)`. Překlady na zkratky přes
  `bakalari_trid_kod` (třídy) + `bakalari_pred`/`bakalari_ucit` (předměty/učitelé).
- Časy zvonění (hodina→od/do) zatím Bakaláři nevedou v rozvrhu — buď číselník
  `rozvrh_zvoneni`, nebo jen pořadí hodin.

## Obrazovka v appce (`/rozvrh-verze`, dlaždice „🗓️ Verze rozvrhu")
- **Přepínač verzí** (chipy A/B/C + poznámka + „finální").
- **Pohled**: 📚 po třídách / 👩‍🏫 po učitelích / 🚪 po učebnách (rail jako docházka).
- **Mřížka** den × hodina (Po–Pá), buňka = předmět + (učitel/třída/učebna dle pohledu)
  + odlišení lichý/sudý. Zoom A−/A+ (jako rozvrh přehled).
- **Porovnání 2 verzí** vedle sebe (rozdíly zvýrazněné) — fáze 2.
- ACL: rodiče + členové tenantu 13 (NERUDOVKA), RO pro běžné.

## STAV: Iterace 1 LIVE (21.6.2026) — jazyková kostra
- Datový model `tenant.rozvrh_verze` + `tenant.rozvrh_bunka` ✅.
- **Generátor (sandbox Python, `outputs/gen_lang2.py`)** — heuristický placer cizích jazyků.
  **🔑 KLÍČOVÝ MODEL:** jazykové skupiny napříč ročníky (KOD_SPOJ) běží **PARALELNĚ
  synchronizovaně** (žáci se rozdělí do NJ/FJ/ŠJ/RJ skupin ve stejný čas) → modelováno jako
  **bandy** (kohorta tříd × úroveň CJ = jeden blok, všechny paralelní skupiny ve stejných hodinách).
  Špatný model (skupiny proti sobě) dával 33 neumístěných; bandy → **1 neumístěná, skóre 9**.
- Tvrdá omezení v solveru: učitel/třída 1× za slot, AJ≤7h, 2./3.CJ≤8h, Ždimerová≥2h, Šedová≤7h,
  bloky 1+1+1/1+1+2/2+1+1, AJ 4.r dvouhodinovka, spread ≥3 dny. Měkká (skóre): rule18 (1.+2.CJ
  stejnou hodinu), <3 dny, adjacence. **40-60 seedů → top 3 varianty.**
- **3 varianty (A/B/C)** v PG, **0 kolizí učitelů** (ověřeno). Jazykové úrovně z předmětu+hodin
  (AJ=1.CJ; ostatní 4h=2.CJ, 2h=3.CJ) — TODO ověřit přes skupina Z/D zkratku.
- **Prohlížeč `/rozvrh-verze`** (dlaždice „🗓️ Varianty rozvrhu" v Bakaláři sekci) — chipy variant
  (skóre+neum.), pohled Třídy/Učitelé, mřížka Po–Pá×1–9, barvy dle úrovně CJ. Endpointy
  `/app/rozvrh/verze` + `/app/rozvrh/grid`.

## Další iterace (TODO)
- Ostatní předměty (z úvazků) — placement do volných slotů + učebnová omezení (kritéria D).
- Učebny: přiřazení z `bakalari_mistnost` dle pravidel (GDN→BNA/BPG, Písmo→BŠ/BK/BA, IT, velké ŠJ→10/13).
- Obědové vlny (4×5 tříd denně), přejezd Nerudovka↔Aťásy (1 volná h), bloky ČJL/ekonomika/aranžér/Lyceum, TV kluci.
- Ověřit CJ 2./3. úroveň přes skupina zkratku (Z/D) místo heuristiky hodin.
- Produkční generátor jako cloud akce (Klárka „Generovat" v appce) místo sandboxu.

## Import (DOPLNÍM po podkladech — záleží na formátu)
Možné zdroje od generátoru: export XML/CSV/Excel z Bakalářů, nebo tabulky `a_r_*`
(generátor) v Bakalářích. Pipeline: parse → mapování na `rozvrh_bunka` (den/hod/
třída/učitel/předmět/učebna/cyklus) → `verze` řádek. Reuse mostu `db=bakalari`
nebo upload souboru. **Klíč: dostat z každé varianty buňky do jednotného tvaru.**

## Gotchas (z dnešní práce na úvazcích — drž)
- Kódy tříd v rozvrhu/úvazku jsou Bakaláři-interní a matoucí → VŽDY překládat přes
  r_trid (kód→zkratka). Pro 2026/2027 r_trid ještě neexistuje → pokračující kohorty
  posun +1 ročník, nové 1. ročníky čekají na zveřejnění školou.
- Jazyky/TV = skupiny napříč třídami (KOD_SPOJ) → v rozvrhu jedna buňka pro spojenou
  skupinu, ne za každou třídu.
- POCET_HOD v úvazku = dvoutýdenní cyklus (÷2 na týden).
