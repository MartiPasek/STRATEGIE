# EC_MobilniTerminal

**Schema**: dbo · **Cluster**: Other · **Rows**: 202,793 · **Size**: 27.39 MB · **Sloupců**: 23 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Zpracovano` | bit | ANO | ((0)) |  |
| 3 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 4 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 5 | `CisloObjednavky` | int | ANO |  |  |
| 6 | `CisloZam` | int | ANO |  |  |
| 7 | `CisloTerminalu` | int | NE |  |  |
| 8 | `Command` | int | NE |  |  |
| 9 | `RegCis` | nvarchar(30) | ANO |  |  |
| 10 | `BarCode` | nvarchar(100) | ANO |  |  |
| 11 | `Mnozstvi` | numeric(19,6) | ANO |  |  |
| 12 | `MnozstviNavic` | nvarchar(1) | ANO |  |  |
| 13 | `DatZpracovatDo` | datetime | ANO |  |  |
| 14 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 15 | `Prijemka` | int | ANO |  |  |
| 16 | `KontrolaOK` | bit | ANO | ((0)) |  |
| 17 | `PoznamkaZpracovano` | nvarchar(1000) | ANO |  |  |
| 18 | `Poznamka` | nvarchar(MAX) | ANO |  |  |
| 19 | `Resitel` | nvarchar(128) | ANO |  |  |
| 20 | `PoznamkaZmeny` | ntext | ANO |  |  |
| 21 | `UzivCHYBA` | bit | ANO | ((0)) |  |
| 22 | `MnozstviPuvodni` | numeric(19,6) | ANO |  |  |
| 23 | `VybranyRegal` | nvarchar(20) | ANO |  |  |

## Indexy

- **PK** `PK_EC_MobilniTerminal1` (CLUSTERED) — `ID`
