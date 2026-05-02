# EC_HodnoceniVP_Uzavrene

**Schema**: dbo · **Cluster**: HR · **Rows**: 587 · **Size**: 0.42 MB · **Sloupců**: 38 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Rok` | int | ANO |  |  |
| 3 | `Mesic` | int | ANO |  |  |
| 4 | `CisloZam` | int | ANO |  |  |
| 5 | `PrijmeniJmeno` | nvarchar(201) | ANO |  |  |
| 6 | `LoginID` | nvarchar(128) | ANO |  |  |
| 7 | `PocetFaktur` | int | ANO |  |  |
| 8 | `PocetNabidek` | int | ANO |  |  |
| 9 | `PocetPOBJ` | int | ANO |  |  |
| 10 | `FakturyCastkaCelkem` | numeric(19,6) | ANO |  |  |
| 11 | `OdmenaPocetNab` | numeric(19,6) | ANO |  |  |
| 12 | `VyfakturovaneHodiny` | numeric(19,6) | ANO |  |  |
| 13 | `Typ` | varchar(7) | NE |  |  |
| 14 | `VyfakturovaneHodinyKalkulace` | numeric(19,6) | ANO |  |  |
| 15 | `PocetNovychPolozek` | int | ANO |  |  |
| 16 | `PocetVydPopt` | int | ANO |  |  |
| 17 | `VP_KCzaEUR` | numeric(19,6) | NE |  |  |
| 18 | `VP_KCzaKalkHod` | numeric(19,6) | NE |  |  |
| 19 | `VP_KCzaNab` | numeric(19,6) | NE |  |  |
| 20 | `VP_KCzaKartu` | numeric(19,6) | NE |  |  |
| 21 | `VP_KCzaVydPopt` | numeric(19,6) | ANO |  |  |
| 22 | `VP_PrumerOD` | date | ANO |  |  |
| 23 | `VP_PrumerDO` | date | ANO |  |  |
| 24 | `PocetBezKoef` | int | ANO |  |  |
| 25 | `OdmenaZaEUR` | numeric(19,6) | ANO |  |  |
| 26 | `OdmenaHodiny` | numeric(19,6) | ANO |  |  |
| 27 | `OdmenaNoveKarty` | numeric(19,6) | ANO |  |  |
| 28 | `OdmenaCelkem` | numeric(19,6) | ANO |  |  |
| 29 | `OdmenaZaVydPopt` | numeric(19,6) | ANO |  |  |
| 30 | `PrumerZaEUR` | numeric(19,6) | ANO |  |  |
| 31 | `PrumerZaKalkHod` | numeric(19,6) | ANO |  |  |
| 32 | `PrumerZaPocetNab` | numeric(19,6) | ANO |  |  |
| 33 | `PrumerZaKarty` | numeric(19,6) | ANO |  |  |
| 34 | `PrumerCelkem` | numeric(19,6) | ANO |  |  |
| 35 | `PrumerZaVydPopt` | numeric(19,6) | ANO |  |  |
| 36 | `Autor` | nvarchar(126) | ANO | (suser_sname()) |  |
| 37 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 38 | `OdmenaCelkemZaokr` | numeric(27,0) | ANO |  |  |
