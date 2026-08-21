# Podklad OSVC: ukol na Nakup musi CIST objednavku, ne pocitat podklad znovu

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co se stalo (20. 8. 2026, ostry test Vasyl Namjak c. 464)
Objednavka 861586 obsahovala 4 radky za **27 277 Kc**. Ukol na Nakup, ktery se posila
hned po ni, ale tvrdil **27 098 Kc** — chybel radek „Rezie + dovolena 179 Kc".

## Proc
`podklad_ukol_send` si podklad POCITAL ZNOVU (`podklad_vyplaceni_pdf`). Jenze poradi je:
1. `podklad_osvc_zapis` → zapise radky a **ORAZITKUJE** zdroje (`fakturace_obj_id`)
2. `podklad_osvc_helios_obj` → polozky objednavky
3. `podklad_ukol_send` → ukol

Po kroku 1 uz orazitkovana rezie/dovolena/odmena **z prepoctu vypadne** — to je spravne
chovani (aby se nefakturovala dvakrat), jen se nesmi pouzit pro popis toho, co se prave
objednalo.

**Zakerne bylo, ze zakazky rozdil neudelaly.** Ty se totiz z podkladu neztraci
orazitkovanim, ale az odectem „uz objednano" pres zrcadlo zaloh — takze zustaly stejne
a rozdil vypadal jako drobna nesrovnalost v jednom cisle, ne jako chybejici radek.

## Reseni (nasazeno)
`podklad_ukol_send` cte radky z **`tenant.osvc_vobj_radek`** = zaznamu toho, co se
opravdu zapsalo. `podklad_osvc_generuj` mu predava `vobj_id`. Pri samostatnem odeslani
ukolu (tlacitko po neuspechu) si dohleda posledni hlavicku ve stavu `objednano`
mladsi nez 2 dny. Prepocet zustal jen jako zaloha, kdyz zadna cerstva objednavka neni.

## Obecne pravidlo
**Co popisuje uz provedeny zapis (ukol, mail, potvrzeni, report), se musi cist ZE ZAPISU,
ne pocitat znovu ze zdrojovych dat.** Zdrojova data se zapisem zmenila — prave proto,
ze zapis probehl. Plati na cely podklad OSVC i na kazdy dalsi „vygeneruj a oznam" tok.
Souvisi s [[doc-system-strategie-centrala-ukolnik-zalozeni-ukolu-pasti]].

