# EC_TempPrehledMat

**Schema**: dbo · **Cluster**: Other · **Rows**: 3,669 · **Size**: 2.01 MB · **Sloupců**: 30 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `CisloZakazky` | nvarchar(10) | ANO |  |  |
| 2 | `RegCis` | nvarchar(30) | NE |  |  |
| 3 | `Nazev` | nvarchar(100) | NE |  |  |
| 4 | `ZbyvaResit` | numeric(38,2) | ANO |  |  |
| 5 | `PozadDatDod` | date | ANO |  |  |
| 6 | `PotvrzDatDod` | date | ANO |  |  |
| 7 | `Poznamka` | varchar(1) | NE |  |  |
| 8 | `Autor` | nvarchar(128) | ANO |  |  |
| 9 | `DatPorizeni` | datetime | NE |  |  |
| 10 | `ID` | int | NE |  |  |
| 11 | `Nazev2` | nvarchar(100) | NE |  |  |
| 12 | `Objednano` | numeric(10,3) | ANO |  |  |
| 13 | `Vydano` | numeric(10,3) | ANO |  |  |
| 14 | `Vraceno` | numeric(10,3) | ANO |  |  |
| 15 | `ZustaloNaZakazce` | numeric(10,3) | ANO |  |  |
| 16 | `Kalkulovano` | numeric(12,3) | ANO |  |  |
| 17 | `PozadovanoVyroba` | numeric(10,3) | ANO |  |  |
| 18 | `ZbyvaResitNakup` | numeric(38,2) | ANO |  |  |
| 19 | `TerminOK` | int | NE |  |  |
| 20 | `PocetDniDoDodani` | int | ANO |  |  |
| 21 | `Objednavky` | nvarchar(MAX) | ANO |  |  |
| 22 | `TerminDodavky` | nvarchar(MAX) | ANO |  |  |
| 23 | `StavGenerDO_Text` | varchar(26) | ANO |  |  |
| 24 | `Skladem` | numeric(20,6) | ANO |  |  |
| 25 | `ZmenilKalkulaci` | nvarchar(128) | ANO |  |  |
| 26 | `DatZmenyKalkulace` | datetime | ANO |  |  |
| 27 | `Kod` | nvarchar(15) | ANO |  |  |
| 28 | `Blokovano` | tinyint | NE |  |  |
| 29 | `Dodavatel` | nvarchar(255) | ANO |  |  |
| 30 | `PotvrzDatDodText` | nvarchar(MAX) | ANO |  |  |
