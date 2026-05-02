# EC_ZamestPlatby

**Schema**: dbo · **Cluster**: Other · **Rows**: 19,686 · **Size**: 2.30 MB · **Sloupců**: 14 · **FK**: 1 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Datum` | datetime | NE | (getdate()) |  |
| 3 | `CisloZam` | int | NE |  |  |
| 4 | `CisloZakazky` | varchar(15) | NE |  |  |
| 5 | `Vyplaceno` | int | NE |  |  |
| 6 | `Prijato` | int | NE | ((0)) |  |
| 7 | `Hotove` | bit | NE | ((0)) |  |
| 8 | `CisloDokladu` | varchar(30) | ANO |  |  |
| 9 | `DatumSplatnosti` | datetime | ANO |  |  |
| 10 | `Poznamka` | varchar(80) | ANO |  |  |
| 11 | `CisloOrg` | int | ANO |  |  |
| 12 | `Druh` | nvarchar(5) | ANO |  |  |
| 13 | `HodnotaSmer` | numeric(18,2) | ANO |  |  |
| 14 | `Uctovano` | bit | ANO |  |  |

## Cizí klíče (declared)

- `CisloZam` → [`TabCisZam`](TabCisZam.md).`Cislo` _(constraint: `FK_EC_ZamestFinalniFinance_TabCisZam`)_
