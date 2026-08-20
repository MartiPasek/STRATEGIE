# Zrcadlo ec.pripl_srazky: proc musi byt PLNY re-import (Centrala vyplnuje IDPolVobj bez zmeny DatZmeny)

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Zrcadlo `ec.pripl_srazky` — plny re-import misto inkrementalniho

Claude-24 (Kristy), 19. 8. 2026. Opraveno tyz den, commit `a1d2dd97`.

## Priznak

Podklad fakturace OSVC nabizel k proplaceni odmenu, ktera uz OBJEDNANA I VYFAKTUROVANA byla.
Konkretne Dusan Havlat (105): `EC_FinPriplatkySrazkyDefinice` ID 19940, 6 921 Kc, "Jednorazove
odmeny od vedouciho". V Centrale mel radek `IDPolVobj=1299421` a `IDPolPF=1300066`,
v zrcadle `ec.pripl_srazky` mel oba sloupce NULL.

## Prycina (overeno v kodu i v datech)

`modules/erp/api/pripl_srazky_sync.sync_from_ec()` bral z Centraly jen radky zmenene od
posledniho behu — vodoznak `ISNULL(DatZmeny, DatPorizeni) >= max(COALESCE(dat_zmeny, dat_porizeni))`.

**Centrala ale pri generovani podkladu fakturace vyplni `IDPolVobj`/`IDPolPF` a pri vyplate
`DatVyplaceni`/`Vyplaceno`/`Vyplatil` — a NESAHNE pritom na `DatZmeny`.** Pro vodoznak je
takova zmena neviditelna, takze uz se do zrcadla nikdy nedostala. (Uklidovy krok syncu
srovnava jen seznam ID — doplni chybejici a smaze zmizele — obsah existujicich radku neresi.)

## Rozsah (mereno 19.8.2026, roky 2025+2026, 2 979 radku na obou stranach)

Porovnani vsech 30 sloupcu radek po radku: **lisilo se 70 radku (2,3 %)**, zadny radek
nechybel ani nepretekal. Sloupce:

| sloupec | radku | zmena |
|---|---|---|
| dat_vyplaceni | 59 | prazdne -> datum vyplaty |
| vyplaceno | 59 | 0 -> 1 |
| vyplatil | 59 | prazdne -> jmeno (Peta) |
| poznamka | 61 | puvodni text -> "vyplaceno pres proc EC_Mzdy_VyplatitPrip" (zapsala Centrala) |
| id_pol_vobj | 9 | prazdne -> ID polozky objednavky |
| id_pol_pf | 4 | prazdne -> ID polozky prijate faktury |

Castky, hodiny, sazby, typy, mzdove slozky, platnosti, cisla zamestnancu, autori, data
porizeni ani priznaky mesicne/fix/schvaleno se nelisily vubec.

## Oprava

V `_mirror_run_job` (router.py) job `sync_pripl_srazky_ec` vola `sync_from_ec(full=True)`
misto `sync_from_ec()`. `full=True` jen vynecha podminku vodoznaku — stejny UPDATE/INSERT kod,
2 979 radku misto ~50 za beh, trvani ~4 s. Zrcadlo je jednosmerne (do Centraly se nic nevraci),
takze neni co ztratit; rucni editace v `ec.pripl_srazky` stejne nedavaji smysl (akcni tlacitka
v jadru jsou proto skryta, viz `pripl_srazky_sync` docstring).

**Overeno po nasazeni:** rok 2026 zrcadlo 976 radku / 168 s VOBJ / 109 nevyplacenych = presne
jako Centrala (pred opravou 160 / 175). Beh hlasi `ins=0, upd=2979, del=0`. Podklad Havlata
spadl z 6 921 Kc na **0 Kc**; kontrolni beh Voriska (327) zustal na 127 588 Kc beze zmeny.

## Poucen1 do dalsich zrcadel

Kdyz zdrojovy system meni radky jinou cestou nez uzivatelskou editaci (procedura, davka,
generator), nemusi si u toho aktualizovat sloupec zmeny. **Inkrementalni sync podle
`DatZmeny` je pak diravy.** U malych tabulek (radove tisice radku) je plny re-import
levnejsi nez hledani, ktera cesta zapisu na co sahne. Nase zrcadlo zaloh
`tenant.osvc_zaloha_zakazek` (`sync_osvc_zalohy`) timhle netrpi — cte celou tabulku pokazde.

