# EC_DokladyZbozi_Log

**Schema**: dbo · **Cluster**: Warehouse · **Rows**: 231,842 · **Size**: 252.36 MB · **Sloupců**: 306 · **FK**: 0 · **Indexů**: 1

## Sloupce

| # | Název | Typ | NULL | Default | Popis |
|---|-------|-----|------|---------|-------|
| 1 | `Log_ID` | int | NE |  |  |
| 2 | `Log_Author` | nvarchar(128) | ANO | (suser_name()) |  |
| 3 | `Log_DatPorizeni` | datetime | ANO | (getdate()) |  |
| 4 | `Log_SPID` | smallint | ANO | (@@spid) |  |
| 5 | `Log_Location` | nvarchar(128) | ANO |  |  |
| 6 | `Log_Info` | nvarchar(500) | ANO |  |  |
| 7 | `ID` | int | ANO |  |  |
| 8 | `DruhPohybuZbo` | tinyint | ANO |  |  |
| 9 | `DruhPohybuPrevod` | tinyint | ANO |  |  |
| 10 | `IDSklad` | nvarchar(30) | ANO |  |  |
| 11 | `RadaDokladu` | nvarchar(3) | ANO |  |  |
| 12 | `PoradoveCislo` | int | ANO |  |  |
| 13 | `StredNaklad` | nvarchar(30) | ANO |  |  |
| 14 | `StredVynos` | nvarchar(30) | ANO |  |  |
| 15 | `IdSkladPrevodu` | nvarchar(30) | ANO |  |  |
| 16 | `TypPrevodky` | nvarchar(3) | ANO |  |  |
| 17 | `CisloOrg` | int | ANO |  |  |
| 18 | `DIC` | nvarchar(15) | ANO |  |  |
| 19 | `Organizace2` | int | ANO |  |  |
| 20 | `Prijemce` | int | ANO |  |  |
| 21 | `MistoUrceni` | int | ANO |  |  |
| 22 | `DatPorizeni` | datetime | ANO | (getdate()) |  |
| 23 | `Autor` | nvarchar(128) | ANO | (suser_sname()) |  |
| 24 | `DatPorizeniSkut` | datetime | ANO | (getdate()) |  |
| 25 | `Zmenil` | nvarchar(128) | ANO |  |  |
| 26 | `DatZmeny` | datetime | ANO |  |  |
| 27 | `DatPovinnostiFa` | datetime | ANO |  |  |
| 28 | `DatRealizace` | datetime | ANO |  |  |
| 29 | `DatUctovani` | datetime | ANO |  |  |
| 30 | `SplatnoPocitatOd` | tinyint | ANO | ((0)) |  |
| 31 | `Splatnost` | datetime | ANO |  |  |
| 32 | `DatumSplatnoRPT` | datetime | ANO |  |  |
| 33 | `DUZP` | datetime | ANO |  |  |
| 34 | `DatumDoruceni` | datetime | ANO |  |  |
| 35 | `NabidkaCenik` | int | ANO | ((0)) |  |
| 36 | `Obdobi` | int | ANO |  |  |
| 37 | `UKod` | int | ANO |  |  |
| 38 | `SazbaDPH` | numeric(5,2) | ANO |  |  |
| 39 | `DruhSazbyDPH` | tinyint | ANO |  |  |
| 40 | `ZemeDPH` | nvarchar(3) | ANO |  |  |
| 41 | `SazbaSD` | numeric(19,6) | ANO | ((0.0)) |  |
| 42 | `FormaUhrady` | nvarchar(30) | ANO |  |  |
| 43 | `FormaDopravy` | nvarchar(30) | ANO |  |  |
| 44 | `KonstSymbol` | nvarchar(10) | ANO |  |  |
| 45 | `SpecifickySymbol` | nvarchar(10) | ANO | ('') |  |
| 46 | `Poznamka` | ntext | ANO |  |  |
| 47 | `Text1` | ntext | ANO |  |  |
| 48 | `Text2` | ntext | ANO |  |  |
| 49 | `Text3` | ntext | ANO |  |  |
| 50 | `BlokovaniEditoru` | smallint | ANO |  |  |
| 51 | `NOkruhCislo` | nvarchar(15) | ANO |  |  |
| 52 | `CisloZakazky` | nvarchar(15) | ANO |  |  |
| 53 | `Mena` | nvarchar(3) | ANO |  |  |
| 54 | `DatumKurzu` | datetime | ANO |  |  |
| 55 | `Kurz` | numeric(19,6) | ANO | ((1.0)) |  |
| 56 | `JednotkaMeny` | int | ANO | ((1)) |  |
| 57 | `KurzEuro` | numeric(19,6) | ANO | ((0)) |  |
| 58 | `VstupniCena` | tinyint | ANO | ((0)) |  |
| 59 | `Sleva` | numeric(19,6) | ANO | ((0.0)) |  |
| 60 | `Stav` | tinyint | ANO |  |  |
| 61 | `Nazev` | nvarchar(50) | ANO |  |  |
| 62 | `Code` | nvarchar(20) | ANO |  |  |
| 63 | `DoprDispo` | nvarchar(20) | ANO |  |  |
| 64 | `PopisDodavky` | nvarchar(40) | ANO |  |  |
| 65 | `TerminDodavky` | nvarchar(20) | ANO |  |  |
| 66 | `Puvod` | nvarchar(20) | ANO |  |  |
| 67 | `CisReferatu` | nvarchar(20) | ANO |  |  |
| 68 | `Referat` | nvarchar(20) | ANO |  |  |
| 69 | `SumaKc` | numeric(19,6) | ANO | ((0.0)) |  |
| 70 | `Zaloha` | numeric(19,6) | ANO | ((0.0)) |  |
| 71 | `ZaokrouhleniFak` | smallint | ANO | ((2)) |  |
| 72 | `ZaokrouhleniFakVal` | smallint | ANO | ((2)) |  |
| 73 | `CastkaZaoValDoKc` | numeric(19,6) | ANO | ((0.0)) |  |
| 74 | `PomCislo` | nvarchar(15) | ANO | ('') |  |
| 75 | `NavaznyDoklad` | int | ANO |  |  |
| 76 | `NavaznyDobropis` | int | ANO |  |  |
| 77 | `DatUhrady` | datetime | ANO |  |  |
| 78 | `SumaUhrad` | numeric(19,6) | ANO | ((0.0)) |  |
| 79 | `SumaVystavenychPlataku` | numeric(19,6) | ANO | ((0.0)) |  |
| 80 | `IDPrikaz` | int | ANO |  |  |
| 81 | `IDBankSpoj` | int | ANO |  |  |
| 82 | `IDStazka` | int | ANO |  |  |
| 83 | `IDVozidlo` | int | ANO |  |  |
| 84 | `CisloZam` | int | ANO |  |  |
| 85 | `EcCelkemDokl` | numeric(19,6) | ANO | ((0.0)) |  |
| 86 | `EcCelkemDoklUcto` | numeric(19,6) | ANO | ((0.0)) |  |
| 87 | `SNCelkemDokl` | numeric(19,6) | ANO | ((0.0)) |  |
| 88 | `DodFak` | nvarchar(20) | ANO | ('') |  |
| 89 | `DodFakKV` | nvarchar(60) | ANO | ('') |  |
| 90 | `ZdrojCisKV` | tinyint | ANO | ((0)) |  |
| 91 | `NavaznaObjednavka` | nvarchar(30) | ANO | ('') |  |
| 92 | `Splneno` | bit | ANO | ((0)) |  |
| 93 | `DatumMixu` | datetime | ANO |  |  |
| 94 | `IDPosta` | int | ANO |  |  |
| 95 | `NastaveniSlev` | smallint | ANO | ((0)) |  |
| 96 | `SumaVal` | numeric(19,6) | ANO | ((0.0)) |  |
| 97 | `ZalohaVal` | numeric(19,6) | ANO | ((0.0)) |  |
| 98 | `ZalohaDanKurz` | numeric(19,6) | ANO | ((0.0)) |  |
| 99 | `StavRezervace` | nchar(1) | ANO | (N' ') |  |
| 100 | `Modul` | tinyint | ANO | ((0)) |  |
| 101 | `HlidanyDoklad` | nchar(1) | ANO | (N'N') |  |
| 102 | `TiskovyForm` | int | ANO |  |  |
| 103 | `StornoDoklad` | int | ANO |  |  |
| 104 | `OpravnyDoklad` | bit | ANO | ((0)) |  |
| 105 | `OpravDanDoklad` | bit | ANO | ((0)) |  |
| 106 | `ZadanaCastkaZaoKc` | numeric(19,6) | ANO | ((0.0)) |  |
| 107 | `ZadanaCastkaZaoVal` | numeric(19,6) | ANO | ((0.0)) |  |
| 108 | `SumaKcBezDPH` | numeric(19,6) | ANO | ((0.0)) |  |
| 109 | `StavPrevodu` | smallint | ANO | ((0)) |  |
| 110 | `IDJCD` | int | ANO |  |  |
| 111 | `SumaValBezDPH` | numeric(19,6) | ANO | ((0.0)) |  |
| 112 | `KontaktZam` | int | ANO |  |  |
| 113 | `JeToZaloha` | bit | ANO | ((0)) |  |
| 114 | `RealizacniFak` | bit | ANO | ((0)) |  |
| 115 | `IdObdobiStavu` | int | ANO |  |  |
| 116 | `KontaktOsoba` | int | ANO |  |  |
| 117 | `Nabidka` | int | ANO |  |  |
| 118 | `PoziceZaokrDPH` | tinyint | ANO | ((2)) |  |
| 119 | `HraniceZaokrDPH` | tinyint | ANO | ((2)) |  |
| 120 | `ZaokrDPHMalaCisla` | tinyint | ANO | ((0)) |  |
| 121 | `ZaokrDPHvaluty` | tinyint | ANO | ((0)) |  |
| 122 | `IDstin` | int | ANO |  |  |
| 123 | `Rezim` | nvarchar(4) | ANO |  |  |
| 124 | `CSCD` | bit | ANO | ((0)) |  |
| 125 | `SamoVyDICDPH` | nvarchar(15) | ANO |  |  |
| 126 | `SamoVyMenaDPH` | nvarchar(3) | ANO |  |  |
| 127 | `SamoVyZdrojKurzu` | int | ANO | ((2)) |  |
| 128 | `SamoVyDatumKurzuDPH` | datetime | ANO |  |  |
| 129 | `SamoVyMnoKurzDPH` | int | ANO | ((1)) |  |
| 130 | `SamoVyKurzDPH` | numeric(19,6) | ANO | ((1)) |  |
| 131 | `SamoVyMenaDPHHM` | nvarchar(3) | ANO |  |  |
| 132 | `SamoVyDatumKurzuDPHHM` | datetime | ANO |  |  |
| 133 | `SamoVyMnoKurzDPHHM` | int | ANO | ((1)) |  |
| 134 | `SamoVyKurzDPHHM` | numeric(19,6) | ANO | ((1)) |  |
| 135 | `DatPorizeni_D` | int | ANO |  |  |
| 136 | `DatPorizeni_M` | int | ANO |  |  |
| 137 | `DatPorizeni_Y` | int | ANO |  |  |
| 138 | `DatPorizeni_Q` | int | ANO |  |  |
| 139 | `DatPorizeni_W` | int | ANO |  |  |
| 140 | `DatPorizeni_X` | datetime | ANO |  |  |
| 141 | `DatPorizeniSkut_D` | int | ANO |  |  |
| 142 | `DatPorizeniSkut_M` | int | ANO |  |  |
| 143 | `DatPorizeniSkut_Y` | int | ANO |  |  |
| 144 | `DatPorizeniSkut_Q` | int | ANO |  |  |
| 145 | `DatPorizeniSkut_W` | int | ANO |  |  |
| 146 | `DatPorizeniSkut_X` | datetime | ANO |  |  |
| 147 | `DatZmeny_D` | int | ANO |  |  |
| 148 | `DatZmeny_M` | int | ANO |  |  |
| 149 | `DatZmeny_Y` | int | ANO |  |  |
| 150 | `DatZmeny_Q` | int | ANO |  |  |
| 151 | `DatZmeny_W` | int | ANO |  |  |
| 152 | `DatZmeny_X` | datetime | ANO |  |  |
| 153 | `DatPovinnostiFa_D` | int | ANO |  |  |
| 154 | `DatPovinnostiFa_M` | int | ANO |  |  |
| 155 | `DatPovinnostiFa_Y` | int | ANO |  |  |
| 156 | `DatPovinnostiFa_Q` | int | ANO |  |  |
| 157 | `DatPovinnostiFa_W` | int | ANO |  |  |
| 158 | `DatPovinnostiFa_X` | datetime | ANO |  |  |
| 159 | `Realizovano` | bit | ANO |  |  |
| 160 | `Uctovano` | bit | ANO |  |  |
| 161 | `DatRealizace_D` | int | ANO |  |  |
| 162 | `DatRealizace_M` | int | ANO |  |  |
| 163 | `DatRealizace_Y` | int | ANO |  |  |
| 164 | `DatRealizace_Q` | int | ANO |  |  |
| 165 | `DatRealizace_W` | int | ANO |  |  |
| 166 | `DatRealizace_X` | datetime | ANO |  |  |
| 167 | `DatUctovani_D` | int | ANO |  |  |
| 168 | `DatUctovani_M` | int | ANO |  |  |
| 169 | `DatUctovani_Y` | int | ANO |  |  |
| 170 | `DatUctovani_Q` | int | ANO |  |  |
| 171 | `DatUctovani_W` | int | ANO |  |  |
| 172 | `DatUctovani_X` | datetime | ANO |  |  |
| 173 | `Splatnost_D` | int | ANO |  |  |
| 174 | `Splatnost_M` | int | ANO |  |  |
| 175 | `Splatnost_Y` | int | ANO |  |  |
| 176 | `Splatnost_Q` | int | ANO |  |  |
| 177 | `Splatnost_W` | int | ANO |  |  |
| 178 | `Splatnost_X` | datetime | ANO |  |  |
| 179 | `DatumSplatnoRPT_D` | int | ANO |  |  |
| 180 | `DatumSplatnoRPT_M` | int | ANO |  |  |
| 181 | `DatumSplatnoRPT_Y` | int | ANO |  |  |
| 182 | `DatumSplatnoRPT_Q` | int | ANO |  |  |
| 183 | `DatumSplatnoRPT_W` | int | ANO |  |  |
| 184 | `DatumSplatnoRPT_X` | datetime | ANO |  |  |
| 185 | `DUZP_D` | int | ANO |  |  |
| 186 | `DUZP_M` | int | ANO |  |  |
| 187 | `DUZP_Y` | int | ANO |  |  |
| 188 | `DUZP_Q` | int | ANO |  |  |
| 189 | `DUZP_W` | int | ANO |  |  |
| 190 | `DUZP_X` | datetime | ANO |  |  |
| 191 | `DatumDoruceni_D` | int | ANO |  |  |
| 192 | `DatumDoruceni_M` | int | ANO |  |  |
| 193 | `DatumDoruceni_Y` | int | ANO |  |  |
| 194 | `DatumDoruceni_Q` | int | ANO |  |  |
| 195 | `DatumDoruceni_W` | int | ANO |  |  |
| 196 | `DatumDoruceni_X` | datetime | ANO |  |  |
| 197 | `TerminDodavkyDat` | datetime | ANO |  |  |
| 198 | `TerminDodavkyDat_X` | datetime | ANO |  |  |
| 199 | `DatSplneni` | datetime | ANO |  |  |
| 200 | `PlatnostDo` | datetime | ANO |  |  |
| 201 | `DatumKurzu_D` | int | ANO |  |  |
| 202 | `DatumKurzu_M` | int | ANO |  |  |
| 203 | `DatumKurzu_Y` | int | ANO |  |  |
| 204 | `DatumKurzu_Q` | int | ANO |  |  |
| 205 | `DatumKurzu_W` | int | ANO |  |  |
| 206 | `DatumKurzu_X` | datetime | ANO |  |  |
| 207 | `SumaKcDPoh` | numeric(19,6) | ANO |  |  |
| 208 | `DatUhrady_D` | int | ANO |  |  |
| 209 | `DatUhrady_M` | int | ANO |  |  |
| 210 | `DatUhrady_Y` | int | ANO |  |  |
| 211 | `DatUhrady_Q` | int | ANO |  |  |
| 212 | `DatUhrady_W` | int | ANO |  |  |
| 213 | `DatUhrady_X` | datetime | ANO |  |  |
| 214 | `KcZvyseni` | numeric(19,6) | ANO |  |  |
| 215 | `KcSnizeni` | numeric(19,6) | ANO |  |  |
| 216 | `KcZvSn` | numeric(19,6) | ANO |  |  |
| 217 | `EcSNCelkemDokl` | numeric(19,6) | ANO |  |  |
| 218 | `SNCelkemDoklDruh` | numeric(19,6) | ANO |  |  |
| 219 | `EcSNCelkemDoklDruh` | numeric(19,6) | ANO |  |  |
| 220 | `EcZvyseni` | numeric(19,6) | ANO |  |  |
| 221 | `EcSnizeni` | numeric(19,6) | ANO |  |  |
| 222 | `EcZvSn` | numeric(19,6) | ANO |  |  |
| 223 | `SumaKcBezDPHDruh` | numeric(19,6) | ANO |  |  |
| 224 | `SumaValBezDPHDruh` | numeric(19,6) | ANO |  |  |
| 225 | `KcBezDPHZvyseni` | numeric(19,6) | ANO |  |  |
| 226 | `KcBezDPHSnizeni` | numeric(19,6) | ANO |  |  |
| 227 | `KcBezDPHZvSn` | numeric(19,6) | ANO |  |  |
| 228 | `SamoVyDatumKurzuDPH_D` | int | ANO |  |  |
| 229 | `SamoVyDatumKurzuDPH_M` | int | ANO |  |  |
| 230 | `SamoVyDatumKurzuDPH_Y` | int | ANO |  |  |
| 231 | `SamoVyDatumKurzuDPH_Q` | int | ANO |  |  |
| 232 | `SamoVyDatumKurzuDPH_W` | int | ANO |  |  |
| 233 | `SamoVyDatumKurzuDPH_X` | datetime | ANO |  |  |
| 234 | `SamoVyDatumKurzuDPHHM_D` | int | ANO |  |  |
| 235 | `SamoVyDatumKurzuDPHHM_M` | int | ANO |  |  |
| 236 | `SamoVyDatumKurzuDPHHM_Y` | int | ANO |  |  |
| 237 | `SamoVyDatumKurzuDPHHM_Q` | int | ANO |  |  |
| 238 | `SamoVyDatumKurzuDPHHM_W` | int | ANO |  |  |
| 239 | `SamoVyDatumKurzuDPHHM_X` | datetime | ANO |  |  |
| 240 | `RezimMOSS` | tinyint | ANO | ((0)) |  |
| 241 | `TerminDodavkyDat_D` | int | ANO |  |  |
| 242 | `TerminDodavkyDat_M` | int | ANO |  |  |
| 243 | `TerminDodavkyDat_Y` | int | ANO |  |  |
| 244 | `TerminDodavkyDat_Q` | int | ANO |  |  |
| 245 | `TerminDodavkyDat_W` | int | ANO |  |  |
| 246 | `IDDanovyRezim` | int | ANO |  |  |
| 247 | `PlneniDoLimitu` | bit | ANO | ((1)) |  |
| 248 | `KHDPHDoLimitu` | tinyint | ANO | ((1)) |  |
| 249 | `RezimPreuctovaniSK` | bit | ANO | ((0)) |  |
| 250 | `NastavPreuctovaniSK` | tinyint | ANO | ((1)) |  |
| 251 | `ZbyvaUvolnitValProSaldo` | numeric(19,6) | ANO | ((0.0)) |  |
| 252 | `ZbyvaUvolnitKCProSaldo` | numeric(19,6) | ANO | ((0.0)) |  |
| 253 | `StavEET` | tinyint | ANO | ((2)) |  |
| 254 | `SumaValDPoh` | numeric(20,6) | ANO |  |  |
| 255 | `DruhCU` | tinyint | ANO | ((1)) |  |
| 256 | `JeNovaVetaEditor` | bit | ANO | ((0)) |  |
| 257 | `FakturacniZam` | int | ANO |  |  |
| 258 | `PZ2` | nvarchar(20) | ANO | ('') |  |
| 259 | `StavNahPlneni` | tinyint | ANO | ((0)) |  |
| 260 | `CastkaNahPlneni` | numeric(19,6) | ANO | ((0.0)) |  |
| 261 | `PotvrDoruceni` | bit | ANO | ((0)) |  |
| 262 | `JeToDDPP` | bit | ANO | ((0)) |  |
| 263 | `SrazkovaDanVHM` | numeric(19,6) | ANO | ((0.0)) |  |
| 264 | `PomerKoef` | numeric(19,6) | ANO |  |  |
| 265 | `NeupozNaNenavDok` | bit | ANO | ((0)) |  |
| 266 | `DruhPohybuZboPZO` | tinyint | ANO |  |  |
| 267 | `StavZalFak` | tinyint | ANO |  |  |
| 268 | `ZpusobKurzZal` | tinyint | ANO |  |  |
| 269 | `Nehradit` | tinyint | ANO | ((0)) |  |
| 270 | `ZboziSluzba` | tinyint | ANO | ((0)) |  |
| 271 | `PoradoveCisloPuvodniFaKV` | nvarchar(32) | ANO |  |  |
| 272 | `DelkaPorCis` | tinyint | ANO |  |  |
| 273 | `ParovaciZnak` | nvarchar(20) | ANO |  |  |
| 274 | `IdOSSOpr` | int | ANO |  |  |
| 275 | `UctovanoNulovy` | bit | ANO | ((0)) |  |
| 276 | `PorCisKV` | nvarchar(60) | ANO |  |  |
| 277 | `Cislo` | nvarchar(17) | ANO |  |  |
| 278 | `EcCelkemDoklUctoDruhovy` | numeric(19,6) | ANO |  |  |
| 279 | `IDBankSpPrep` | int | ANO |  |  |
| 280 | `KonstSymbolPrep` | nvarchar(10) | ANO |  |  |
| 281 | `SpecSymbolPrep` | nvarchar(10) | ANO | ('') |  |
| 282 | `SlevyBezRecykl` | bit | ANO | ((0)) |  |
| 283 | `MetodaSD` | bit | ANO | ((0)) |  |
| 284 | `VypoctenaLhutaSplatnosti` | int | ANO |  |  |
| 285 | `DatRealMnoz` | datetime | ANO |  |  |
| 286 | `ZaokrNaPadesat` | smallint | ANO | ((0)) |  |
| 287 | `PrevodRealizovat` | bit | ANO | ((0)) |  |
| 288 | `SumaKcPoZaoDPoh` | numeric(20,6) | ANO |  |  |
| 289 | `SumaKcPoZao` | numeric(20,6) | ANO |  |  |
| 290 | `CastkaZaoKc` | numeric(20,6) | ANO |  |  |
| 291 | `SumaKcPoZaoBezZal` | numeric(20,6) | ANO |  |  |
| 292 | `CastkaZaoVal` | numeric(20,6) | ANO |  |  |
| 293 | `SumaKcPoZaoBezZalVal` | numeric(20,6) | ANO |  |  |
| 294 | `Saldo` | numeric(19,6) | ANO |  |  |
| 295 | `DnuProdleniZapl` | int | ANO |  |  |
| 296 | `DnuProdleniNazapl` | int | ANO |  |  |
| 297 | `DnuProdleni` | int | ANO |  |  |
| 298 | `SumaValPoZao` | numeric(20,6) | ANO |  |  |
| 299 | `SumaValPoZaoDPoh` | numeric(20,6) | ANO |  |  |
| 300 | `RealizovanoMnoz` | bit | ANO |  |  |
| 301 | `DatRealMnoz_D` | int | ANO |  |  |
| 302 | `DatRealMnoz_M` | int | ANO |  |  |
| 303 | `DatRealMnoz_Y` | int | ANO |  |  |
| 304 | `DatRealMnoz_Q` | int | ANO |  |  |
| 305 | `DatRealMnoz_W` | int | ANO |  |  |
| 306 | `DatRealMnoz_X` | datetime | ANO |  |  |

## Indexy

- **PK** `PK_EC_DokladyZbozi_Log` (CLUSTERED) — `Log_ID`
