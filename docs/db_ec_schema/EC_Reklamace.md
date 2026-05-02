# EC_Reklamace

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 283 · **Size**: 0.94 MB · **Sloupců**: 46 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Typ` | tinyint | ANO |  |  |
| 3 | `TypText` | varchar(8) | NE |  |  |
| 4 | `UzivTyp` | tinyint | ANO | ((0)) |  |
| 5 | `UzivTypText` | varchar(10) | NE |  |  |
| 6 | `Stav` | tinyint | NE | ((0)) |  |
| 7 | `StavText` | varchar(10) | ANO |  |  |
| 8 | `Archiv` | int | NE |  |  |
| 9 | `PoradCisRek` | nvarchar(6) | ANO |  |  |
| 10 | `Nazev` | nvarchar(255) | ANO | (N'NOVÁ') |  |
| 11 | `PoradCisObj` | int | ANO |  |  |
| 12 | `CisloOrg` | int | ANO |  | cislo organizace z vydané objednávky |
| 13 | `CisloKontaktOrg` | int | ANO |  |  |
| 14 | `CisloZakazky` | nvarchar(200) | ANO |  |  |
| 15 | `ZakazkaOrg` | nvarchar(128) | ANO |  |  |
| 16 | `ZakazkaZodOsb` | nvarchar(128) | ANO |  |  |
| 17 | `IDDoklad` | int | ANO |  | pořadové číslo z tabdokladyzbozi |
| 18 | `CisFakNavazDok` | nvarchar(200) | ANO |  |  |
| 19 | `DodaciList` | nvarchar(100) | ANO |  |  |
| 20 | `ExtCisReklamace` | nvarchar(100) | ANO |  |  |
| 21 | `Zjisteno` | datetime | ANO |  |  |
| 22 | `Zjisteno_X` | datetime | ANO |  |  |
| 23 | `Potvrzeno` | datetime | ANO |  |  |
| 24 | `TerminDodavatele` | datetime | ANO |  |  |
| 25 | `VyresitDo` | datetime | ANO |  |  |
| 26 | `Vyreseno` | datetime | ANO |  |  |
| 27 | `PopisNeshody` | ntext | ANO |  |  |
| 28 | `Pricina` | ntext | ANO |  |  |
| 29 | `ZpusobOdstraneni` | ntext | ANO |  |  |
| 30 | `NapravnaOpatreni` | ntext | ANO |  |  |
| 31 | `Opatreni` | int | ANO |  |  |
| 32 | `Poznamka` | ntext | ANO |  |  |
| 33 | `Pristupnost` | tinyint | NE | ((0)) |  |
| 34 | `PristupnostText` | varchar(7) | ANO |  |  |
| 35 | `Jazyk` | nvarchar(2) | ANO |  |  |
| 36 | `TextPredPolozkami` | ntext | ANO |  |  |
| 37 | `TextZaPolozkami` | ntext | ANO |  |  |
| 38 | `ZodOsobaCislo` | int | ANO |  |  |
| 39 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 40 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 41 | `DatPorizeni_X` | datetime | ANO |  |  |
| 42 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 43 | `DatZmeny` | datetime | ANO |  |  |
| 44 | `RadaDokladu` | varchar(3) | NE |  |  |
| 45 | `splneno` | bit | ANO | ((0)) |  |
| 46 | `NakladyNaReseni` | decimal(10,2) | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_Reklamace` (CLUSTERED) — `ID`
