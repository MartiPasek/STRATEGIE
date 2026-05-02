# EC_TerminyPlanSkup

**Schema**: dbo · **Cluster**: Other · **Rows**: 5 · **Size**: 0.08 MB · **Sloupců**: 6 · **FK**: 0 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Skupina` | int | NE |  |  |
| 3 | `Nazev` | nchar(40) | NE |  |  |
| 4 | `Poznamka` | nchar(100) | ANO |  |  |
| 5 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 6 | `DatPorizeni` | datetime | NE | (getdate()) |  |

## Indexy

- **PK** `PK_EC_TerminyPlanSkup` (CLUSTERED) — `ID`
- **UNIQUE** `UQ__EC_Termi__0F10E22860086F5B` (NONCLUSTERED) — `Skupina`
