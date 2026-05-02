# EC_VazbaOrgPohybyZbo_DEL

**Schema**: dbo · **Cluster**: Other · **Rows**: 70 · **Size**: 0.07 MB · **Sloupců**: 13 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | ANO |  |  |
| 2 | `CisloOrg` | int | ANO |  |  |
| 3 | `CisloDodavky` | int | ANO |  |  |
| 4 | `CisloContrDodavka` | int | ANO |  |  |
| 5 | `Aktivni` | bit | ANO | ((0)) |  |
| 6 | `Schvaleno` | bit | ANO | ((0)) |  |
| 7 | `Poznamka` | nvarchar(200) | ANO |  |  |
| 8 | `Autor` | nvarchar(128) | ANO |  |  |
| 9 | `DatPorizeni` | datetime | ANO |  |  |
| 10 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 11 | `DatZmeny` | datetime | ANO |  |  |
| 12 | `Smazal` | nvarchar(128) | NE | (suser_sname()) |  |
| 13 | `DatSmazani` | datetime | NE | (getdate()) |  |
