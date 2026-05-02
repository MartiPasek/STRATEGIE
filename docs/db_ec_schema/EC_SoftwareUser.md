# EC_SoftwareUser

**Schema**: dbo · **Cluster**: Other · **Rows**: 164 · **Size**: 0.20 MB · **Sloupců**: 25 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `ID` | int | NE |  |  |
| 2 | `Software` | int | NE |  |  |
| 3 | `Aktivni` | bit | NE | ((1)) |  |
| 4 | `User` | int | NE |  |  |
| 5 | `Developer` | bit | NE | ((0)) |  |
| 6 | `CanUpdate` | bit | ANO | ((1)) |  |
| 7 | `ModeUpdate` | tinyint | ANO |  |  |
| 8 | `ModeUpdateText` | varchar(12) | ANO |  |  |
| 9 | `ForcedVersion` | int | ANO |  |  |
| 10 | `LastVersion` | int | ANO |  |  |
| 11 | `DateOfLastUpdate` | datetime | ANO |  |  |
| 12 | `PreviousVersion` | int | ANO |  |  |
| 13 | `DateOfPreviousUpdate` | datetime | ANO |  |  |
| 14 | `DateOfLastLogin` | datetime | ANO |  |  |
| 15 | `TT_Conn_Enable` | bit | ANO | ((1)) |  |
| 16 | `OfflineMode` | int | NE | ((0)) |  |
| 17 | `Author` | nvarchar(128) | NE | (suser_sname()) |  |
| 18 | `CreationDate` | datetime | NE | (getdate()) |  |
| 19 | `Changed` | nvarchar(128) | ANO |  |  |
| 20 | `DateChanges` | datetime | ANO |  |  |
| 21 | `UpdateVersion` | int | ANO | (NULL) | požadovaná verze aplikace na kterou se má uskutečnit update uživatele |
| 22 | `StayVersion` | int | ANO | (NULL) |  |
| 23 | `UkazujChybyProcedur` | bit | NE | ((0)) |  |
| 24 | `UserChangedVersion` | bit | ANO | ((0)) |  |
| 25 | `MD5_LastUserChangedVersion` | nvarchar(1000) | ANO |  |  |

## Indexy

- **PK** `PK_EC_SoftwareUser` (CLUSTERED) — `ID`
