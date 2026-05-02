# EC_MobilniTerminal_160111_103400

**Schema**: dbo · **Cluster**: Other · **Rows**: 1,557 · **Size**: 0.26 MB · **Sloupců**: 15 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Zpracovano` | bit | ANO |  |  |
| 3 | `DatPorizeni` | datetime | NE |  |  |
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
| 14 | `Autor` | nvarchar(128) | ANO |  |  |
| 15 | `Prijemka` | int | ANO |  |  |
