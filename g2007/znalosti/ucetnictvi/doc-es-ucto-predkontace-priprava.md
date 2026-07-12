# ES účto — systém řad dokladů a předkontací (příprava obšlehnutí z Heliosu)

> oblast: `ucetnictvi` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# ES účto — systém řad dokladů a předkontací (příprava obšlehnutí z Heliosu)

**Datum:** 25. 6. 2026 · **Autor:** Claude (ID23) · **Pro:** Marti
**Cíl (Marti):** „Totálně obšlehnout z Heliosu systém Řady dokladů a jejich předkontací. To je základ úspěchu." (ES = EUROSOFT-System, data v `DB_IS`.)

---

## 1. Co jsem v Heliosu našel (DB_EC/DB_IS — schéma identické)

Účetní/předkontační systém Heliosu stojí na těchto tabulkách:

| Tabulka | Role |
|---|---|
| **TabSbornik** | Číselník sborníků (= účetní řady dokladů). 82 řádků v ES. Klíč `Cislo` (`501`, `100`, `200`…), `Nazev`, `DruhData`, **`UcetMD`/`UcetDAL`** (default předkontace — viz pozn. níže), `Strana`, `Zaknihovano`, ~50 `Prenos_*` flagů (co se z dokladu táhne do deníku). |
| **TabSbornikDef** | Sborník per účetní období: `IdSbornik`, `IdObdobi`, `CiselnaRada`, `Blokovano`, `Uzaverka`, `DelkaPorCis`. |
| **TabDenik** | Účetní deník (zaúčtované řádky). Klíč: `Sbornik`, `CisloUcet`+`Strana`, **`UcetMD`/`UcetDAL`**, `CastkaMD`/`CastkaDAL`/`Castka`, `Mena`, `CisloOrg`, `Utvar`, `CisloZakazky`, `DICOrg`, **`IdDokladyZbozi`** (vazba na zdrojový doklad!), `ExtDoklad`. |
| **TabMaticeUcto** | Účtovací matice — odvození účtu z dimenzí: `CisloUcet` × (`CisloUtvar`, `CisloOrg`, `CisloZakazky`, `CisloNO`, `IdVozidlo`, `CisloZam`) s `PlatnostOd/Do` + `Prazdny*` zástupné znaky. = „když zakázka X / středisko Y → účet Z". |
| **TabMaStdUcto** / TabSTDUctovyRozvrhStandard | Standardní zaúčtování (šablony řádků) navázané na `Sbornik` (`IdStandardCislo`, `NadDoklad`). |
| **TabAutoUctovani(Par)** | Engine automatického účtování: `IdDokladu`, `Agenda`, `DruhPohybuZbo`, `StavUctovani` → generuje řádky deníku z dokladu dle sborníku. |

## 2. 🔑 Klíčové zjištění (drž!)

**Předkontace na hlavičce sborníku (`TabSbornik.UcetMD/UcetDAL`) je v ES skoro všude PRÁZDNÁ.** Z 82 sborníků má vyplněné účty jen **501 (FP tuzemsko): MD `431000` / DAL `321001`, Strana 1**.

→ **Reálná předkontace nežije na hlavičce sborníku, ale:**
1. v **zaúčtovaných řádcích `TabDenik`** (co se fakticky účtovalo — `Sbornik` → `UcetMD`/`UcetDAL` kombinace + četnost), a
2. ve **standardech** (`TabMaStdUcto`/`TabSTDUctovyRozvrhStandard`) + **matici** (`TabMaticeUcto`) pro dimenze.

**Doporučení:** předkontaci „obšlehnout" **empiricky z `TabDenik`** (jako jsme stavěli `bank_predkontace` — učit se z reality, doctrine #23), ne z prázdné hlavičky. Pro každý sborník zjistit reálné MD→DAL páry + jak často → to je pravdivá předkontační mapa.

## 3. Sborníky ES (výběr — celých 82 v DB)

Faktury: `100` FP tuzemsko, `110` FP EU, `120` FP 3Z, `150-170` dobropisy přijaté, `200` FV tuzemsko, `210` FV EU, `220` FV 3Z, `250-270` dobropisy vydané, `501` FP tuzemsko (MD 431000/DAL 321001), `601` FV tuzemsko.
Peníze: `060-069` banky, `070-077` pokladny, `075/076` kartové účty, `690` kartové centrum.
Interní: `080` interní doklady, `081` zápočty, `082` skonta, `083` rozpouštění režií, `090/099` PS/KS, `800` interní, `820` kurzové rozdíly, `830` přeúčtování DPH, `900` mzdy, `940` opakované platby.

## 4. Návrh mirroru ES předkontací (k odsouhlasení)

**Tabulky (PG, tenant.\*):**
- `tenant.es_sbornik` — 82 sborníků 1:1 (cislo, nazev, druh_data, ucet_md, ucet_dal, strana, zaknihovano). *(Pozn.: `tenant.ucet_sbornik` už částečně existuje — sjednotit/rozšířit.)*
- `tenant.es_predkontace` — **empirická předkontace z `TabDenik`**: per (sbornik, ucet_md, ucet_dal) → počet výskytů, objem, příklad dokladu. = co se reálně účtuje.
- (volitelně) `tenant.es_ucto_matice` — `TabMaticeUcto` pro dimenzionální odvození (zakázka/středisko → účet).

**Sync:** `sync-es-sbornik` (DB_IS.TabSbornik) + `sync-es-predkontace` (agregace `DB_IS.TabDenik` GROUP BY Sbornik, UcetMD, UcetDAL za 2025-26).

**UI:** rozšířit `/app/uctovani/rady` (už existuje — čte z deníku per sborník) o pohled „sborník → reálné MD/DAL + četnost" = předkontační katalog. Dlaždice/sekce ve Finance.

**Návaznost:** tahle mapa pak krmí účtovací engine (`bank_predkontace` → rozšířit o sborníkové předkontace) pro automatické zaúčtování dokladů do `ucetni_denik`.

## 5. Co potvrdit s Martim (po návratu z Heliosu)

1. **Mapování doklad-řada → sborník** — jak Helios ví, že FP (řada 500/510…) jde do sborníku `100`/`501`? (Konfigurace v sborníku přes `DruhData`/`Agenda` v `TabAutoUctovani`, nebo ručně při zaúčtování?) Tohle je most mezi doklady (které už máme 1:1) a předkontací.
2. **Zda brát předkontaci empiricky z TabDenik** (doporučeno) **vs** z `TabMaStdUcto` standardů (formálně definované šablony).
3. **Rozsah** — jen 2025-26 (čistý start), nebo i historie pro statistiku četnosti.
4. **Dimenze** — chceme i `TabMaticeUcto` (zakázka/středisko → účet), nebo zatím jen sborník-úroveň MD/DAL.

---

*Připraveno, čeká na Martiho vstup z Heliosu. Doklady EC i ES jsou už zrcadlené 1:1 (PF/FV/VO/PO/PP/kalkulace) → předkontace je logicky další vrstva: doklad → sborník → účty MD/DAL → deník.*


