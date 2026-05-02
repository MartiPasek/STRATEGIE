# EC_TempUkoly

**Schema**: dbo · **Cluster**: Other · **Rows**: 0 · **Size**: 0.00 MB · **Sloupců**: 20 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `IDUkolu` | int | ANO |  |  |
| 3 | `Predmet` | nvarchar(255) | NE |  |  |
| 4 | `TerminZahajeni` | datetime | ANO |  |  |
| 5 | `TerminSplneni` | datetime | ANO |  |  |
| 6 | `DatumZahajeni` | datetime | ANO |  |  |
| 7 | `DatumKontroly` | datetime | ANO |  |  |
| 8 | `DatumDokonceni` | datetime | ANO |  |  |
| 9 | `Stav` | tinyint | NE |  |  |
| 10 | `Priorita` | tinyint | NE |  |  |
| 11 | `HotovoProcent` | smallint | NE |  |  |
| 12 | `Zadavatel` | int | ANO |  |  |
| 13 | `Resitel` | int | ANO |  |  |
| 14 | `Popis` | ntext | ANO |  |  |
| 15 | `BlokovaniEditoru` | smallint | ANO |  |  |
| 16 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 17 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 18 | `DatZmeny` | datetime | ANO |  |  |
| 19 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 20 | `CisloZakazky` | nvarchar(15) | ANO |  |  |

## Indexy

- **PK** `PK__EC_TempUkoly__ID` (CLUSTERED) — `ID`
