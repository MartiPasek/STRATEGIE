# Datová mapa kalkulace — Centrála (DB_EC) ↔ STRATEGIE (PG)

> oblast: `kalkulace-rozvadecu` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Datová mapa kalkulace — Centrála (DB_EC) ↔ STRATEGIE (PG)

> Pojmenování a spárování tabulek napříč oběma systémy pro zdroj pravdy kalkulace. Claude C23, 22.7.2026. Ověřeno dotazy do DB_EC (db=mssql) i PG (tenant.*).

**Konvence:** Centrála 1 = **DB_EC** (MSSQL, read-only, legacy pravda). STRATEGIE = **PG** `tenant.*`: `ec_*` = zrcadla z DB_EC, `cenik_*`/`kalk_*` = nativní systémy STRATEGIE.

## 1. Kmen zboží (identita dílu)
| Role | Centrála DB_EC | STRATEGIE PG |
|---|---|---|
| Master | `TabKmenZbozi` (209 sl., ~17,5k) + `_EXT`/`Dodatek`/`Imp` | `ec_kmen_zbozi` (17 459, zrcadlo) |
| Index z kalkulací | — | `kalk_kmen` (4 958: reg_cis, nazev, skp, jednotka, kmen_ec_id) |

Klíč = **`RegCis`**. Nese `Vyrobce`, `Aktualni_Dodavatel`, `Hmotnost`+rozměry, **`DodaciLhuta`**, kategorie přes flagy `Dilec`/`Montaz`/`Material`/`Naradi`/`RezijniMat`.

## 2. Kalkulace položky (historie + koeficient = IP)
| Role | Centrála DB_EC | STRATEGIE PG |
|---|---|---|
| Položky | `EC_KalkulacePolozky` (**142 sl.**) + `_ARCHIV`/`Temp*` | `ec_kalkulace_pol` (**jen 17 sl. — OCHUZENÉ**) |
| Hlavičky | `EC_KalkulaceHlav` | `ec_kalkulace_hlav` |

Klíče na řádku: `RegCis` + **`IDKmenZbozi`** (most na kmen/sklad) + **`IDCenik`** (most na ceník).
**Koeficient (IP): `K_ARB`, `K_VKM`** + sazby `ARB_Sazba` (28) / `VKM_Sazba` (14,5) — jsou jen ve zdroji, **zrcadlo je nemá** (má jen odvozený `arbeitstunden`).

## 3. Ceníky (aktuální cena)
| Role | Centrála DB_EC | STRATEGIE PG (nativní) |
|---|---|---|
| Položky | `EC_CenikyTXT` (**5,9 mil.**, klíč `RegCisHeo`, `EC_PC`/`EC_NC`/`Mena`/rabaty) | `cenik_polozka` (**539k**, `kat_kod`+`kat_kod_norm`, `list_price`/`net_price`/`rabat`/`mena`/`hmotnost_kg`) |
| Hlavičky/platnost | `EC_CenikyTXTHlav` (2412, `Vyrobce`/`PlatnostOD`/`Do`) | `cenik_import` (platnost, zdroj_soubor) |
| Konfig/vzorce | — | `cenik_vyrobce` (col_map), `cenik_vzorec` (vyraz), `cenik_cena_medi` |
| Vazby | `EC_CenikyVazby`, `EC_X_Ceniky`, `EC_extCeniky`, `EC_CenikyPorovnani` | `ec_cenik_hlav` (95), `ec_cenik_nastaveni`, `ec_cenik_vzorec*` (zrcadla) |

Naimportováno **11 výrobců** (SIE 261k, MUR 58k, WEI 51k, PHO 47k, EAT 32k, SCH 31k, WAG 30k, LAP 22k, RIT 4,6k, FIN 1,4k, HAR 0,5k), poslední import **2.7.2026**, 99,7 % s cenou.
`kat_kod_norm` = **3-kód výrobce + číslo bez mezer** (`SIE1ED1322-0AA00…`).
**`cenik_prevod` (překladová tabulka) SMAZÁNA 22.7.2026** — prázdná, pro standard netřeba (párování řeší deterministická normalizace).

## 4. Sklad (dostupnost)
| Role | Centrála DB_EC | STRATEGIE PG |
|---|---|---|
| Stav | `TabStavSkladu` (17,5k) + `_EXT` | `ec_stav_skladu` (17 495) |
| Pohyby | `TabSkladVydeje` (157k), `TabSkladPrijmy` (126k) | `ec_pohyb_zbozi` (124k), `ec_doklad_zbozi` |

## Spojovací klíče (celý flow)
- Díl: **`RegCis`** (kmen, kalkulace) ↔ **`RegCisHeo`** (ceník DB_EC) ↔ **`kat_kod_norm`** (ceník PG, s prefixem výrobce).
- Díl → sklad: **`IDKmenZbozi`**. Díl → ceník: **`IDCenik`**. Zakázka (celý řetězec): **`CisloZakazky`**.

## Klíčová zjištění (22.7.2026)
1. **Zrcadlo `ec_kalkulace_pol` je lossy** — pro zdroj pravdy dotáhnout ze zdroje `K_ARB`/`K_VKM`/`IDKmenZbozi`/`IDCenik`.
2. **Aktuální cena už existuje nativně** (`cenik_polozka` 539k) — nestavět katalog od nuly.
3. **Koeficient = explicitní `K_ARB`/`K_VKM`**, ne dopočet.
4. **Identita = kmen zboží** (`RegCis`); vesmír kalkulace = kmen ∪ historie ∪ ceník.
5. **Normalizace se zatím nesešla** (0 % přímé shody kalkulace↔ceník) — ceník má prefix výrobce, kalkulace holé číslo → párování potřebuje **prefix-aware normalizaci** (mapování výrobce → 3-kód SIE/RIT…). Další krok.
6. „Zdroj pravdy" = **propojovací/kurátorská vrstva** nad kmen + ceník + koeficient, ne nová median-tabulka.

