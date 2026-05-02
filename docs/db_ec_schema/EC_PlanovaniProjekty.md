# EC_PlanovaniProjekty

**Schema**: dbo · **Cluster**: Other · **Rows**: 10 · **Size**: 0.09 MB · **Sloupců**: 26 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDNadrazene` | int | ANO |  |  |
| 3 | `Aktivni` | bit | NE | ((1)) |  |
| 4 | `Nazev` | nvarchar(255) | NE |  |  |
| 5 | `Popis` | ntext | ANO |  |  |
| 6 | `Adresar` | nchar(40) | ANO |  |  |
| 7 | `CisloZam` | int | ANO |  |  |
| 8 | `CisloZamZastup` | int | ANO |  |  |
| 9 | `CisloZamVedouci` | int | ANO |  |  |
| 10 | `PrioritaVedouci` | tinyint | ANO |  |  |
| 11 | `PrioritaZam` | tinyint | ANO |  |  |
| 12 | `HodinyPlan` | int | ANO |  |  |
| 13 | `FinancePlan` | int | ANO |  |  |
| 14 | `HodinyRealita` | int | ANO |  |  |
| 15 | `FinanceRealita` | int | ANO |  |  |
| 16 | `HotovoProcent` | int | NE | ((0)) |  |
| 17 | `DatumZacatkuPlan` | datetime | ANO |  |  |
| 18 | `DatumDokonceniPlan` | datetime | ANO |  |  |
| 19 | `DatumZacatkuReal` | datetime | ANO |  |  |
| 20 | `DatumDokonceniReal` | datetime | ANO |  |  |
| 21 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 22 | `DatZmeny` | datetime | ANO |  |  |
| 23 | `DatKontroly` | datetime | ANO |  |  |
| 24 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 25 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 26 | `Poznamka` | ntext | ANO |  |  |

## Indexy

- **PK** `PK_EC_PlanovaniProjekty` (CLUSTERED) — `ID`
