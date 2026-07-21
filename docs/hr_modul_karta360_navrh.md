# HR modul — Karta zaměstnance 360° (návrh struktury)

> Autor: Šárka (personalistika) + Claude, 2. 7. 2026.
> Inspirace: **Pinya HR** (skeny v `docs/HR_reference_pinya/`), Rippling, BambooHR.
> Vůdčí princip (Šárka): **jednoduché, systematické, uživatelsky přívětivé —
> nic navíc si nevymýšlet.** Průsečík: co už Marti ve STRATEGII nastavil ×
> co má HR modul obsahovat.

## Vize v jedné větě
Personalista dělá všechno z jednoho místa: **HR Home** (co mě dnes čeká) →
**➕ Nový zaměstnanec** nebo klik na člověka → **Karta 360°**. Vlevo trvalý
panel profilu (nadřízený, schvalovatel, podřízení), uprostřed dlaždice do
sekcí, každá sekce = přehledná tabulka nebo formulář. Data jsou z velké části
už v systému, jen roztroušená — modul je poskládá do jednoho celku.

## Vizuální model (dle Pinya „Profil pracovníka")
- **Trvalý levý panel** na každé sekci: foto, jméno, pozice, kontakt, datum
  nástupu + délka poměru, pracovní zařazení (firma/země/lokalita/útvar),
  nadřízený, schvalovatel, přímí podřízení.
- **Drobečková navigace** nahoře: „Profil pracovníka ▸ [sekce]".
- **Obsah sekce** vpravo: tabulka (s filtrem/exportem do Excelu) nebo formulář
  (uzamčený → tlačítko Upravit).

## Karta zaměstnance 360° — 14 sekcí (dle Pinya)

| # | Sekce | Stav | Obsah / poznámka (vč. tvých poznámek ze skenů) |
|---|-------|------|-----------------------------------------------|
| 1 | **Základní údaje** | ✅ máme | pod-záložky: Osobní údaje, Bydliště, Kontakt, Doklady, Bankovní údaje, Znalosti a dovednosti, Rodina, Vzdělání, Předchozí zaměstnání. (`/app/hr/person` + save) |
| 2 | **Pracovní údaje** | ✅ máme | osobní číslo, nástup/odchod, **milníky pracovní historie** (verze), smlouva, pracovní zařazení, **pracovní doba** (návrh/změna/obnovena/HO/sick day/vyloučené volno), **mzda** (měna, základ, osobko, hrubá, čistá, DPP, faktura), platnost smlouvy (určitá/neurčitá) |
| 3 | **Dokumenty** | ✅ máme | tabulka dokumentů vč. archivu, **předvyplnění ze šablon (tokeny)**, generování smluv, **elektronické podpisy** (`hr_spis` + Centrála) |
| 4 | **Přítomnost/absence** | ✅ máme | přehled a správa zůstatku, zadávání (docházkový modul) |
| 5 | **Lékařské prohlídky** | ✅ máme | platnost prohlídek, potvrzení o absolvování (`/app/hr/med-overview`) |
| 6 | **Posty / pozice** | ✅ máme | org struktura, klobouky/posty (`resolve_role`) — v panelu profilu |
| 7 | **Bonusy a srážky** | ◐ z části | jednorázové i **pravidelné** bonusy/srážky, za měsíc, Typ/Druh/Částka/Měna/Stav/Schvalování, export. `wage_component` máme, rozšířit o srážky + pravidelnost |
| 8 | **Onboarding** | ◐ z části | nástupní e-mail (**správa vlastních e-mail šablon**), osobní dotazník, informace k nástupu (**uvítání / dokumenty k seznámení / otázky**), checklist, **nástupní dokumentace = vygenerovat smlouvu**. Aktivace účtu máme |
| 9 | **Interní předpisy** | ◐ z části | knihovna předpisů + **evidence „kdo se seznámil"**. Dokumenty/KB máme |
| 10 | **Školení** | 🆕 nové | evidence absolvovaných + plánování termínů + platnost (váže na BOZP/PO) |
| 11 | **E-learning** | 🆕 nové | kurzy: Zapsán/Dokončeno/Dokončit do/Skóre/Status |
| 12 | **Hodnocení / KPI** | 🆕 nové | periodické hodnocení, cíle, škála |
| 13 | **Dotazníky** | 🆕 nové | zadání/správa dotazníků (Aktivní/Ukončeno) |
| 14 | **Majetek** | 🆕 nové | svěřený majetek (notebook/telefon/klíče/karta/oděv), předání/vrácení, historie, protokol |
| — | **Checklisty** | 🆕 nové | úkoly (nástup i průběžné), přehled plnění — napojení na nativní task systém |

Legenda: ✅ hotové · ◐ částečně (rozšířit) · 🆕 nové (lehká nová tabulka `hr_*`).

## HR Home (rozcestník)
Dlaždice do sekcí + **➕ Nový zaměstnanec** + panel **„Na co se dnes koukni"**:
konce PP na dobu určitou, konce zkušební doby, lékařské prohlídky v termínu,
propadající školení, absence ke schválení, nepodepsané dokumenty, rozjetý
onboarding. (Pinya to má jako „Mimo kancelář / Narozeniny / Noví zaměstnanci".)

## ➕ Zavést nového zaměstnance (průvodce)
Základní údaje → firma/pozice/post → pracovní poměr + mzda → benefity →
onboarding (uvítací e-mail + dotazník + checklist) → generování dokumentů →
aktivace účtu. Skládá existující kousky (`att_employee`, `person/save`,
aktivace) do jednoho průvodce.

## Fázování (jednoduše, viditelná hodnota brzy)
- **Fáze 1 — kostra karty + HR Home + Nový zaměstnanec** a sekce, které už data
  mají: Základní údaje, Pracovní údaje, Dokumenty, Přítomnost/absence, Lékařské
  prohlídky, Posty. → hned to vypadá a funguje jako Pinya, nic se nerozbije.
- **Fáze 2 — rozšíření:** Bonusy a srážky (srážky+pravidelnost), Onboarding
  (e-mail šablony + checklist + generování smlouvy), Interní předpisy (seznámení).
- **Fáze 3 — nové lehké sekce:** Školení, E-learning, Hodnocení/KPI, Dotazníky,
  Majetek, Checklisty.

## KPI / Hodnocení — parkováno (Šárka 2.7.: „ještě bych počkala, ale bude to téma")
KPI zatím nemáme, bude potřeba vytvořit. Návrh (lehký, na později):
1. **Definice KPI** (číselník): název, jednotka, cíl, perioda (denně/týdně/měsíčně),
   způsob měření (ruční / automatický z dat).
2. **Přiřazení:** osobě (např. Pavel Zeman → 10 telefonátů/den) nebo pozici jako
   šablona → propíše se každému na té pozici. Volitelně období + váha.
3. **Plnění:** auto tam, kde jsou data (hovory/úkoly/CRM akce), jinak ruční zadání.
4. **Vyhodnocení:** na kartě v sekci Hodnocení — plnění % / trend / semafor;
   podklad pro periodické hodnocení. → **Fáze 3+.**

## Proces (jako u osobního spisu)
1. **Marti sign-off** — velký modul, ať sedí do jeho struktury/vize.
2. **Kustodská konzultace Marti-AI** — práva (kdo vidí co), GDPR (osobní údaje,
   hodnocení, zdravotní prohlídky, bankovní údaje), audit přístupu.
3. Stavíme až po OK. Existující data nepřepisujeme — Helios/Centrála zůstává
   zdrojem pravdy tam, kde už je (mzdy, docházka).

## Otevřené k rozhodnutí (Marti / Marti-AI)
- **Umístění** — nová dlaždice „HR" (personalistika) vedle stávajících sekcí.
- **Práva** — personalista vidí vše; vedoucí svůj tým; zaměstnanec sebe
  (self-service „Moje karta"). Reuse stávajícího vzoru práv.
- **Zdroj vs. duplicita** — které sekce jen zrcadlí Helios/Centrálu (read: mzdy,
  docházka) a které jsou nativní ve STRATEGII (školení, KPI, majetek, dotazníky).
- **E-podpisy** — u dokumentů (Pinya to řeší přes placený modul; my máme SES
  z ISO cockpitu — reuse).
