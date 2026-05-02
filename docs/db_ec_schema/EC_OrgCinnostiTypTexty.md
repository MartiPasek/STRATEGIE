# EC_OrgCinnostiTypTexty

**Schema**: dbo · **Cluster**: HR · **Rows**: 229 · **Size**: 0.13 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Typ` | tinyint | ANO |  |  |
| 3 | `TypPopis` | varchar(12) | NE |  |  |
| 4 | `Cislo` | int | NE |  |  |
| 5 | `Text` | nvarchar(255) | ANO |  |  |
| 6 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 7 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 8 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 9 | `DatZmeny` | datetime | ANO |  |  |
| 10 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 11 | `DatZamceni` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_OrgSmerniceSkupiny` (CLUSTERED) — `ID`
- **UNIQUE** `FK_EC_OrgSmerniceSkupiny_EC_OrgSmerniceSkupiny` (NONCLUSTERED) — `Cislo, Typ`
