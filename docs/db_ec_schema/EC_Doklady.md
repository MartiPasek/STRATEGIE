# EC_Doklady

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 47 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `DruhPohybuZbo` | tinyint | NE |  |  |
| 3 | `RadaDokladu` | nvarchar(3) | NE |  |  |
| 4 | `PoradoveCislo` | int | NE |  |  |
| 5 | `StredNaklad` | nvarchar(30) | ANO |  |  |
| 6 | `CisloOrg` | int | ANO |  |  |
| 7 | `Prijemce` | int | ANO |  |  |
| 8 | `MistoUrceni` | int | ANO |  |  |
| 9 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 10 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 11 | `DatPorizeniSkut` | datetime | NE | (getdate()) |  |
| 12 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 13 | `DatZmeny` | datetime | ANO |  |  |
| 14 | `DatRealizace` | datetime | ANO |  |  |
| 15 | `Splatnost` | datetime | ANO |  |  |
| 16 | `DatumDoruceni` | datetime | ANO |  |  |
| 17 | `SazbaDPH` | numeric(5,2) | ANO |  |  |
| 18 | `FormaDopravy` | nvarchar(30) | ANO |  |  |
| 19 | `Poznamka` | ntext | ANO |  |  |
| 20 | `Text1` | ntext | ANO |  |  |
| 21 | `Text2` | ntext | ANO |  |  |
| 22 | `Text3` | ntext | ANO |  |  |
| 23 | `BlokovaniEditoru` | smallint | ANO |  |  |
| 24 | `NOkruhCislo` | nvarchar(15) | ANO |  |  |
| 25 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 26 | `Mena` | nvarchar(3) | ANO |  |  |
| 27 | `DatumKurzu` | datetime | ANO |  |  |
| 28 | `Kurz` | numeric(19,6) | NE | ((1.0)) |  |
| 29 | `JednotkaMeny` | int | NE | ((1)) |  |
| 30 | `KurzEuro` | numeric(19,6) | NE | ((0)) |  |
| 31 | `VstupniCena` | tinyint | NE | ((0)) |  |
| 32 | `Sleva` | numeric(19,6) | NE | ((0.0)) |  |
| 33 | `Stav` | tinyint | ANO |  |  |
| 34 | `Nazev` | nvarchar(50) | ANO |  |  |
| 35 | `PopisDodavky` | nvarchar(40) | ANO |  |  |
| 36 | `TerminDodavky` | nvarchar(20) | ANO |  |  |
| 37 | `NavaznyDoklad` | int | ANO |  |  |
| 38 | `IDBankSpoj` | int | ANO |  |  |
| 39 | `CisloZam` | int | ANO |  |  |
| 40 | `DodFak` | nvarchar(20) | NE | ('') |  |
| 41 | `NavaznaObjednavka` | nvarchar(30) | NE | ('') |  |
| 42 | `Splneno` | bit | NE | ((0)) |  |
| 43 | `TiskovyForm` | int | ANO |  |  |
| 44 | `SumaKcBezDPH` | numeric(19,6) | NE | ((0.0)) |  |
| 45 | `SumaValBezDPH` | numeric(19,6) | NE | ((0.0)) |  |
| 46 | `KontaktZam` | int | ANO |  |  |
| 47 | `KontaktOsoba` | int | ANO |  |  |

## Indexy

- **PK** `PK_EC_Doklady` (CLUSTERED) — `ID`
