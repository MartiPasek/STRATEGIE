# EC_Ukoly_Komplet

**Schema**: dbo · **Cluster**: Other · **Rows**: 630,777 · **Size**: 737.48 MB · **Sloupců**: 73 · **FK**: 0 · **Indexů**: 5

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDUkol` | int | ANO |  |  |
| 3 | `IDNadrazene` | int | ANO |  |  |
| 4 | `Stav` | tinyint | ANO |  |  |
| 5 | `StavText` | nvarchar(100) | NE |  |  |
| 6 | `StavResitel` | tinyint | ANO |  |  |
| 7 | `StavResitelText` | nvarchar(100) | ANO |  |  |
| 8 | `Zadavatel` | int | NE |  |  |
| 9 | `Predmet` | nvarchar(255) | NE | ('') |  |
| 10 | `Popis` | ntext | ANO |  |  |
| 11 | `TerminZahajeni` | datetime | NE | (getdate()) |  |
| 12 | `TerminSplneni` | datetime | ANO | (getdate()+(1)) |  |
| 13 | `OdhadHod` | numeric(19,2) | ANO | ((0.5)) |  |
| 14 | `Aktivni` | bit | NE | ((0)) |  |
| 15 | `DatPrevzeti` | datetime | ANO |  |  |
| 16 | `DatZahajeni` | datetime | ANO |  |  |
| 17 | `DatDokonceni` | datetime | ANO |  |  |
| 18 | `DatKontroly` | datetime | ANO |  |  |
| 19 | `HotovoProcent` | smallint | NE |  |  |
| 20 | `RealHod` | numeric(19,2) | ANO |  |  |
| 21 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 22 | `InfoProZadavatele` | bit | NE | ((0)) |  |
| 23 | `InfoProResitele` | bit | NE | ((0)) |  |
| 24 | `ZadavatelChceInfo` | bit | ANO | ((0)) |  |
| 25 | `IDOpakUkol` | int | ANO |  |  |
| 26 | `IDCinnost` | int | ANO |  |  |
| 27 | `IDSmernice` | int | ANO |  |  |
| 28 | `IDKvalif` | int | ANO |  |  |
| 29 | `IDDoklad` | int | ANO |  |  |
| 30 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 31 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 32 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 33 | `DatZmeny` | datetime | ANO |  |  |
| 34 | `Import` | bit | NE | ((0)) |  |
| 35 | `ImportID` | int | ANO |  |  |
| 36 | `ZmenaTermSplneni` | datetime | ANO |  |  |
| 37 | `NavrhTermSpl` | int | NE |  |  |
| 38 | `NeverejnyUkol` | bit | NE | ((0)) |  |
| 39 | `DruhPozadavku` | int | ANO |  |  |
| 40 | `IDResitelVazba` | int | ANO |  |  |
| 41 | `VazbaTyp` | tinyint | ANO |  |  |
| 42 | `VazbaAktivni` | bit | ANO |  |  |
| 43 | `Priorita` | int | ANO |  |  |
| 44 | `ZakazkaNazev` | nvarchar(100) | ANO |  |  |
| 45 | `ZakazkaDruhyNazev` | nvarchar(100) | ANO |  |  |
| 46 | `PoTerminuSplneni` | int | NE |  |  |
| 47 | `TerminOsobni` | datetime | ANO |  |  |
| 48 | `Dulezitost` | tinyint | ANO |  |  |
| 49 | `PrioritaPocitana` | nchar(10) | ANO |  |  |
| 50 | `UserJeKopie` | bit | ANO |  |  |
| 51 | `UserJeResitel` | bit | ANO |  |  |
| 52 | `ZadavatelLogin` | nvarchar(100) | ANO |  |  |
| 53 | `UserJeZadavatel` | bit | ANO |  |  |
| 54 | `SeznamResitelu` | nvarchar(1000) | ANO |  |  |
| 55 | `PosledniPoznamka` | nvarchar(MAX) | ANO |  |  |
| 56 | `AutorPoznamky` | nvarchar(50) | ANO |  |  |
| 57 | `DnesOdpracovano` | numeric(19,2) | ANO |  |  |
| 58 | `Zakaznik` | nvarchar(100) | ANO |  |  |
| 59 | `NazevSmernice` | nvarchar(255) | ANO |  |  |
| 60 | `User` | int | ANO |  |  |
| 61 | `SeznamKopie` | nvarchar(1000) | ANO |  |  |
| 62 | `SeznamResiteluText` | nvarchar(MAX) | ANO |  |  |
| 63 | `SeznamKopieText` | nvarchar(MAX) | ANO |  |  |
| 64 | `IDObjMat` | int | ANO |  |  |
| 65 | `Popis_bin` | varbinary(MAX) | ANO |  |  |
| 66 | `DatPoslPoznamka` | datetime | ANO |  |  |
| 67 | `DatPoslOtevreni` | datetime | ANO |  |  |
| 68 | `DatPoslOtevZad` | datetime | ANO |  |  |
| 70 | `ProKazdehoUkolZvlast` | bit | ANO | ((0)) |  |
| 71 | `SchovatPredTerminem` | bit | ANO | ((0)) |  |
| 72 | `Informacni` | bit | ANO | ((0)) |  |
| 73 | `JenZprava` | bit | ANO | ((0)) |  |
| 74 | `AutomatickyPotvrdit` | bit | ANO |  |  |

## Indexy

- **PK** `PK_EC_Ukoly_Komplet` (CLUSTERED) — `ID`
- **INDEX** `IX_Ukoly_Komplet_User` (NONCLUSTERED) — `User`
- **INDEX** `IDUkol_Includes` (NONCLUSTERED) — `User, IDUkol`
- **INDEX** `IDUkol` (NONCLUSTERED) — `IDUkol`
- **INDEX** `Ex_Ukoly_Vykryti` (NONCLUSTERED) — `IDUkol, SeznamResitelu, CisloZakazky, UserJeKopie, User, StavResitel, IDObjMat`
