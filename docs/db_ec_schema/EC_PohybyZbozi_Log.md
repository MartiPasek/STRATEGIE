# EC_PohybyZbozi_Log

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 149,429 · **Size**: 212.04 MB · **Sloupců**: 253 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Log_ID` | int | NE |  |  |
| 2 | `Log_Author` | nvarchar(128) | NE | (suser_name()) |  |
| 3 | `Log_DatPorizeni` | datetime | NE | (getdate()) |  |
| 4 | `Log_SPID` | smallint | ANO | (@@spid) |  |
| 5 | `Log_Location` | nvarchar(128) | ANO |  |  |
| 6 | `Log_Info` | nvarchar(500) | ANO |  |  |
| 7 | `ID` | int | ANO |  |  |
| 8 | `IDZboSklad` | int | ANO |  |  |
| 9 | `IDDoklad` | int | ANO |  |  |
| 10 | `IDOldDoklad` | int | ANO |  |  |
| 11 | `SkupZbo` | nvarchar(3) | ANO |  |  |
| 12 | `RegCis` | nvarchar(30) | ANO |  |  |
| 13 | `Nazev1` | nvarchar(100) | ANO |  |  |
| 14 | `Nazev2` | nvarchar(100) | ANO |  |  |
| 15 | `Nazev3` | nvarchar(100) | ANO |  |  |
| 16 | `Nazev4` | nvarchar(100) | ANO |  |  |
| 17 | `SKP` | nvarchar(50) | ANO |  |  |
| 18 | `NazevSozNa1` | nvarchar(100) | ANO | ('') |  |
| 19 | `NazevSozNa2` | nvarchar(100) | ANO | ('') |  |
| 20 | `NazevSozNa3` | nvarchar(100) | ANO | ('') |  |
| 21 | `Popis4` | nvarchar(100) | ANO | ('') |  |
| 22 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 23 | `IDVozidlo` | int | ANO |  |  |
| 24 | `CisloZam` | int | ANO |  |  |
| 25 | `MJ` | nvarchar(10) | ANO |  |  |
| 26 | `MJEvidence` | nvarchar(10) | ANO |  |  |
| 27 | `PrepMnozstvi` | float | ANO | ((1.0)) |  |
| 28 | `Mena` | nvarchar(3) | ANO |  |  |
| 29 | `Kurz` | numeric(19,6) | ANO | ((1.0)) |  |
| 30 | `JednotkaMeny` | int | ANO | ((1)) |  |
| 31 | `KurzEuro` | numeric(19,6) | ANO | ((0)) |  |
| 32 | `SazbaDPH` | numeric(5,2) | ANO |  |  |
| 33 | `SazbaDPHHlavicky` | numeric(5,2) | ANO |  |  |
| 34 | `SazbaSD` | numeric(19,6) | ANO | ((0.0)) |  |
| 35 | `Mnozstvi` | numeric(19,6) | ANO | ((0.0)) |  |
| 36 | `VraceneMnozstvi` | numeric(19,6) | ANO | ((0.0)) |  |
| 37 | `MnOdebrane` | numeric(19,6) | ANO | ((0.0)) |  |
| 38 | `MnozstviStorno` | numeric(19,6) | ANO | ((0.0)) |  |
| 39 | `MnozstviReal` | numeric(19,6) | ANO | ((0.0)) |  |
| 40 | `MnOdebraneReal` | numeric(19,6) | ANO | ((0.0)) |  |
| 41 | `MnozstviStornoReal` | numeric(19,6) | ANO | ((0.0)) |  |
| 42 | `SlevaSkupZbo` | numeric(5,2) | ANO | ((0.0)) |  |
| 43 | `SlevaZboKmen` | numeric(5,2) | ANO | ((0.0)) |  |
| 44 | `SlevaZboSklad` | numeric(5,2) | ANO | ((0.0)) |  |
| 45 | `SlevaOrg` | numeric(5,2) | ANO | ((0.0)) |  |
| 46 | `SlevaSozNa` | numeric(5,2) | ANO | ((0.0)) |  |
| 47 | `VstupniCena` | tinyint | ANO | ((0)) |  |
| 48 | `JCbezDaniKC` | numeric(19,6) | ANO | ((0.0)) |  |
| 49 | `JCsSDKc` | numeric(19,6) | ANO | ((0.0)) |  |
| 50 | `JCsDPHKc` | numeric(19,6) | ANO | ((0.0)) |  |
| 51 | `JCbezDaniVal` | numeric(19,6) | ANO | ((0.0)) |  |
| 52 | `JCsSDVal` | numeric(19,6) | ANO | ((0.0)) |  |
| 53 | `JCsDPHVal` | numeric(19,6) | ANO | ((0.0)) |  |
| 54 | `JCbezDaniKcPoS` | numeric(19,6) | ANO | ((0.0)) |  |
| 55 | `JCsSDKcPoS` | numeric(19,6) | ANO | ((0.0)) |  |
| 56 | `JCsDPHKcPoS` | numeric(19,6) | ANO | ((0.0)) |  |
| 57 | `JCbezDaniValPoS` | numeric(19,6) | ANO | ((0.0)) |  |
| 58 | `JCsSDValPoS` | numeric(19,6) | ANO | ((0.0)) |  |
| 59 | `JCsDPHValPoS` | numeric(19,6) | ANO | ((0.0)) |  |
| 60 | `CCbezDaniKc` | numeric(19,6) | ANO | ((0.0)) |  |
| 61 | `CCsSDKc` | numeric(19,6) | ANO | ((0.0)) |  |
| 62 | `CCsDPHKc` | numeric(19,6) | ANO | ((0.0)) |  |
| 63 | `CCbezDaniVal` | numeric(19,6) | ANO | ((0.0)) |  |
| 64 | `CCsSDVal` | numeric(19,6) | ANO | ((0.0)) |  |
| 65 | `CCsDPHVal` | numeric(19,6) | ANO | ((0.0)) |  |
| 66 | `CCbezDaniKcPoS` | numeric(19,6) | ANO | ((0.0)) |  |
| 67 | `CCsSDKcPoS` | numeric(19,6) | ANO | ((0.0)) |  |
| 68 | `CCsDPHKcPoS` | numeric(19,6) | ANO | ((0.0)) |  |
| 69 | `CCbezDaniValPoS` | numeric(19,6) | ANO | ((0.0)) |  |
| 70 | `CCsSDValPoS` | numeric(19,6) | ANO | ((0.0)) |  |
| 71 | `CCsDPHValPoS` | numeric(19,6) | ANO | ((0.0)) |  |
| 72 | `CCevid` | numeric(19,6) | ANO | ((0.0)) |  |
| 73 | `CCevidSN` | numeric(19,6) | ANO | ((0.0)) |  |
| 74 | `AltCena` | numeric(19,6) | ANO | ((0.0)) |  |
| 75 | `CCevidPozadovana` | numeric(19,6) | ANO | ((0.0)) |  |
| 76 | `NastaveniSlev` | smallint | ANO | ((4681)) |  |
| 77 | `Poznamka` | ntext | ANO |  |  |
| 78 | `EvMnozstvi` | numeric(19,6) | ANO | ((0.0)) |  |
| 79 | `EvStav` | numeric(19,6) | ANO | ((0.0)) |  |
| 80 | `Obal` | int | ANO |  |  |
| 81 | `CisloNOkruh` | nvarchar(15) | ANO |  |  |
| 82 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 83 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 84 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 85 | `DatZmeny` | datetime | ANO |  |  |
| 86 | `BlokovaniEditoru` | smallint | ANO |  |  |
| 87 | `IDPrikaz` | int | ANO |  |  |
| 88 | `IDOldPolozka` | int | ANO |  |  |
| 89 | `CisloOrg` | int | ANO |  |  |
| 90 | `DruhPohybuZbo` | tinyint | ANO |  |  |
| 91 | `JCZadaneDPHKc` | numeric(19,6) | ANO |  |  |
| 92 | `CCZadaneDPHKc` | numeric(19,6) | ANO |  |  |
| 93 | `JCZadaneDPHKcPoS` | numeric(19,6) | ANO |  |  |
| 94 | `CCZadaneDPHKcPoS` | numeric(19,6) | ANO |  |  |
| 95 | `JCZadaneDPHVal` | numeric(19,6) | ANO |  |  |
| 96 | `CCZadaneDPHVal` | numeric(19,6) | ANO |  |  |
| 97 | `JCZadaneDPHValPoS` | numeric(19,6) | ANO |  |  |
| 98 | `CCZadaneDPHValPoS` | numeric(19,6) | ANO |  |  |
| 99 | `PotvrzDatDod` | datetime | ANO |  |  |
| 100 | `PozadDatDod` | datetime | ANO |  |  |
| 101 | `DokladPrikazu` | int | ANO |  |  |
| 102 | `Hmotnost` | numeric(19,6) | ANO | ((0.0)) |  |
| 103 | `ZemePuvodu` | nvarchar(2) | ANO |  |  |
| 104 | `ZemePreference` | nvarchar(3) | ANO | ('') |  |
| 105 | `IDAkce` | int | ANO |  |  |
| 106 | `StredNaklad` | nvarchar(30) | ANO |  |  |
| 107 | `SkutecneDatReal` | datetime | ANO |  |  |
| 108 | `ZemeOdeslani` | nvarchar(2) | ANO |  |  |
| 109 | `JCDID` | int | ANO |  |  |
| 110 | `IdPolJCD` | int | ANO |  |  |
| 111 | `IdPolNCTS` | int | ANO |  |  |
| 112 | `Lokace` | nvarchar(10) | ANO |  |  |
| 113 | `MnozstviObalu` | int | ANO | ((0.0)) |  |
| 114 | `KodBaleni` | nvarchar(8) | ANO | ('') |  |
| 115 | `CisloEUR1` | nvarchar(35) | ANO |  |  |
| 116 | `CisloLicence` | nvarchar(28) | ANO | ('') |  |
| 117 | `CisloJCD` | nvarchar(23) | ANO |  |  |
| 118 | `PorCisloPolJCD` | int | ANO |  |  |
| 119 | `DatumProjednaniJCD` | datetime | ANO |  |  |
| 120 | `DodaciPodminka` | nvarchar(3) | ANO |  |  |
| 121 | `KurzJCD` | numeric(19,6) | ANO |  |  |
| 122 | `HmotnostBrutto` | numeric(19,6) | ANO | ((0.0)) |  |
| 123 | `Lhuta` | datetime | ANO |  |  |
| 124 | `PCDCislo` | nvarchar(23) | ANO |  |  |
| 125 | `PCDPorCisloPol` | int | ANO |  |  |
| 126 | `PCDDatum` | datetime | ANO |  |  |
| 127 | `BarCode` | nvarchar(50) | ANO |  |  |
| 128 | `TypVyrobnihoDokladu` | tinyint | ANO |  |  |
| 129 | `KJKontrolovat` | bit | ANO | ((0)) |  |
| 130 | `KJSkontrolovano` | bit | ANO | ((0)) |  |
| 131 | `PocetZmetku` | numeric(19,6) | ANO | ((0.0)) |  |
| 132 | `TerminSlevaProc` | numeric(5,2) | ANO | ((0.0)) |  |
| 133 | `TerminSlevaNazev` | nvarchar(50) | ANO | ('') |  |
| 134 | `SlevaCastka` | numeric(19,6) | ANO | ((0.0)) |  |
| 135 | `IdUmisteni` | int | ANO |  |  |
| 136 | `FMonthMsgPohyby` | int | ANO |  |  |
| 137 | `SkutecnaSazbaDPH` | numeric(5,2) | ANO |  |  |
| 138 | `SlevaPolozkyKc` | numeric(20,6) | ANO |  |  |
| 139 | `CCevidUcto` | numeric(19,6) | NE |  |  |
| 140 | `CCevidSNDruh` | numeric(19,6) | ANO |  |  |
| 141 | `Prevedeno` | bit | ANO |  |  |
| 142 | `JeObal` | bit | ANO |  |  |
| 143 | `DatPorizeni_D` | int | ANO |  |  |
| 144 | `DatPorizeni_M` | int | ANO |  |  |
| 145 | `DatPorizeni_Y` | int | ANO |  |  |
| 146 | `DatPorizeni_Q` | int | ANO |  |  |
| 147 | `DatPorizeni_W` | int | ANO |  |  |
| 148 | `DatPorizeni_X` | datetime | ANO |  |  |
| 149 | `DatZmeny_D` | int | ANO |  |  |
| 150 | `DatZmeny_M` | int | ANO |  |  |
| 151 | `DatZmeny_Y` | int | ANO |  |  |
| 152 | `DatZmeny_Q` | int | ANO |  |  |
| 153 | `DatZmeny_W` | int | ANO |  |  |
| 154 | `DatZmeny_X` | datetime | ANO |  |  |
| 155 | `MnozstviDruhove` | numeric(19,6) | ANO |  |  |
| 156 | `MnozstviZvyseni` | numeric(19,6) | ANO |  |  |
| 157 | `MnozstviSnizeni` | numeric(19,6) | ANO |  |  |
| 158 | `CCsDPHKcPoSDruhova` | numeric(19,6) | ANO |  |  |
| 159 | `CCsDPHKcPoSZvyseni` | numeric(19,6) | ANO |  |  |
| 160 | `CCsDPHKcPoSSnizeni` | numeric(19,6) | ANO |  |  |
| 161 | `CCsDPHValPoSDruhova` | numeric(19,6) | ANO |  |  |
| 162 | `CCevidDruhova` | numeric(19,6) | ANO |  |  |
| 163 | `CCevidZvyseni` | numeric(19,6) | ANO |  |  |
| 164 | `CCevidSnizeni` | numeric(19,6) | ANO |  |  |
| 165 | `PotvrzDatDod_D` | int | ANO |  |  |
| 166 | `PotvrzDatDod_M` | int | ANO |  |  |
| 167 | `PotvrzDatDod_Y` | int | ANO |  |  |
| 168 | `PotvrzDatDod_Q` | int | ANO |  |  |
| 169 | `PotvrzDatDod_W` | int | ANO |  |  |
| 170 | `PotvrzDatDod_X` | datetime | ANO |  |  |
| 171 | `PozadDatDod_D` | int | ANO |  |  |
| 172 | `PozadDatDod_M` | int | ANO |  |  |
| 173 | `PozadDatDod_Y` | int | ANO |  |  |
| 174 | `PozadDatDod_Q` | int | ANO |  |  |
| 175 | `PozadDatDod_W` | int | ANO |  |  |
| 176 | `PozadDatDod_X` | datetime | ANO |  |  |
| 177 | `SkutecneDatReal_D` | int | ANO |  |  |
| 178 | `SkutecneDatReal_M` | int | ANO |  |  |
| 179 | `SkutecneDatReal_Y` | int | ANO |  |  |
| 180 | `SkutecneDatReal_Q` | int | ANO |  |  |
| 181 | `SkutecneDatReal_W` | int | ANO |  |  |
| 182 | `SkutecneDatReal_X` | datetime | ANO |  |  |
| 183 | `CCsSDKcPoSDruhova` | numeric(19,6) | ANO |  |  |
| 184 | `CCsSDKcPoSZvyseni` | numeric(19,6) | ANO |  |  |
| 185 | `CCsSDKcPoSSnizeni` | numeric(19,6) | ANO |  |  |
| 186 | `CCsSDValPoSDruhova` | numeric(19,6) | ANO |  |  |
| 187 | `DatumProjednaniJCD_D` | int | ANO |  |  |
| 188 | `DatumProjednaniJCD_M` | int | ANO |  |  |
| 189 | `DatumProjednaniJCD_Y` | int | ANO |  |  |
| 190 | `DatumProjednaniJCD_Q` | int | ANO |  |  |
| 191 | `DatumProjednaniJCD_W` | int | ANO |  |  |
| 192 | `DatumProjednaniJCD_X` | datetime | ANO |  |  |
| 193 | `Lhuta_D` | int | ANO |  |  |
| 194 | `Lhuta_M` | int | ANO |  |  |
| 195 | `Lhuta_Y` | int | ANO |  |  |
| 196 | `Lhuta_Q` | int | ANO |  |  |
| 197 | `Lhuta_W` | int | ANO |  |  |
| 198 | `Lhuta_X` | datetime | ANO |  |  |
| 199 | `PCDDatum_D` | int | ANO |  |  |
| 200 | `PCDDatum_M` | int | ANO |  |  |
| 201 | `PCDDatum_Y` | int | ANO |  |  |
| 202 | `PCDDatum_Q` | int | ANO |  |  |
| 203 | `PCDDatum_W` | int | ANO |  |  |
| 204 | `PCDDatum_X` | datetime | ANO |  |  |
| 205 | `ZamknoutCenu` | bit | ANO | ((0)) |  |
| 206 | `CCbezDaniKcPoSDruhova` | numeric(19,6) | ANO |  |  |
| 207 | `CCbezDaniKcPoSZvyseni` | numeric(19,6) | ANO |  |  |
| 208 | `CCbezDaniKcPoSSnizeni` | numeric(19,6) | ANO |  |  |
| 209 | `CCbezDaniValPoSDruhova` | numeric(19,6) | ANO |  |  |
| 210 | `JCevid` | numeric(19,6) | ANO |  |  |
| 211 | `JCevidSN` | numeric(19,6) | ANO |  |  |
| 212 | `SazbaDPHproPDP` | numeric(5,2) | ANO |  |  |
| 213 | `IDOZTxtPol` | int | ANO |  |  |
| 214 | `Poradi` | int | ANO |  |  |
| 215 | `IDZakazModif` | int | ANO |  |  |
| 216 | `SamoVyDPHZaklad` | numeric(19,6) | ANO |  |  |
| 217 | `SamoVyDPHCastka` | numeric(19,6) | ANO |  |  |
| 218 | `SamoVyDPHZakladHM` | numeric(19,6) | ANO |  |  |
| 219 | `SamoVyDPHCastkaHM` | numeric(19,6) | ANO |  |  |
| 220 | `MnozOdebrane` | numeric(19,6) | ANO | ((0.0)) |  |
| 221 | `IDCiloveTxtPol` | int | ANO |  |  |
| 222 | `MnozstviRPT` | numeric(19,6) | ANO | ((0)) |  |
| 223 | `MJKV` | int | ANO |  |  |
| 224 | `MnozstviKV` | numeric(19,6) | ANO | ((0.0)) |  |
| 225 | `DruhSazbyDPH` | tinyint | ANO |  |  |
| 226 | `SamoVyDPHRucneZadano` | bit | ANO | ((0)) |  |
| 227 | `RezimPDP` | bit | ANO |  |  |
| 228 | `IDKodPDP` | int | ANO |  |  |
| 229 | `IDDanovyKlic` | int | ANO |  |  |
| 230 | `JCbezDaniKcPoSDruhova` | numeric(19,6) | ANO |  |  |
| 231 | `JCsDPHKcPoSDruhova` | numeric(19,6) | ANO |  |  |
| 232 | `JCbezDaniValPoSDruhova` | numeric(19,6) | ANO |  |  |
| 233 | `JCsDPHValPoSDruhova` | numeric(19,6) | ANO |  |  |
| 234 | `EET_dic_poverujiciho` | nvarchar(12) | ANO |  |  |
| 235 | `DruhEET` | tinyint | ANO | ((1)) |  |
| 236 | `Zisk` | numeric(19,6) | ANO |  |  |
| 237 | `Marze` | numeric(5,2) | ANO |  |  |
| 238 | `ObchPrirazka` | numeric(19,6) | ANO |  |  |
| 239 | `PlZisk` | numeric(19,6) | ANO |  |  |
| 240 | `PlMarze` | numeric(5,2) | ANO |  |  |
| 241 | `PlObchPrirazka` | numeric(19,6) | ANO |  |  |
| 242 | `ZdrojNC` | tinyint | ANO |  |  |
| 243 | `ZdrojNCSl` | tinyint | ANO |  |  |
| 244 | `HraniceMarze` | numeric(5,2) | ANO |  |  |
| 245 | `NCMarze` | numeric(19,6) | ANO | ((0.0)) |  |
| 246 | `PomerKoef` | numeric(19,6) | ANO |  |  |
| 247 | `JeNovaVetaEditor` | bit | ANO | ((0)) |  |
| 248 | `JeSN` | bit | ANO | ((0)) |  |
| 249 | `SplnenoPol` | bit | ANO | ((0)) |  |
| 250 | `SplnenoHlava` | bit | ANO | ((0)) |  |
| 251 | `Splneno` | bit | ANO |  |  |
| 252 | `PouzitoMajetek` | bit | ANO | ((0)) |  |
| 253 | `PouzitoSklad` | bit | ANO | ((0)) |  |

## Indexy

- **PK** `PK_EC_PohybyZbozi_Log` (CLUSTERED) — `Log_ID`
