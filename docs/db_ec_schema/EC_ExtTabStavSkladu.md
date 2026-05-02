# EC_ExtTabStavSkladu

**Schema**: dbo · **Cluster**: Other · **Rows**: 22,652 · **Size**: 9.32 MB · **Sloupců**: 47 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDKmenZbozi` | int | NE |  |  |
| 3 | `IDSklad` | nvarchar(30) | NE |  |  |
| 4 | `Mnozstvi` | numeric(19,6) | NE |  |  |
| 5 | `MnozstviDispo` | numeric(19,6) | NE |  |  |
| 6 | `MnozstviKVydeji` | numeric(19,6) | NE |  |  |
| 7 | `MnozNaDObjKVyrizeni` | numeric(19,6) | NE |  |  |
| 8 | `BlokovanoProDObj` | numeric(19,6) | NE |  |  |
| 9 | `StavSkladu` | numeric(19,6) | NE |  |  |
| 10 | `StavSkladuSouvis` | numeric(19,6) | NE |  |  |
| 11 | `Prumer` | numeric(19,6) | NE |  |  |
| 12 | `PrumerZadany` | numeric(19,6) | NE |  |  |
| 13 | `InventuraMn` | numeric(19,6) | NE |  |  |
| 14 | `InventuraCena` | numeric(19,6) | NE |  |  |
| 15 | `Minimum` | numeric(19,6) | NE |  |  |
| 16 | `Maximum` | numeric(19,6) | NE |  |  |
| 17 | `Sleva` | numeric(5,2) | NE |  |  |
| 18 | `Poznamka` | ntext | ANO |  |  |
| 19 | `UKod` | int | ANO |  |  |
| 20 | `Blokovano` | tinyint | NE |  |  |
| 21 | `DatPorizeni` | datetime | NE |  |  |
| 22 | `Autor` | nvarchar(128) | NE |  |  |
| 23 | `BlokovaniEditoru` | smallint | ANO |  |  |
| 24 | `JizNaSklade` | bit | NE |  |  |
| 25 | `Objednano` | numeric(19,6) | NE |  |  |
| 26 | `KontrolaVC` | nchar(1) | NE |  |  |
| 27 | `IDAkce` | int | ANO |  |  |
| 28 | `ZadavaniUmisteni` | smallint | NE |  |  |
| 29 | `MnozstviKPrijmu` | numeric(19,6) | NE |  |  |
| 30 | `MnozBezVyd` | numeric(20,6) | ANO |  |  |
| 31 | `MnozDispoBezVyd` | numeric(20,6) | ANO |  |  |
| 32 | `DatPorizeni_D` | int | ANO |  |  |
| 33 | `DatPorizeni_M` | int | ANO |  |  |
| 34 | `DatPorizeni_Y` | int | ANO |  |  |
| 35 | `DatPorizeni_Q` | int | ANO |  |  |
| 36 | `DatPorizeni_W` | int | ANO |  |  |
| 37 | `DatPorizeni_X` | datetime | ANO |  |  |
| 38 | `Rezervace` | numeric(20,6) | ANO |  |  |
| 39 | `PodMin` | numeric(20,6) | ANO |  |  |
| 40 | `NadMax` | numeric(20,6) | ANO |  |  |
| 41 | `Inventura_Mn` | numeric(20,6) | ANO |  |  |
| 42 | `Inventura_Fin` | numeric(20,6) | ANO |  |  |
| 43 | `MnozSPrij` | numeric(20,6) | ANO |  |  |
| 44 | `MnozDispoSPri` | numeric(20,6) | ANO |  |  |
| 45 | `MnozSPrijBezVyd` | numeric(20,6) | ANO |  |  |
| 46 | `MnozDispoSPrijBezVyd` | numeric(20,6) | ANO |  |  |
| 47 | `MnozstviKryte` | numeric(19,6) | NE |  |  |
