# EC_Hala2015

**Schema**: dbo · **Cluster**: Production · **Rows**: 802 · **Size**: 0.41 MB · **Sloupců**: 21 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Nazev` | nvarchar(255) | ANO |  |  |
| 3 | `Poznamka` | ntext | ANO |  |  |
| 4 | `Skupina` | int | ANO |  |  |
| 5 | `Platil` | nvarchar(50) | ANO |  |  |
| 6 | `CenaNabidky` | numeric(19,6) | ANO |  |  |
| 7 | `CenaObjednavky` | numeric(19,6) | ANO |  |  |
| 8 | `CenaBezDPH` | numeric(19,6) | ANO |  |  |
| 9 | `DatumZaplaceni` | datetime | ANO |  |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |
| 14 | `Kredit` | numeric(19,2) | ANO |  |  |
| 15 | `Debet` | numeric(19,2) | ANO |  |  |
| 16 | `DatPripadu` | datetime | ANO |  |  |
| 17 | `IdZdroj` | int | ANO |  |  |
| 18 | `Oznac1` | bit | ANO | ((0)) |  |
| 19 | `Oznac2` | bit | ANO | ((0)) |  |
| 20 | `Oznac3` | bit | ANO | ((0)) |  |
| 21 | `Zustatek` | numeric(19,2) | ANO |  |  |

## Indexy

- **PK** `PK_EC_Hala2015` (CLUSTERED) — `ID`
