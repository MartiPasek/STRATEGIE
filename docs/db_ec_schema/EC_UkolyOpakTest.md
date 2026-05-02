# EC_UkolyOpakTest

**Schema**: dbo · **Cluster**: Other · **Rows**: 19,817 · **Size**: 48.41 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `TerminZahajeni` | datetime | ANO |  |  |
| 3 | `TerminSplneni` | datetime | ANO |  |  |
| 4 | `Zadavatel` | int | ANO |  |  |
| 6 | `Predmet` | nvarchar(255) | NE | (N'chybí predmet!!!!!!!!!!!!!!!!!!') |  |
| 7 | `Priorita` | tinyint | NE | ((1)) |  |
| 8 | `Popis` | ntext | ANO |  |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 11 | `IDUkoluOpak` | int | ANO |  |  |
| 12 | `OKUloz` | bit | ANO |  |  |
| 13 | `SeznamResitelu` | nvarchar(4000) | ANO |  |  |
| 14 | `SeznamKopie` | nvarchar(4000) | ANO |  |  |
| 15 | `Popis_bin` | varbinary(MAX) | ANO |  |  |

## Indexy

- **PK** `PK_EC_UkolyOpakTest` (CLUSTERED) — `ID`
