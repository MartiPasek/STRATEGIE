# EC_UkolyOpak

**Schema**: dbo · **Cluster**: Other · **Rows**: 352 · **Size**: 2.66 MB · **Sloupců**: 55 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `ID_AktualnihoUkolu` | int | ANO |  |  |
| 3 | `Status` | tinyint | NE | ((0)) |  |
| 4 | `PoznamkaAutora` | ntext | ANO |  |  |
| 5 | `TerminZahajeni` | datetime | ANO | (CONVERT([date],getdate())) |  |
| 6 | `TerminSplneni` | datetime | ANO | (CONVERT([date],getdate())) |  |
| 7 | `Predmet` | nvarchar(255) | ANO | (N'zadny predmet !!!!!!!!!!!!!!!!!!!') |  |
| 8 | `Priorita` | tinyint | NE | ((1)) |  |
| 9 | `Zadavatel` | int | NE | ([dbo].[ec_getuserciszam]()) |  |
| 10 | `Popis` | ntext | ANO |  |  |
| 11 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 12 | `Zacatek` | datetime | ANO | (CONVERT([date],getdate())) |  |
| 13 | `Konec` | datetime | ANO |  |  |
| 14 | `Trvani` | tinyint | NE | ((0)) |  |
| 15 | `TypOpakovani` | tinyint | NE | ((0)) |  |
| 16 | `IntervalOpakovani` | int | NE | ((1)) |  |
| 17 | `DatumZacatek` | datetime | ANO | (CONVERT([date],getdate())) |  |
| 18 | `KonecTyp` | tinyint | ANO | ((0)) |  |
| 19 | `KonecOpakovani` | int | ANO | ((10000)) |  |
| 20 | `KonecDen` | datetime | ANO |  |  |
| 21 | `DenPondeli` | bit | NE | ((0)) |  |
| 22 | `DenUtery` | bit | NE | ((0)) |  |
| 23 | `DenStreda` | bit | NE | ((0)) |  |
| 24 | `DenCtvrtek` | bit | NE | ((0)) |  |
| 25 | `DenPatek` | bit | NE | ((0)) |  |
| 26 | `DenSobota` | bit | NE | ((0)) |  |
| 27 | `DenNedele` | bit | NE | ((0)) |  |
| 28 | `MesicRokDenVMesici` | tinyint | NE | ((1)) |  |
| 29 | `MesicRokInstance` | tinyint | NE | ((0)) |  |
| 30 | `MesicRokMaskaDne` | tinyint | NE | ((0)) |  |
| 31 | `RokMesic` | tinyint | NE | ((1)) |  |
| 32 | `DenTyp` | tinyint | NE | ((0)) |  |
| 33 | `MesicTyp` | tinyint | NE | ((0)) |  |
| 34 | `RokTyp` | tinyint | NE | ((0)) |  |
| 35 | `TextOpak` | nvarchar(160) | NE | (N'!!! nedefinovaný text !!!') |  |
| 36 | `DatPorizeni` | datetime | NE | (CONVERT([date],getdate())) |  |
| 37 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 38 | `DatZmeny` | datetime | ANO |  |  |
| 39 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 40 | `Zamknul` | nvarchar(128) | ANO |  |  |
| 41 | `DatZamceni` | datetime | ANO |  |  |
| 42 | `ID_Cinnosti` | int | ANO |  |  |
| 43 | `Typ` | smallint | ANO |  | null = obecný, 1 = položka mustru |
| 44 | `ID_PredchozihoUkolu` | int | ANO |  |  |
| 45 | `DobaOdPredchoziho` | int | ANO |  |  |
| 46 | `InfoZadavatel` | bit | ANO |  |  |
| 47 | `SeznamResitelu` | nvarchar(400) | ANO |  |  |
| 48 | `SeznamKopie` | nvarchar(400) | ANO |  |  |
| 49 | `DatumZalozeni` | datetime | NE | (CONVERT([date],getdate())) |  |
| 50 | `SeznamResiteluText` | nvarchar(400) | ANO |  |  |
| 51 | `SeznamKopieText` | nvarchar(400) | ANO |  |  |
| 52 | `Popis_bin` | varbinary(MAX) | ANO |  |  |
| 53 | `PotvrdUkol_PoDokonceni` | bit | ANO | ((0)) |  |
| 54 | `NeBlokovatDochZadavatel` | bit | ANO | ((0)) |  |
| 55 | `NeBlokovatDochResitel` | bit | ANO | ((0)) |  |

## Indexy

- **PK** `PK__EC_UkolyOpak__ID` (CLUSTERED) — `ID`
