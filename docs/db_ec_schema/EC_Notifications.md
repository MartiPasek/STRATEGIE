# EC_Notifications

**Schema**: dbo · **Cluster**: Logging · **Rows**: 563,355 · **Size**: 141.64 MB · **Sloupců**: 21 · **FK**: 0 · **Indexů**: 2

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Application` | nvarchar(20) | NE | (N'Centrala') |  |
| 3 | `UserCis` | int | ANO |  |  |
| 4 | `Aktivni` | bit | NE | ((1)) |  |
| 5 | `Title` | nvarchar(200) | NE |  |  |
| 6 | `Message` | nvarchar(MAX) | NE | ('') |  |
| 7 | `Icon` | int | NE | ((0)) |  |
| 8 | `IDDoklad` | int | ANO |  |  |
| 9 | `IDUkol` | int | ANO |  |  |
| 10 | `IDSmernice` | int | ANO |  |  |
| 11 | `DatZobrazeni` | datetime | ANO |  |  |
| 12 | `DatPotvrzeni` | datetime | ANO |  |  |
| 13 | `Autor` | nvarchar(128) | NE | (suser_sname()) |  |
| 14 | `DatPorizeni` | datetime | NE | (getdate()) |  |
| 15 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 16 | `DatZmeny` | datetime | ANO |  |  |
| 17 | `ID_E` | int | ANO |  |  |
| 18 | `ID_Zdroj` | int | ANO |  |  |
| 19 | `TypNotifikace` | int | ANO | ((1)) | 1 = úkol, 2 = obecné jádro, 3 = neotevírat detail, 4 = poznámka, 9 = do dochazky |
| 20 | `ZobrazujNotifikaci` | bit | ANO | ((1)) |  |
| 21 | `NechNotifikaciVPrehledu` | bit | ANO |  |  |

## Indexy

- **PK** `PK_EC_Notifications` (CLUSTERED) — `ID`
- **INDEX** `IK_NOTIFICATION` (NONCLUSTERED) — `Application, Aktivni, Title, Message, Icon, IDDoklad, IDUkol, IDSmernice, DatZobrazeni, DatPotvrzeni, Autor, DatPorizeni, Zmenil, DatZmeny, ID_E, ID_Zdroj, TypNotifikace, ZobrazujNotifikaci, NechNotifikaciVPrehledu, UserCis`
