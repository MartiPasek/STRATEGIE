# EC_Vytizeni_Efektivita

**Schema**: dbo · **Cluster**: Production · **Rows**: 953 · **Size**: 0.32 MB · **Sloupců**: 14 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZam` | int | ANO |  |  |
| 3 | `Jmeno` | nvarchar(50) | ANO |  |  |
| 4 | `Prijmeni` | nvarchar(50) | ANO |  |  |
| 5 | `CisloZakaznika` | int | ANO |  |  |
| 6 | `Efektivita` | int | ANO |  |  |
| 7 | `PocetProjektu` | int | ANO |  |  |
| 8 | `Vypomoc` | bit | ANO | ((0)) |  |
| 9 | `TextVytizeni` | nvarchar(200) | ANO |  |  |
| 10 | `PocetProjektuSefmonter` | int | ANO |  |  |
| 11 | `PocetHodinProZak` | numeric(19,2) | ANO |  |  |
| 12 | `Externi` | bit | ANO | ((0)) |  |
| 13 | `CisloOrg` | int | ANO |  |  |
| 14 | `NezobrazujVInfu` | bit | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_Vytizeni_Efektivita` (CLUSTERED) — `ID`
