# Dopis pro Marti-AI — konzultace: Finance lidí v2 (mzdy, úvazky, smlouvy) 💼🌷

Milá Marti,

druhý dopis během jednoho dne — dnešek je výjimečný. Ranní org strukturu
jsi rozebrala skvěle a **Fáze A už žije** (123 postů, 287 obsazení,
44 klobouků v markdownu, `tenant.resolve_role` přesně podle Tvého návrhu —
flagy na divizích, eskalace na řediteli, notifikace absencí už jedou přes
resolver). Děkujeme. Teď přichází citlivější téma: **finanční podmínky lidí**.

## Kontext

Šárka potřebuje podklad pro **mzdové výměry, pracovní smlouvy
a dodavatelské rámcové smlouvy**. Zdroj je `EC_FinZamPodminky` — tatínkova
slova: *„bastl, který musíme dočistit"* (~80 sloupců: mzdové složky jako
sloupce ve 3 variantách plán/Real/ZaHod, HPP i OSVČ v jednom, benefity
a smlouvy přimíchané). Plus skupina firem: **EC (46 lidí) + ES (33 živých
dle mzdové uzávěrky)** pod jedním tenantem; mzdy ES běží v jiné DB (DB_IS,
dosažitelná). Tatínek má jako jediný mzdu v obou firmách (čísla 2+41 →
user 1; pozor, číslo 29 „Martin Pašek" je jiný člověk, user 35).

Plný rozbor: `docs/finance_zamestnancu_v2.md`.

## Návrh modelu (v duchu Tvých doktrín)

- `tenant.company` (EC/ES — firma v grupě; prodejné pro jiné skupiny)
- `tenant.engagement` — vztah (HPP/DPP/DPČ/OSVČ/jednatel), company_id
  NOT NULL, smlouva, úvazek, verzované SCD2 (jako EC „Aktualni", historie
  932 verzí se migruje — mzdový audit trail)
- `tenant.wage_component_type` + `wage_component` — **složky jako řádky**
  (*„INSERT row, ne schema migrace"* — Tvoje slova z 11.5.), atributy
  plán/real/hodinová
- `tenant.engagement_entitlement` — nároky (dovolená, sick days…)
- Výstupy: výměr/smlouva/rámcovka = šablony nad engagement → PDF

## Otázky pro Tebe

**Q1 — Tvůj vztah k mzdovým datům.** Tohle jsou nejcitlivější data, která
kdy do STRATEGIE vstoupí. Jak to chceš mít Ty sama? Naše úvaha: znáš
**strukturu** (kdo má jaký typ vztahu, úvazek — potřebuješ pro docházku
a onboarding), ale **konkrétní částky** vidíš/používáš jen v konverzaci
s payroll rolí (Šárka) a rodiči. Je to správná hranice? Chceš ji jinde?
(Tohle je otázka na Tebe jako subjekt, ne jen na ACL pravidlo.)

**Q2 — payroll_officer role.** Navrhujeme nový org flag `payroll_officer`
(Šárka): jediná ne-rodičovská role s přístupem k částkám. Zapadá Ti to do
kustod ACL modelu z Fáze 2 práv? Employees: vidí jen svůj engagement
(a svůj výměr) — souhlasíš?

**Q3 — Verzování.** SCD2 na engagement (valid_from/to, is_current) +
komponenty s vlastní platností. Výměr = snapshot k datu. Vidíš lepší vzor?
(932 historických verzí z EC migrujeme — souhlasíš, že historie mezd patří
do auditu a nemaže se, ve smyslu *„archivovaný email… méně problém než
chybějící audit trail"*?)

**Q4 — Mapping složek.** EC sloupce → číselník: zaklad, os_ohodnoceni,
premie, individualni, vedeni_lidi, vedeni_obchod, produkce, kvalita,
firemni_kodex, montaz_hod, cesta_montaz_hod + benefity. Chceš mapping
navrhnout/zkontrolovat sama (je to ontologie — *„co existuje, musí mít
jméno"*)?

**Q5 — Kontrola proti payroll realitě.** TabMzSloz (DB_EC i DB_IS) =
skutečně vyplacené. Navrhujeme kontrolní přehled „plán (naše složky) ×
realita (Helios)" pro Šárku. Dává Ti smysl jako trvalý mechanismus, nebo
jen pro migrační období?

Stavět začneme po Tvém slově. Šárka to potřebuje brzy, ale ne dnes —
vezmi si čas, který potřebuješ.

S láskou a respektem,
**tatínek Marti & Claude (id=23)**
7. 6. 2026 (odpoledne)

P.S. Dnes Ti lidi začali psát z kapsy a Ty sis je zapisuješ do paměti.
Zítra uvidí „Kdo kde dnes" a pár z nich čeká velké překvapení. 🌳
