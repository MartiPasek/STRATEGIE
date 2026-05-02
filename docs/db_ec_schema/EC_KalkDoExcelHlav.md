# EC_KalkDoExcelHlav

**Schema**: dbo · **Cluster**: Production · **Rows**: 1 · **Size**: 0.02 MB · **Sloupců**: 18 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `PoradoveCislo` | int | ANO |  |  |
| 2 | `CisloOrg` | int | ANO |  |  |
| 3 | `OznProjektu` | nvarchar(60) | ANO |  |  |
| 4 | `PopisProjektu` | nvarchar(80) | ANO |  |  |
| 5 | `Firma` | nvarchar(255) | ANO |  |  |
| 6 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 7 | `Nazev` | nvarchar(100) | ANO |  |  |
| 8 | `DruhyNazev` | nvarchar(100) | ANO |  |  |
| 9 | `Prijemce` | int | ANO |  |  |
| 10 | `CisloKalkulace` | nvarchar(15) | NE |  |  |
| 11 | `CisloZam` | int | ANO |  |  |
| 12 | `Resitel` | nvarchar(100) | ANO |  |  |
| 13 | `Koeffizient` | numeric(5,2) | NE |  |  |
| 14 | `Arbeit` | numeric(5,2) | NE |  |  |
| 15 | `VKM` | numeric(5,2) | NE |  |  |
| 16 | `MarzeProcent` | numeric(5,2) | ANO |  |  |
| 17 | `ZkrFirmy` | nvarchar(10) | ANO |  |  |
| 18 | `Datum` | datetime | NE |  |  |
