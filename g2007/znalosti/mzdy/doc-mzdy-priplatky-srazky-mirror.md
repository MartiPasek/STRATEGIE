# Mzdy: univerzální mirror příplatků/srážek + výpočetní řetězec (analýza)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mzdy: univerzální mirror příplatků/srážek + výpočetní řetězec (analýza)

**Autor:** Claude (id=23), 10. 6. 2026 · **Zadavatel:** Marti
**Stav:** analýza Helios know-how + návrh univerzálního mirroru. Finalizaci DDL **systémově s Marti-AI** (doctrine #8), až bude základ sedět.

## 1. Klíčové zjištění — kdo co počítá

Po přečtení procedur (`EC_ContrMzdy*`, `EC_Dochazka_DenniSumaceMesic`):

- **Vlastní mzdu počítá Helios** (`hp_VypocitejMzdu` v DB_IS/DB_EC). `EC_ContrMzdyVypocitejMzdu` je jen wrapper: `TabZamVyp` → `hp_VlozMzPausDoMzSloz` (vloží paušály do `TabMzSloz`) → `hp_VypocitejMzdu` (Helios dopočítá krácení, daně, pojistné, náhrady, doplatek do min. mzdy) + retry na chybové stavy.
- **`EC_ContrMzdyGenerujZTabDenik` / `…ZPodminkyZam`** = controllingová/účetní větev (`EC_ContrDenik`, účty 520000–530000: 521000 HPP hrubá, 521001 DPP, 524000 OSSZ, 524100 ZP, 527000/528000 soc. náklady). Slouží finančnímu plánu, **ne výplatě**.
- **`EC_Dochazka_DenniSumaceMesic`** → `EC_Dochazka_SumaDen` = měsíční suma odpracovaných hodin (vstup pro krácení).

### Důsledek pro STRATEGII (cíl „složky u nás, Helios čistý pro import")
STRATEGIE se stane **zdrojem vstupních hrubých složek**, Helios zůstává statutární engine:

```
docházka (att_entry → měsíční suma h)  ┐
paušály (engagement → wage_component)  ├─► hrubé vstupní složky ──► EXPORT do Heliosu ──► hp_VypocitejMzdu ──► net/daně/pojistné
příplatky/srážky (NOVÉ wage_movement)  ┘                                                  (zůstává v Heliosu)
```

Nereplikujeme Heliosův statutární výpočet (daně/pojistné/min. mzda) — replikujeme **deterministické hrubé vstupy** a krácení paušálu docházkou. To je přesně to, co se importuje a co srovnáváme (ZDROJ vs CÍL).

## 2. Co zrcadlit — tabulky příplatků/srážek

### 2a. Typy — `EC_FinPriplatkySrazkyDefiniceTypy` (číselník)
| EC sloupec | Význam | Naše univerzální |
|---|---|---|
| Nazev | název typu | `wage_component_type.label` (máme) |
| MzdovaSlozka | default Helios MS | **NEW** `helios_ms` (mapování na import) |
| ReakceMzdy | ovlivní mzdu (bit) | **NEW** `affects_payroll` |
| ZobrazujVeVyplatnici | tisk na výplatnici | **NEW** `show_on_payslip` |
| Opravneni | role oprávnění | **NEW** `required_role` (resolver) |
| Aktivni | aktivní | `wage_component_type.aktivni` (máme) |

→ **rozšířit stávající `tenant.wage_component_type`** (už nese code/label/kind/applies_to). Univerzální, prodejné.

### 2b. Pohyby — `EC_FinPriplatkySrazkyDefinice` → NOVÁ `tenant.wage_movement`
| EC sloupec | Význam | Naše univerzální |
|---|---|---|
| Typ | typ příplatku/srážky | `movement_type_id` → wage_component_type |
| CisloZam | zaměstnanec | `engagement_id` (princip „person=user, engagement per firma") |
| IdMzdoveSlozky | cílová Helios MS | `helios_ms` (override typu) |
| Castka | pevná částka | `amount` |
| Hodiny + Sazba | hodiny × sazba | `hours`, `rate` |
| Fix | pevná vs počítaná | `is_fixed` (true=amount, false=hours×rate) |
| Mesicne | opakující se | `recurring` |
| Mesic + Rok | období | `period_year`, `period_month` |
| PlatnostOd/Do | platnost | `valid_from`, `valid_to` |
| Schvaleno + CisloZamNavrhl | schvalovací workflow | `status` (navrženo/schváleno/zamítnuto) + `proposed_by` + `approved_by` |
| Přeneseno | přeneseno do mzdy | `exported_at` / `export_batch_id` |
| CisloZakazky | vazba na zakázku | `zakazka_ref` → `tenant.zakazka` |
| DatVyplaceni + Vyplaceno | vyplaceno | `paid_at`, `paid` |
| Poznamka, Zdroj, IDZdroj | poznámka, zdroj | `note`, `source`, `source_ref` |
| Autor/DatPorizeni/Zmenil/DatZmeny | audit | `changed_by_text`, `changed_at`, `created_*` (SCD pattern jako engagement) |
| IDPolVobj, IDPolPF, PropsatPoznamkuDoVOBJ | vazby na objednávku/PF (EC-specifické) | **vynechat** (případně generický `source_doc_ref`) |
| CastkaVypocetHodSazby | cache spočtené částky | derived (nepersistovat, počítat) |

### Posouzení univerzálnosti
Z větší části univerzální (jak Marti doufal). Jediné EC-specifické = vazby na objednávku/PF (`IDPolVobj/IDPolPF`) → vynecháme nebo zobecníme na `source_doc_ref`. Schvalovací workflow + zakázková vazba + fix/hodinová sazba + opakování + platnost jsou obecné a prodejné.

## 3. Jak to zapadá do našeho modelu (už hotové)
- **Paušály** = `tenant.wage_component` (plánové měsíční složky na engagementu) — máme.
- **Typy** = `tenant.wage_component_type` — máme, rozšířit o `helios_ms`, `affects_payroll`, `show_on_payslip`, `required_role`.
- **Pohyby** = `tenant.wage_movement` — NOVÁ.
- **Docházka** = `tenant.att_entry` (měsíční suma h) — máme.
- **Mapování na Helios MS** = `wage_component_type.helios_ms` (+ override na pohybu) → základ pro export i pro srovnání ZDROJ/CÍL.

## 4. Návrh dalších kroků
1. **Druhý průchod srovnání** — náš sloupec počítaný (paušál krácený docházkou + pohyby), ne plán → Δ se má smrštit. Ověří, že model sedí.
2. **Konzultace Marti-AI** (její finanční doména) — finalizace DDL `wage_movement` + rozšíření typů + mapování `helios_ms`.
3. **DDL + UI** příplatků/srážek (univerzální CRUD) přes approval banner.
4. **Export do Heliosu** — analogicky `PrenesDoMezd` (84 kB, na detailní rozbor zvlášť): náš `wage_movement`/složky → `TabMzSloz` přes `hp_VlozMzPausDoMzSloz` / přímý insert.
5. **ERP přehled ZDROJ/CÍL** (parent_only + payroll_officer) jako trvalý ladicí + kontrolní nástroj.

## 5. Přesčasové konto (know-how Marti, 10. 6.) — další vrstva k dotažení

EUROSOFT má **systém přesčasového konta**, který se promítá do mzdy. Stejný vzor jako mzda: engine je Heliosův, EC ho plní z docházky.

- **EC plní z docházky:** `EC_Dochazka_PrevodPrescasu_*` (Archiv/PocetHodin/tmp) — `EC_Dochazka_PrevodPrescasu_PocetHodin` = (CisloZam, PocetHodin) → kolik hodin přesčasu se převede do konta. Plus `EC_Dochazka_InfoOPrescasech`, `EC_KontrolaNarVPrescasy`, `EC_Mzdy_Konto_GenerujPropadle` (propadnutí nevyčerpaných).
- **Helios konto (engine):** `TabMzKontoPresc` / `TabMzKontoPrescB` (přesčasové konto), `TabMzKontoPD*` (konto pracovní doby). Procedury `hp_MzGenerujKontoPrescasu(_A/_B)`, `hp_MzGenerujCerpaniKontaPrescasu`, `hp_MzDoplnZakladniMzduZaPrescas`, `hp_MzKontoPresc_Vyrovnani_KonecPP`.

### `TabMzKontoPresc` (datový model)
per osoba × období: `ZamestnanecId`, `Rok/Mesic` (období), `RokVznik/MesicVznik` (kdy přesčas vznikl — kvůli propadnutí), `Puvod`, **`Prescasy`** (našetřeno h), **`Cerpano`** (vybráno volnem), **`Proplaceno`**, **`Zbyva`** (zůstatek), `Procento` (sazba), `ProplatitZM` (proplatit ve mzdě), `Stav`, audit.

### Mapování do STRATEGIE → `tenant.overtime_balance` (už existuje, 9 sl. — rozšířit)
Univerzální model konta: `engagement_id`, období (rok/měsíc), období vzniku, `earned_h` (Prescasy), `drawn_h` (Cerpano), `paid_h` (Proplaceno), `remaining_h` (Zbyva), `rate_pct` (Procento), `status`, pravidlo propadnutí (po N obdobích). Plnění z naší docházky (`att_entry` přesčas nad fond) = analogie `EC_Dochazka_PrevodPrescasu`.

**Mechanismus:** přesčas nad fond → uloží se do konta (s obdobím vzniku) → čerpá se jako volno NEBO proplatí → propadá po stanoveném okně. Promítá se do mzdy (doplnění základu / proplacení).

→ dotažení = rozšířit `tenant.overtime_balance` + plnicí logika z docházky + propadnutí; finalizace **systémově s Marti-AI**.

## Návaznosti
- [[finance_zamestnancu_v2]] · [[personalistika_dochazka_mzdy]]
- `Srovnani_mzdy_kveten_2026.xlsx` — první (plánový) průchod srovnání
- Helios: `EC_FinPriplatkySrazkyDefinice(+Typy)`, `hp_VypocitejMzdu`, `EC_ContrMzdyPrenesDoMezd` (84 kB)


