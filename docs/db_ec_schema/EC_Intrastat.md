# EC_Intrastat

**Schema**: dbo · **Cluster**: Other · **Rows**: 148 · **Size**: 0.14 MB · **Sloupců**: 32 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDDoklad` | int | ANO |  |  |
| 3 | `Obdobi` | int | ANO |  |  |
| 4 | `IDDoprava` | int | ANO |  |  |
| 5 | `PoradoveCisloDokladu` | int | ANO |  |  |
| 6 | `DICKontrola` | nvarchar(15) | ANO |  |  |
| 7 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 8 | `Mesic` | int | ANO |  |  |
| 9 | `Rok` | int | ANO |  |  |
| 10 | `Zakaznik` | int | ANO |  |  |
| 11 | `FakturovanaHodnotaKc` | numeric(9,0) | ANO |  |  |
| 12 | `Kurz` | numeric(9,0) | ANO |  |  |
| 13 | `FakturovanaHodnotaVal` | numeric(9,2) | ANO |  |  |
| 14 | `VlastniHmotnost` | numeric(9,2) | ANO |  |  |
| 15 | `AdresaDoruceni` | nvarchar(2000) | ANO |  |  |
| 16 | `KodIntrastat` | int | ANO |  |  |
| 17 | `DIC` | nvarchar(15) | ANO |  |  |
| 18 | `DICPartnera` | nvarchar(15) | ANO |  |  |
| 19 | `StatOdeslani` | nvarchar(3) | ANO |  |  |
| 20 | `KrajPuvodu` | nvarchar(50) | ANO |  |  |
| 21 | `ZemePuvodu` | nvarchar(50) | ANO |  |  |
| 22 | `Transakce` | int | ANO |  |  |
| 23 | `DruhDopravy` | int | ANO |  |  |
| 24 | `DodaciPodminky` | nvarchar(10) | ANO |  |  |
| 25 | `TypVety` | nvarchar(3) | ANO |  |  |
| 26 | `StatistickyZnak` | nvarchar(50) | ANO |  |  |
| 27 | `MnozstviMJ` | numeric(19,6) | ANO |  |  |
| 28 | `Smer` | nvarchar(3) | ANO |  |  |
| 29 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 30 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 31 | `Zmenil` | nvarchar(128) | ANO | (suser_sname()) |  |
| 32 | `DatZmeny` | datetime | ANO | (getdate()) |  |

## Indexy

- **PK** `PK__EC_Intra__3214EC278064A129` (CLUSTERED) — `ID`
