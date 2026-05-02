# EC_IAP_TabZakazka

**Schema**: dbo · **Cluster**: Other · **Rows**: 12,052 · **Size**: 6.98 MB · **Sloupců**: 73 · **FK**: 0 · **Indexů**: 0

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `CisloZakazky` | nvarchar(15) | NE |  |  |
| 3 | `Nazev` | nvarchar(100) | NE |  |  |
| 4 | `DruhyNazev` | nvarchar(100) | NE |  |  |
| 5 | `Rada` | nvarchar(3) | ANO |  |  |
| 6 | `Prijemce` | int | ANO |  |  |
| 7 | `PrijemceMU` | int | ANO |  |  |
| 8 | `Zadavatel` | int | ANO |  |  |
| 9 | `Zodpovida` | int | ANO |  |  |
| 10 | `KontaktOsoba` | int | ANO |  |  |
| 11 | `Stredisko` | nvarchar(30) | ANO |  |  |
| 12 | `DatumStartPlan` | datetime | ANO |  |  |
| 13 | `DatumStartReal` | datetime | ANO |  |  |
| 14 | `DatumKonecPlan` | datetime | ANO |  |  |
| 15 | `DatumKonecReal` | datetime | ANO |  |  |
| 16 | `Ukonceno` | tinyint | NE |  |  |
| 17 | `Stav` | nvarchar(15) | NE |  |  |
| 18 | `Priorita` | nvarchar(10) | NE |  |  |
| 19 | `Identifikator` | nvarchar(15) | NE |  |  |
| 20 | `CisloObjednavky` | nvarchar(30) | NE |  |  |
| 21 | `CisloNabidky` | nvarchar(30) | NE |  |  |
| 22 | `CisloSmlouvy` | nvarchar(30) | NE |  |  |
| 23 | `Upozorneni` | nvarchar(255) | NE |  |  |
| 24 | `NavaznaZak` | nvarchar(15) | ANO |  |  |
| 25 | `NadrizenaZak` | nvarchar(15) | ANO |  |  |
| 26 | `VynosPlan` | numeric(19,6) | NE |  |  |
| 27 | `ZakKalCislo` | int | ANO |  |  |
| 28 | `GenIDKonJed` | int | ANO |  |  |
| 29 | `JeProjekt` | bit | NE |  |  |
| 30 | `JeServis` | bit | NE |  |  |
| 31 | `VerejnaZakazka` | bit | NE |  |  |
| 32 | `Poznamka` | ntext | ANO |  |  |
| 33 | `Autor` | nvarchar(128) | NE |  |  |
| 34 | `DatPorizeni` | datetime | NE |  |  |
| 35 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 36 | `DatZmeny` | datetime | ANO |  |  |
| 37 | `BlokovaniEditoru` | smallint | ANO |  |  |
| 38 | `DatumStartPlan_D` | int | ANO |  |  |
| 39 | `DatumStartPlan_M` | int | ANO |  |  |
| 40 | `DatumStartPlan_Y` | int | ANO |  |  |
| 41 | `DatumStartPlan_Q` | int | ANO |  |  |
| 42 | `DatumStartPlan_W` | int | ANO |  |  |
| 43 | `DatumStartPlan_X` | datetime | ANO |  |  |
| 44 | `DatumStartReal_D` | int | ANO |  |  |
| 45 | `DatumStartReal_M` | int | ANO |  |  |
| 46 | `DatumStartReal_Y` | int | ANO |  |  |
| 47 | `DatumStartReal_Q` | int | ANO |  |  |
| 48 | `DatumStartReal_W` | int | ANO |  |  |
| 49 | `DatumStartReal_X` | datetime | ANO |  |  |
| 50 | `DatumKonecPlan_D` | int | ANO |  |  |
| 51 | `DatumKonecPlan_M` | int | ANO |  |  |
| 52 | `DatumKonecPlan_Y` | int | ANO |  |  |
| 53 | `DatumKonecPlan_Q` | int | ANO |  |  |
| 54 | `DatumKonecPlan_W` | int | ANO |  |  |
| 55 | `DatumKonecPlan_X` | datetime | ANO |  |  |
| 56 | `DatumKonecReal_D` | int | ANO |  |  |
| 57 | `DatumKonecReal_M` | int | ANO |  |  |
| 58 | `DatumKonecReal_Y` | int | ANO |  |  |
| 59 | `DatumKonecReal_Q` | int | ANO |  |  |
| 60 | `DatumKonecReal_W` | int | ANO |  |  |
| 61 | `DatumKonecReal_X` | datetime | ANO |  |  |
| 62 | `DatPorizeni_D` | int | ANO |  |  |
| 63 | `DatPorizeni_M` | int | ANO |  |  |
| 64 | `DatPorizeni_Y` | int | ANO |  |  |
| 65 | `DatPorizeni_Q` | int | ANO |  |  |
| 66 | `DatPorizeni_W` | int | ANO |  |  |
| 67 | `DatPorizeni_X` | datetime | ANO |  |  |
| 68 | `DatZmeny_D` | int | ANO |  |  |
| 69 | `DatZmeny_M` | int | ANO |  |  |
| 70 | `DatZmeny_Y` | int | ANO |  |  |
| 71 | `DatZmeny_Q` | int | ANO |  |  |
| 72 | `DatZmeny_W` | int | ANO |  |  |
| 73 | `DatZmeny_X` | datetime | ANO |  |  |
