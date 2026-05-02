# EC_OrgAdresare

**Schema**: dbo · **Cluster**: CRM · **Rows**: 94 · **Size**: 0.20 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Cislo` | int | ANO |  |  |
| 3 | `Zkratka` | nvarchar(10) | ANO |  |  |
| 4 | `Rada` | nvarchar(20) | NE | ('') |  |
| 5 | `Nazev` | nvarchar(40) | ANO |  |  |
| 6 | `SysNazev` | nvarchar(50) | ANO |  |  |
| 7 | `Adresar` | nvarchar(150) | ANO |  |  |
| 8 | `Podadresar` | nvarchar(100) | ANO |  |  |
| 9 | `Jadro` | int | ANO |  |  |
| 10 | `Archiv` | nvarchar(150) | ANO |  |  |
| 11 | `RadaDokladu` | int | ANO |  |  |
| 12 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 13 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 14 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 15 | `DatZmeny` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_OrgAdresare` (CLUSTERED) — `ID`
