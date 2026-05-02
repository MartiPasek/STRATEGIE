# EC_VazbaOrgPohybyZbo

**Schema**: dbo · **Cluster**: Other · **Rows**: 1,341 · **Size**: 0.20 MB · **Sloupců**: 11 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloOrg` | int | ANO |  |  |
| 3 | `CisloDodavky` | int | ANO |  |  |
| 4 | `CisloContrDodavka` | int | ANO |  |  |
| 5 | `Aktivni` | bit | ANO | ((0)) |  |
| 6 | `Schvaleno` | bit | ANO | ((0)) |  |
| 7 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 11 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK_EC_VazbaOrgPohybyZbo` (CLUSTERED) — `ID`
