# Podklad OSVC: prvni ostry test zapisu do Heliosu (Vasyl 19.8.2026) — co selhalo a co opravit

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Prvni ostry test zapisu objednavky — Vasyl Namjak, 19. 8. 2026

Claude-24 (Kristy). Test provedla Kristy z FLOW. **Vysledek: zapis se rozjel, ale skoncil
falesnou chybou; vse uklizeno stornem.** Zitra navazujeme opravami nize.

## Co se stalo

Kristy kliknula „Objednavka EUROSOFT (EC)" na Vasylovi (464, uid 59, podklad 25 657 Kc).
Hlaska: **„Polozka pro VR10609 se nezalozila (bez ID)."**

Realny stav po behu (overeno v obou DB):
- Helios: objednavka **770018** (rada 800, poradove 861586) — polozka **1301883**
  VR10609 za 13 307 Kc **VZNIKLA**, a k ni radek `EC_Zakazky_PlatbyZam` **6779**.
- Ukol na Nakup: **nezalozen** (orchestrator spadl driv) — spravne.
- Razitka v Centrale: **zadna** (razitkuje se az po vlozeni vsech polozek) — spravne.
- U nas: hlavicka #2 'navrzeno', 4 radky, 1 razitko na `vyroba_work` (0,51 h rezie).

## Pricina falesne chyby (root cause)

`podklad_osvc_helios_obj` posila JEDNU davku, ktera obsahuje vic prikazu vracejicich
vysledek: nejdriv `SELECT TOP 1 @regcis = ... ` (dotazeni RegCis/predpisu/strediska),
pak `EXEC EC_PrijemZbozi_InsertPolozky`, a nakonec `SELECT @ident AS ident`.
**Pres MCP `eurosoft_strategie_query_raw` se vraci jen PRVNI result set**, takze skript
`@ident` nikdy neuvidi a vyhodnoti to jako selhani — prestoze polozka vznikla.
Pro srovnani: `podklad_ukol_send` funguje, protoze ma v davce jediny SELECT na konci.

**Oprava (zitra):** rozdelit na dve volani — (1) zjistit RegCis/predpis/stredisko,
(2) EXEC + UPDATE + INSERT + jediny zaverecny SELECT.

## Druha chyba: nahled zkousi jen jednu firmu

Nahled i zapis se ptaji jen na radu podle zvolene firmy. Vasyl ma pritom nerealizovane
objednavky **obe**: 769383 (rada 801 = ES, 5 prazdnych polozek) i 770018 (rada 800 = EC).
Kristy: *„nahled funguje asi jen pro jednu firmu, hlasil u Vasyla, ze neexistuje prazdna
objednavka v EC, ale v ES ji mel"*.

**Oprava (zitra):** nahled ukaze OBE firmy vedle sebe — kde objednavka je a kde neni.

## Treti vec: STORNO NEHLIDA REALIZOVANE OBJEDNAVKY

Kristy 19.8.2026: *„storno nesmi sahat na jiz realizovane objednavky"*. Dnes se tlacitko
Storno ridi stavem NASI hlavicky ('navrzeno'/'objednano'), **ne** stavem dokladu v Heliosu.
Kdyby holky mezitim objednavku zrealizovaly, storno by jeji polozky smazalo.

**Oprava (zitra):** `podklad_osvc_storno` pred mazanim overi, ze doklad ma
`Realizovano = 0` a `DatRealizace IS NULL`; jinak odmitne s vysvetlenim.

## Uklid po testu — probehl a je overeny

Do naseho radku se doplnilo `id_pol_vobj = 1301883` (banner #2244) a Kristy kliknula Storno.
Po nem: polozka 1301883 **pryc**, radek plateb 6779 **pryc**, objednavka 770018 **prazdna**,
objednavka 769383 (ES) **nedotcena** (porad 5 prazdnych polozek), obe nerealizovane.
U nas: 0 razitek, 0 radku, hlavicka #2 = 'storno'. Vasylova testovaci odmena (id 20068,
1 Kc) je zase volna (`id_pol_vobj = NULL`).

**Storno tim padem odzkousene a funguje.**

## Ctvrta vec: mini-sync odmen

`sync_odmeny_osoba` (novy, aktivni) dotahne odmeny JEDNOHO cloveka — cely hodinovy sync
`sync_pripl_srazky_ec` trva ~17 s / 3 000 radku, coz je na kazde kliknuti moc.
Kristy: *„to budeme potrebovat mit hned"*. **Zitra:** zavolat ho z endpointu pred nahledem,
nahledem objednavky i ostrym generovanim (chybu syncu neprenaset do podkladu — jen varovani).

