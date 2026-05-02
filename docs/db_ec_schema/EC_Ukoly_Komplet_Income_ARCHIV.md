# EC_Ukoly_Komplet_Income_ARCHIV

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.02 MB · **Sloupců**: 70 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | ANO |  |  |
| 2 | `IDUkol` | int | ANO |  |  |
| 3 | `IDUkol_New` | int | ANO |  |  |
| 4 | `IDNadrazene` | int | ANO |  |  |
| 5 | `Stav` | tinyint | ANO |  |  |
| 6 | `StavText` | nvarchar(100) | ANO |  |  |
| 7 | `StavResitel` | tinyint | ANO |  |  |
| 8 | `StavResitelText` | nvarchar(100) | ANO |  |  |
| 9 | `Zadavatel` | int | ANO |  |  |
| 10 | `Predmet` | nvarchar(255) | ANO |  |  |
| 11 | `Popis` | ntext | ANO |  |  |
| 12 | `TerminZahajeni` | datetime | ANO |  |  |
| 13 | `TerminSplneni` | datetime | ANO |  |  |
| 14 | `OdhadHod` | numeric(19,2) | ANO |  |  |
| 15 | `Neverejny` | bit | ANO |  |  |
| 16 | `Aktivni` | bit | ANO |  |  |
| 17 | `DatPrevzeti` | datetime | ANO |  |  |
| 18 | `DatZahajeni` | datetime | ANO |  |  |
| 19 | `DatDokonceni` | datetime | ANO |  |  |
| 20 | `DatKontroly` | datetime | ANO |  |  |
| 21 | `HotovoProcent` | smallint | ANO |  |  |
| 22 | `RealHod` | numeric(19,2) | ANO |  |  |
| 23 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 24 | `InfoProZadavatele` | bit | ANO |  |  |
| 25 | `InfoProResitele` | bit | ANO |  |  |
| 26 | `ZadavatelChceInfo` | bit | ANO |  |  |
| 27 | `IDOpakUkol` | int | ANO |  |  |
| 28 | `IDCinnost` | int | ANO |  |  |
| 29 | `IDSmernice` | int | ANO |  |  |
| 30 | `IDKvalif` | int | ANO |  |  |
| 31 | `IDDoklad` | int | ANO |  |  |
| 32 | `Autor` | nvarchar(128) | ANO |  |  |
| 33 | `DatPorizeni` | datetime | ANO |  |  |
| 34 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 35 | `DatZmeny` | datetime | ANO |  |  |
| 36 | `Import` | bit | ANO |  |  |
| 37 | `ImportID` | int | ANO |  |  |
| 38 | `ZmenaTermSplneni` | datetime | ANO |  |  |
| 39 | `NavrhTermSpl` | bit | ANO |  |  |
| 40 | `NeverejnyUkol` | bit | ANO |  |  |
| 41 | `DruhPozadavku` | int | ANO |  |  |
| 42 | `IDResitelVazba` | int | ANO |  |  |
| 43 | `VazbaTyp` | tinyint | ANO |  |  |
| 44 | `VazbaAktivni` | bit | ANO |  |  |
| 45 | `Kopie` | bit | ANO |  |  |
| 46 | `Priorita` | int | ANO |  |  |
| 47 | `ZakazkaNazev` | nvarchar(100) | ANO |  |  |
| 48 | `ZakazkaDruhyNazev` | nvarchar(100) | ANO |  |  |
| 49 | `PoTerminuSplneni` | bit | ANO |  |  |
| 50 | `TerminOsobni` | datetime | ANO |  |  |
| 51 | `Dulezitost` | tinyint | ANO |  |  |
| 52 | `PrioritaPocitana` | nchar(10) | ANO |  |  |
| 53 | `UserJeKopie` | bit | ANO |  |  |
| 54 | `UserJeResitel` | bit | ANO |  |  |
| 55 | `ZadavatelLogin` | nvarchar(50) | ANO |  |  |
| 56 | `UserJeZadavatel` | bit | ANO |  |  |
| 57 | `SeznamResitelu` | nvarchar(255) | ANO |  |  |
| 58 | `PosledniPoznamka` | nvarchar(MAX) | ANO |  |  |
| 59 | `AutorPoznamky` | nvarchar(50) | ANO |  |  |
| 60 | `DnesOdpracovano` | numeric(19,2) | ANO |  |  |
| 61 | `Zakaznik` | nvarchar(100) | ANO |  |  |
| 62 | `NazevSmernice` | nvarchar(255) | ANO |  |  |
| 63 | `Resitel` | int | ANO |  |  |
| 64 | `SeznamKopie` | nvarchar(255) | ANO |  |  |
| 65 | `DruhZmeny` | tinyint | ANO |  |  |
| 66 | `Zpracovano` | bit | ANO |  |  |
| 67 | `DatZpracovani` | datetime | ANO |  |  |
| 68 | `Popis_Bin` | varbinary(MAX) | ANO |  |  |
| 69 | `ZaznamVlozil` | nvarchar(50) | ANO |  |  |
| 70 | `IDObjMat` | int | ANO |  |  |
