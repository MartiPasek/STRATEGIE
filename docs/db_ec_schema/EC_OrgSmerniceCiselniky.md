# EC_OrgSmerniceCiselniky

**Schema**: dbo · **Cluster**: HR · **Rows**: 20 · **Size**: 0.07 MB · **Sloupců**: 12 · **FK**: 0 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Aktivni` | bit | NE | ((1)) |  |
| 3 | `Typ` | tinyint | NE |  |  |
| 4 | `TypText` | varchar(25) | NE |  |  |
| 5 | `Nazev` | nvarchar(255) | NE |  |  |
| 6 | `Popis` | nvarchar(1000) | ANO |  |  |
| 7 | `Priorita` | tinyint | ANO |  |  |
| 8 | `PocetDniDoDoruceni` | int | NE | ((0)) |  |
| 9 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 10 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 11 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 12 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_OrgSmernicePriority` (CLUSTERED) — `ID`
- **UNIQUE** `IX_EC_OrgSmernicePriority` (NONCLUSTERED) — `Priorita`
