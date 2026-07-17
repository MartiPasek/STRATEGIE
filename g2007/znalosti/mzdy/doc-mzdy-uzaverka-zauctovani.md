# Mzdy — měsíční uzávěrka a zaúčtování (runbook)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Mzdy — měsíční uzávěrka a zaúčtování (runbook)

Cloud Helios **iNuvio**, DB **UCTO_EC** (EUROSOFT‑Control) / **UCTO_ES** (EUROSOFT‑System).
Poprvé projeto a ověřeno na období **06/2026** (17. 7. 2026, Claude + Marti).

---

## TL;DR — rychlý postup

1. **Výpočet mezd** dokončený a odsouhlasený (rekapitulace sedí).
2. **Středisko na mzdách = `001`** u všech (`TabZamMzd.Stredisko`). Bez střediska to nejde — viz níže.
3. Mzdy → *Výpočet mzdy* → **Účtování mezd** (při dotazu na přepis červnového dokladu dej *ano*).
4. Zkontroluj kontaci (`TabMzKontace`) — `Utvar` musí být `001`, **žádné `Err`**.
5. **Přenos do Účetnictví** (do deníku).
6. Zkontroluj deník (`TabDenik`) — vše na `001`, částky sedí na kontaci.
7. **Měsíční uzávěrka mzdového období** (zamkne období, otevře další).

---

## ⚠️ Klíčové ponaučení: STŘEDISKO je na nákladech povinné

Empiricky ověřeno 06/2026: **mzdy nejdou zaúčtovat bez střediska.**

- **Nákladové účty (třída 5)** mají v Heliosu „středisko povinné":
  `512000` (cestovné), `521000/521001/521002` (mzdové náklady),
  `524000` (zákonné SP), `524100` (zákonné ZP), `527000/527001` (zákonné sociální náklady).
  Když je středisko prázdné (`NULL`), kontace u nich vyhodí do `Utvar` hodnotu **`Err`**
  a **přenos do deníku by tyto řádky shodil.**
- **Rozvahové / závazkové účty (třída 3)** — `331` (zaměstnanci), `336` (pojišťovny),
  `342` (daň) atd. — středisko **nevyžadují**, prázdné projde.

**Řešení (rozhodnutí Marti):** nerozlišujeme střediska → **všechny mzdy vedeme na jedno společné středisko `001`.**
`NULL` ani „vypnout povinnost na nákladových účtech" nepoužíváme (rozbilo by to nákladové účetnictví po střediscích).

> Pozn.: v datech byla původně směs `001` / `900` / `002`. Sjednoceno na `001`.

---

## Postup krok po kroku (Helios iNuvio)

1. **Výpočet mezd** — Mzdy → *Výpočet mzdy*. Spočítat všechny, projet kontrolní sestavy
   (Rekapitulace mezd, kontrola SP/ZP a daně).
2. **Středisko = 001** — zajistit, že mzdové záznamy mají středisko `001`
   (`TabZamMzd.Stredisko`, viz SQL níže). Když ne, srovnat.
3. **Účtování mezd** — Mzdy → *Výpočet mzdy* → pás karet **Účtování mezd**.
   Vygeneruje účetní doklad podle **kontace mezd** (předkontace). Při přepisu existujícího
   dokladu za období dej *ano*.
4. **Kontrola kontace** — `TabMzKontace` za období: `Utvar` musí být všude `001`,
   **nula `Err`**. Když je `Err`, chybí povinné středisko na nákladovém účtu → srovnat krok 2 a přegenerovat.
5. **Přenos do Účetnictví** — doklad se přenese do účetního deníku (`TabDenik`).
6. **Kontrola deníku** — vše na `001`, součet = součet z kontace (nic se neztratí/nezdvojí),
   deník je podvojný (každý řádek `UcetMD` + `UcetDAL` + `Castka`), takže vyrovnaný z podstaty.
7. **Měsíční uzávěrka** — Mzdy → **Uzavření mzdového období**. Zamkne období
   (`Uzavreno = 3`) a další měsíc je otevřený (`Stav = 1`).

---

## DB reference (kde co je)

**Přístup přes bridge:** `db=mssql188` → cloud **EUR‑DB‑MSSQL‑1P**, default DB **MOST**, login **sa**,
UCTO_EC / UCTO_ES se čtou **cross‑db z MOST** (tříčlenné názvy `UCTO_EC.dbo.…`).
Pozor: `db=mssql` jde na **on‑prem EC‑SERVER2\SQLEXPRESS2017** (DB_EC, DB_IS, DB_ST…) — **UCTO tam NENÍ.**

| Co | Tabulka | Klíčové sloupce |
| --- | --- | --- |
| Mzdové období | `TabMzdObd` | `Rok`, `Mesic`, `IdObdobi`, `Uzavreno` (**3 = zavřeno**, 0 = otevřeno), `Stav` (**1 = aktuální**, 2 = příští), `UzavreniObdobi_Datum`, `UzavreniObdobi_Autor` |
| Mzdy za období | `TabZamMzd` | `IdObdobi`, `CisloZam`, **`Stredisko`**, `VyplatniStredisko` |
| Kontace (výstup zaúčtování) | `TabMzKontace` | `IdObdobi`, `CisloZam`, `CisloUcet`, `Strana`, `Castka`, **`Utvar`** (`Err` = chybí povinné středisko) |
| Účetní deník | `TabDenik` | `UcetMD`, `UcetDAL`, `Castka`, **`Utvar`**, **`IdObdobiMZ`** (vazba na mzdové období), `DatumPripad` |

Vždy nejdřív vyřeš `IdObdobi`:
`SELECT IdObdobi FROM UCTO_EC.dbo.TabMzdObd WHERE Rok=2026 AND Mesic=6`

---

## Ověřovací SQL (bridge `db=mssql188`)

Středisko na mzdách:
```sql
SELECT ISNULL(Stredisko,'<NULL>') stred, COUNT(*) pocet
FROM UCTO_EC.dbo.TabZamMzd
WHERE IdObdobi=(SELECT IdObdobi FROM UCTO_EC.dbo.TabMzdObd WHERE Rok=2026 AND Mesic=6)
GROUP BY Stredisko;
```

Hromadné nastavení střediska na 001 (kdyby bylo potřeba srovnat):
```sql
UPDATE UCTO_EC.dbo.TabZamMzd SET Stredisko='001'
WHERE IdObdobi=(SELECT IdObdobi FROM UCTO_EC.dbo.TabMzdObd WHERE Rok=2026 AND Mesic=6);
```
> Před hromadným zásahem si udělej zálohu: `SELECT * INTO MOST.dbo._bak_… FROM UCTO_EC.dbo.TabZamMzd WHERE …`

Kontrola kontace na „Err" (musí vrátit 0 řádků):
```sql
SELECT CisloUcet, COUNT(*) FROM UCTO_EC.dbo.TabMzKontace
WHERE IdObdobi=(SELECT IdObdobi FROM UCTO_EC.dbo.TabMzdObd WHERE Rok=2026 AND Mesic=6)
  AND Utvar='Err' GROUP BY CisloUcet;
```

Součet deníku za mzdy + kontrola střediska:
```sql
SELECT ISNULL(Utvar,'<NULL>') utvar, COUNT(*) radku, SUM(Castka) suma
FROM UCTO_EC.dbo.TabDenik
WHERE IdObdobiMZ=(SELECT IdObdobi FROM UCTO_EC.dbo.TabMzdObd WHERE Rok=2026 AND Mesic=6)
GROUP BY Utvar;
```

Stav uzávěrky období:
```sql
SELECT Rok, Mesic, Uzavreno, Stav, UzavreniObdobi_Datum, UzavreniObdobi_Autor
FROM UCTO_EC.dbo.TabMzdObd WHERE Rok=2026 AND Mesic BETWEEN 5 AND 8 ORDER BY Mesic;
```

---

## Výsledek 06/2026 (referenční)

| Firma | Zaměstnanců | Deník (Kč) | Středisko | Uzavřeno |
| --- | --- | --- | --- | --- |
| EC | 17 | **2 977 060** | vše `001` | 17. 7. 2026 19:34 |
| ES | 32 z 33 | **5 880 878** | vše `001` | 17. 7. 2026 19:36 |

> ES: 32 z 33 — jeden člověk bez mzdového nákladu (nejspíš Šafránková, mateřská). Nejde o chybu střediska.

---

## Poznámky / TODO do budoucna

- **Autor uzávěrky = `sa`.** Cloudové operace teď jedou pod `sa` (v květnu byl autor „Martia").
  Do auditní stopy by měl jít konkrétní člověk → založit pojmenované loginy na cloudu.
  (Marti‑AI login je zatím jen na on‑prem EC‑SERVER2, na cloudu EUR‑DB‑MSSQL‑1P ještě není.)
- **JMHZ** je samostatný proces (viz `docs/jmhz/`): generuje se z Heliosu, ověřuje proti ČSSZ,
  odesílá **datovkou** (regulatorně na člověku). Pozor: **ošetřovné se vyplácí přes samostatnou
  žádost o ošetřovné, ne přes JMHZ** — vyloučené doby v JMHZ dávku nespouští.
- Zálohové tabulky v MOST po ověření **uklízet** (`_bak_…`), ať se nehromadí.



