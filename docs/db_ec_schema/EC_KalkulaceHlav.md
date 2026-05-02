# EC_KalkulaceHlav

**Schema**: dbo · **Cluster**: Production · **Rows**: 7,309 · **Size**: 2.31 MB · **Sloupců**: 43 · **FK**: 1 · **Indexů**: 4

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDDoklad` | int | ANO |  |  |
| 3 | `CisloKalkulace` | nvarchar(15) | NE |  |  |
| 4 | `RadaDokladu` | nvarchar(3) | NE | ('001') |  |
| 5 | `Objednat` | bit | NE | ((0)) |  |
| 6 | `CisloZam` | int | ANO |  |  |
| 7 | `CisloZamObj` | int | ANO |  |  |
| 8 | `Objednavam` | bit | NE | ((0)) |  |
| 9 | `DatObjednaniOd` | datetime | ANO |  |  |
| 10 | `DatObjednaniDo` | datetime | ANO |  |  |
| 11 | `VKM` | numeric(5,2) | NE | ((0.0)) |  |
| 12 | `Arbeit` | numeric(5,2) | NE | ((0.0)) |  |
| 13 | `Koeffizient` | numeric(5,2) | NE | ((0.0)) |  |
| 14 | `MarzeProcent` | numeric(5,2) | ANO | ((0)) |  |
| 15 | `CenaBezZna` | numeric(8,2) | ANO |  |  |
| 16 | `CenaZnaceni1` | numeric(8,2) | ANO |  |  |
| 17 | `CenaZnaceni2` | numeric(8,2) | ANO |  |  |
| 18 | `CenaMarze` | numeric(8,2) | ANO |  |  |
| 19 | `CenaBezPrjATra` | numeric(8,2) | ANO |  |  |
| 20 | `CenaProjekt` | numeric(8,2) | ANO |  |  |
| 21 | `CenaTransport` | numeric(8,2) | ANO |  |  |
| 22 | `CelkemCena` | numeric(8,2) | ANO |  |  |
| 23 | `CelkemHodBezZna` | numeric(8,2) | ANO |  |  |
| 24 | `HodZnaceni1` | numeric(8,2) | ANO |  |  |
| 25 | `HodZnaceni2` | numeric(8,2) | ANO |  |  |
| 26 | `CelkemHod` | numeric(8,2) | ANO |  |  |
| 27 | `CelkemHmotnost` | int | ANO |  |  |
| 28 | `SkutecNaklady` | numeric(18,2) | ANO |  |  |
| 29 | `DatumKalkSkutecNakl` | datetime | ANO |  |  |
| 30 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 31 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 32 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 33 | `DatZmeny` | datetime | ANO |  |  |
| 34 | `BlokovaniEditoru` | smallint | ANO |  |  |
| 35 | `DatPorizeni_Y` | int | ANO |  |  |
| 36 | `DatPoslZpracovani` | datetime | ANO |  |  |
| 37 | `DatPoslKontrolyPol` | datetime | ANO |  |  |
| 38 | `SkladovaKalkulace` | bit | ANO | ((0)) |  |
| 39 | `Nakupci` | int | ANO |  |  |
| 40 | `AutomatickyDoobjednavat` | bit | ANO | ((0)) |  |
| 41 | `PocitatSVratkou` | bit | ANO | ((0)) |  |
| 42 | `SkladovaVRKalkulace` | bit | ANO | ((0)) |  |
| 43 | `IgnorujBlokaci` | bit | ANO | ((0)) |  |

## Cizí klíče (declared)

- `IDDoklad` → `TabDokladyZbozi`.`ID` _(constraint: `FK_EC_KalkulaceHlav_EC_KalkulaceHlav`)_

## Indexy

- **PK** `PK_EC_KalkulaceHlav` (CLUSTERED) — `ID`
- **INDEX** `IX_EC_KalkulaceHlav` (NONCLUSTERED) — `ID`
- **INDEX** `IX_EC_KalkulaceHlav_1` (NONCLUSTERED) — `ID`
- **INDEX** `IX_EC_KalkulaceHlav_By_IDDoklad` (NONCLUSTERED) — `IDDoklad`
