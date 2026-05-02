# EC_TerminyPlan

**Schema**: dbo · **Cluster**: Other · **Rows**: 34 · **Size**: 0.09 MB · **Sloupců**: 14 · **FK**: 6 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 4 | `Predmet` | nvarchar(100) | ANO |  |  |
| 5 | `DateStart` | datetime | NE |  |  |
| 6 | `DateStop` | datetime | NE |  |  |
| 7 | `TimeStart` | datetime | ANO | ((0)) |  |
| 8 | `TimeEnd` | datetime | ANO | ((0)) |  |
| 9 | `Skupina` | int | ANO |  |  |
| 10 | `PraceZakazka` | nvarchar(15) | ANO |  |  |
| 11 | `PraceUkol` | int | ANO |  |  |
| 12 | `Poznamka` | ntext | ANO |  |  |
| 13 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 14 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Cizí klíče (declared)

- `Skupina` → [`EC_TerminyPlanSkup`](EC_TerminyPlanSkup.md).`Skupina` _(constraint: `FK_EC_TerminyPlan_EC_TerminyPlanSkup`)_
- `ID` → [`EC_TerminyPlan`](EC_TerminyPlan.md).`ID` _(constraint: `FK_EC_TerminyPlan_EC_TerminyPlan`)_
- `CisloZakazky` → `TabZakazka`.`CisloZakazky` _(constraint: `FK_EC_TerminyPlan_TabZakazka`)_
- `PraceZakazka` → `TabZakazka`.`CisloZakazky` _(constraint: `FK_EC_TerminyPlan_TabZakazka1`)_
- `CisloZam` → [`TabCisZam`](TabCisZam.md).`Cislo` _(constraint: `FK_EC_TerminyPlan_TabCisZam`)_
- `PraceUkol` → `TabUkoly`.`ID` _(constraint: `FK_EC_TerminyPlan_TabUkoly`)_

## Indexy

- **PK** `PK_EC_OrgPlanZam` (CLUSTERED) — `ID`
