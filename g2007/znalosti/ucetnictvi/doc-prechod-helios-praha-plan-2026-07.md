# Přechod účetnictví a dokladů do nového Heliosu (Praha) — plán

> oblast: `ucetnictvi` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Přechod účetnictví a dokladů do nového Heliosu (Praha) — plán

**Datum:** 5. 7. 2026 · **Horizont:** 3 týdny (do ~26. 7. 2026) · **Vede:** Marti Pašek

## Cíl
Otočit tok dokladů (výroba, zakázky, banka) ze **starého Heliosu (Plzeň)** do **nového Heliosu (Praha, cloud CMIS)**. Mzdy a účetní deník už v Praze běží — teď navazují doklady a banka.

## Proč (kontext)
- **Asseco** ukončilo podporu staré MSSQL databáze („nůž na krk") → nutný přechod na novou.
- Současně s projektem **digitalizace** jsme novou databázi umístili na **bezpečný cloud v Praze (CMIS)**.
- **Úspora nákladů:** MSSQL už není edice Standard, ale **Express**.

## Cílový model (jak to nově funguje)
- **Helios = jen účetnictví + mzdy.** Rozhraní do Heliosu = **účetní deník**.
- **Doklady a banka nejsou součástí Heliosu.**
- **Zakázky a střediska (útvary) se v účetnictví už nerozlišují.** Analytiku zakázek vedeme dál, ale **mimo Helios** (STRATEGIE).
- Od **1. 1. 2026 sklad A → B**: příjemky a vydejky se **neúčtují** (z deníku se odstraní).

## Stav
| Oblast | Stav |
|---|---|
| Mzdy | ✅ Praha |
| Účetní deník | ✅ Praha |
| Doklady + banka | ⏳ zatím starý Helios (Plzeň) → otočit |

## Harmonogram
**Týden 1 (do ~12. 7.)**
- Zastavit plzeňské účtování **2. pololetí** na starém Heliosu.
- Informovat **Martia 2000** (e-mail — samostatný návrh).
- Účetní: dokončit **uzávěrku 1. pololetí 2026**.
- Účetní: **uzavřít DPH za červen do 17. 7. 2026**.

**Týden 2 (do ~19. 7.)**
- Přenést změny účetního deníku do Prahy.
- Ověřit **DPH + kontrolní hlášení** za červen v Praze a podat včas.
- Technicky napojit tok dokladů + banky → deník Praha.

**Týden 3 (do ~26. 7.)**
- Ostrý provoz dokladů do nového Heliosu (Praha).
- **Reconciliace** deníku Praha × Plzeň (kontrola úplnosti).
- Vypnout starý tok v Plzni.

## Odpovědnosti
- **Marti** — vede přechod, přenos deníku do Prahy, DPH + KH.
- **Petra** — finance, banka, doklady (nový tok).
- **Martia 2000** — uzávěrka 1. pololetí + DPH za červen (Plzeň).
- **Claude / STRATEGIE** — technický přenos deníku, engine dokladů a banky.

## Pojistky
- Paralelní běh, dokud se nepotvrdí úplnost dat v Praze.
- Reconciliace deníku Praha × starý Helios **před** vypnutím starého toku.


