# EC_Ukoly

**Schema**: dbo · **Cluster**: Other · **Rows**: 229,663 · **Size**: 5409.30 MB · **Sloupců**: 56 · **FK**: 0 · **Indexů**: 4

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDNadrazene` | int | ANO |  |  |
| 3 | `Stav` | tinyint | ANO |  |  |
| 5 | `Zadavatel` | int | NE |  |  |
| 6 | `Predmet` | nvarchar(255) | NE | ('') |  |
| 7 | `Popis` | ntext | ANO |  |  |
| 8 | `TerminZahajeni` | datetime | NE | (getdate()) |  |
| 9 | `TerminSplneni` | datetime | ANO | (getdate()+(1)) |  |
| 10 | `OdhadHod` | numeric(19,2) | ANO | ((0.5)) |  |
| 11 | `Neverejny` | bit | NE | ((0)) |  |
| 12 | `Aktivni` | bit | NE | ((0)) |  |
| 13 | `DatPrevzeti` | datetime | ANO |  |  |
| 14 | `DatZahajeni` | datetime | ANO |  |  |
| 15 | `DatDokonceni` | datetime | ANO |  |  |
| 16 | `DatKontroly` | datetime | ANO |  |  |
| 17 | `HotovoProcent` | smallint | NE |  |  |
| 18 | `RealHod` | numeric(19,2) | ANO |  |  |
| 19 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 20 | `InfoProZadavatele` | bit | NE | ((0)) |  |
| 21 | `InfoProResitele` | bit | NE | ((0)) |  |
| 22 | `ZadavatelChceInfo` | bit | ANO | ((0)) |  |
| 23 | `IDOpakUkol` | int | ANO |  |  |
| 24 | `IDCinnost` | int | ANO |  |  |
| 25 | `IDSmernice` | int | ANO |  |  |
| 26 | `IDKvalif` | int | ANO |  |  |
| 27 | `IDDoklad` | int | ANO |  |  |
| 28 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 29 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 30 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 31 | `DatZmeny` | datetime | ANO |  |  |
| 32 | `Import` | bit | NE | ((0)) |  |
| 33 | `ImportID` | int | ANO |  |  |
| 34 | `ZmenaTermSplneni` | datetime | ANO |  |  |
| 35 | `NavrhTermSpl` | int | NE |  |  |
| 36 | `NeverejnyUkol` | bit | NE | ((0)) |  |
| 37 | `DruhPozadavku` | int | ANO |  | 1 = Pozadavek IT (hardware,cipy,server...), 2 = Pozadavek systém (centrala,Helios,Ukolnik...), 3 = Pozadavek dovolena, 4 |
| 38 | `SeznamResitelu` | nvarchar(255) | ANO |  |  |
| 39 | `OfflineRequest` | tinyint | ANO |  | 1 = nový úkol, 2 = update ukolu |
| 40 | `IDObjMat` | int | ANO |  |  |
| 41 | `Popis_Bin` | varbinary(MAX) | ANO |  |  |
| 42 | `PrinosKC_Mes` | numeric(19,2) | ANO | ((0)) |  |
| 43 | `DatPoslPoznamka` | datetime | ANO |  |  |
| 44 | `DatPoslOtevZad` | datetime | ANO |  |  |
| 45 | `ProKazdehoUkolZvlast` | bit | ANO | ((0)) |  |
| 46 | `SchovatPredTerminem` | bit | ANO | ((0)) |  |
| 47 | `Informacni` | bit | ANO | ((0)) |  |
| 48 | `PrioritaPlanIT` | smallint | ANO |  |  |
| 49 | `VerzeChyba` | int | ANO |  |  |
| 50 | `VerzeOprava` | int | ANO |  |  |
| 51 | `IDPuvodnihoUkolu` | int | ANO |  |  |
| 53 | `StavText` | varchar(17) | NE |  |  |
| 54 | `PotvrdUkol_PoDokonceni` | bit | ANO | ((0)) |  |
| 55 | `NeBlokovatDochZadavatel` | bit | ANO | ((0)) |  |
| 56 | `NeBlokovatDochResitel` | bit | ANO | ((0)) |  |
| 57 | `JenZprava` | bit | ANO | ((0)) |  |
| 58 | `AutomatickyPotvrdit` | bit | ANO |  |  |

## Indexy

- **PK** `PK_EC_Ukoly` (CLUSTERED) — `ID`
- **INDEX** `Predmet` (NONCLUSTERED) — `Predmet`
- **INDEX** `Stav_Zadavatel_Includes` (NONCLUSTERED) — `DatDokonceni, Stav, Zadavatel`
- **INDEX** `Stav_Zadavatel_DatDokonceni` (NONCLUSTERED) — `Stav, Zadavatel, DatDokonceni`
