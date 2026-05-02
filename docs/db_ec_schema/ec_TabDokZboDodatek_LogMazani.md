# ec_TabDokZboDodatek_LogMazani

**Schema**: dbo · **Cluster**: Other · **Rows**: 26,683 · **Size**: 22.95 MB · **Sloupců**: 98 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `IDHlavicky` | int | ANO |  |  |
| 2 | `FIntrMonthMsg` | int | ANO |  |  |
| 3 | `ZemeUrceni` | nvarchar(2) | ANO |  |  |
| 4 | `RegionUrceniPuvodu` | tinyint | ANO |  |  |
| 5 | `DodaciPodminky` | nvarchar(3) | ANO |  |  |
| 6 | `DD` | tinyint | ANO |  |  |
| 7 | `PovahaTransakce` | tinyint | ANO |  |  |
| 8 | `ZPZ` | nvarchar(2) | ANO |  |  |
| 9 | `ZPZtext` | nvarchar(40) | ANO |  |  |
| 10 | `PoziceZaokrDPHHla` | tinyint | ANO |  |  |
| 11 | `HraniceZaokrDPHHla` | tinyint | ANO |  |  |
| 12 | `ZaokrNaPadesat` | smallint | ANO |  |  |
| 13 | `DatPrijOdeslZbozi` | datetime | ANO |  |  |
| 14 | `DatumTisku` | datetime | ANO |  |  |
| 15 | `Guid` | nchar(32) | ANO |  |  |
| 16 | `Stav` | tinyint | ANO |  |  |
| 17 | `DatumOdeslani` | datetime | ANO |  |  |
| 18 | `DatumPrijetiPVS` | datetime | ANO |  |  |
| 19 | `DatumZpracovani` | datetime | ANO |  |  |
| 20 | `Autor` | nvarchar(128) | ANO |  |  |
| 21 | `DatPorizeni` | datetime | ANO |  |  |
| 22 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 23 | `DatZmeny` | datetime | ANO |  |  |
| 24 | `BlokovaniEditoru` | smallint | ANO |  |  |
| 25 | `FIntrMonthMsgAnoNe` | bit | ANO |  |  |
| 26 | `DatPrijOdeslZbozi_D` | int | ANO |  |  |
| 27 | `DatPrijOdeslZbozi_M` | int | ANO |  |  |
| 28 | `DatPrijOdeslZbozi_Y` | int | ANO |  |  |
| 29 | `DatPrijOdeslZbozi_Q` | int | ANO |  |  |
| 30 | `DatPrijOdeslZbozi_W` | int | ANO |  |  |
| 31 | `DatPrijOdeslZbozi_X` | datetime | ANO |  |  |
| 32 | `DatumOdeslani_D` | int | ANO |  |  |
| 33 | `DatumOdeslani_M` | int | ANO |  |  |
| 34 | `DatumOdeslani_Y` | int | ANO |  |  |
| 35 | `DatumOdeslani_Q` | int | ANO |  |  |
| 36 | `DatumOdeslani_W` | int | ANO |  |  |
| 37 | `DatumOdeslani_X` | datetime | ANO |  |  |
| 38 | `DatumPrijetiPVS_D` | int | ANO |  |  |
| 39 | `DatumPrijetiPVS_M` | int | ANO |  |  |
| 40 | `DatumPrijetiPVS_Y` | int | ANO |  |  |
| 41 | `DatumPrijetiPVS_Q` | int | ANO |  |  |
| 42 | `DatumPrijetiPVS_W` | int | ANO |  |  |
| 43 | `DatumPrijetiPVS_X` | datetime | ANO |  |  |
| 44 | `DatumZpracovani_D` | int | ANO |  |  |
| 45 | `DatumZpracovani_M` | int | ANO |  |  |
| 46 | `DatumZpracovani_Y` | int | ANO |  |  |
| 47 | `DatumZpracovani_Q` | int | ANO |  |  |
| 48 | `DatumZpracovani_W` | int | ANO |  |  |
| 49 | `DatumZpracovani_X` | datetime | ANO |  |  |
| 50 | `DatPorizeni_D` | int | ANO |  |  |
| 51 | `DatPorizeni_M` | int | ANO |  |  |
| 52 | `DatPorizeni_Y` | int | ANO |  |  |
| 53 | `DatPorizeni_Q` | int | ANO |  |  |
| 54 | `DatPorizeni_W` | int | ANO |  |  |
| 55 | `DatPorizeni_X` | datetime | ANO |  |  |
| 56 | `DatZmeny_D` | int | ANO |  |  |
| 57 | `DatZmeny_M` | int | ANO |  |  |
| 58 | `DatZmeny_Y` | int | ANO |  |  |
| 59 | `DatZmeny_Q` | int | ANO |  |  |
| 60 | `DatZmeny_W` | int | ANO |  |  |
| 61 | `DatZmeny_X` | datetime | ANO |  |  |
| 62 | `ID` | int | NE |  |  |
| 63 | `PoziceZaokrDPHTxt` | tinyint | ANO |  |  |
| 64 | `HraniceZaokrDPHTxt` | tinyint | ANO |  |  |
| 65 | `VypocetSumaKcPoZao` | tinyint | ANO |  |  |
| 66 | `ZapoctiStornoDoOdebMnoz` | bit | ANO |  |  |
| 67 | `KoeficientDPH` | bit | ANO |  |  |
| 68 | `DatumSchvaleni` | datetime | ANO |  |  |
| 69 | `DatumSchvaleni_D` | int | ANO |  |  |
| 70 | `DatumSchvaleni_M` | int | ANO |  |  |
| 71 | `DatumSchvaleni_Y` | int | ANO |  |  |
| 72 | `DatumSchvaleni_Q` | int | ANO |  |  |
| 73 | `DatumSchvaleni_W` | int | ANO |  |  |
| 74 | `DatumSchvaleni_X` | datetime | ANO |  |  |
| 75 | `Schvaleno` | bit | ANO |  |  |
| 76 | `StavSkonta` | smallint | ANO |  |  |
| 77 | `PovolitUpravuDPH` | bit | ANO |  |  |
| 78 | `DOBJZapoctiStornoCiDobropis` | bit | ANO |  |  |
| 79 | `Schvalil` | nvarchar(128) | ANO |  |  |
| 80 | `CastkaRPT` | numeric(19,6) | ANO |  |  |
| 81 | `CastkaRPTCM` | numeric(19,6) | ANO |  |  |
| 82 | `PTRU` | bit | ANO |  |  |
| 83 | `PTRUCastka` | numeric(19,6) | ANO |  |  |
| 84 | `PTRUCastkaCM` | numeric(19,6) | ANO |  |  |
| 85 | `IDDokladOprava` | int | ANO |  |  |
| 86 | `RezimKurzuDPHFaktur` | tinyint | ANO |  |  |
| 87 | `Aktivni` | bit | ANO |  |  |
| 88 | `DatumAkceptace` | datetime | ANO |  |  |
| 89 | `Akceptovano` | bit | ANO |  |  |
| 90 | `DatumAkceptace_D` | int | ANO |  |  |
| 91 | `DatumAkceptace_M` | int | ANO |  |  |
| 92 | `DatumAkceptace_Y` | int | ANO |  |  |
| 93 | `DatumAkceptace_Q` | int | ANO |  |  |
| 94 | `DatumAkceptace_W` | int | ANO |  |  |
| 95 | `DatumAkceptace_X` | datetime | ANO |  |  |
| 96 | `JeNovaVetaEditor` | bit | ANO |  |  |
| 97 | `Smazal` | nvarchar(128) | ANO | (suser_sname()) |  |
| 98 | `DatSmazani` | datetime | ANO | (getdate()) |  |
