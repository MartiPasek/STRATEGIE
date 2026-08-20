# Demo rezim - stav zapojenych obrazovek k 11.8.2026 vecer

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


Navazuje na doc-dochazka-demo-ucet-izolace-ukazkova-data (pricina incidentu, reseni, 10 pasti).
Stav po zapojeni vsech 18 GET cest dochazky (commity 315abe71, 0d2a6195), overeno volanim
pod demo cookie, ne navratovkou.

## VRACI DATA (8)
status, whereabouts, unconfirmed, absence/mine, absence/inbox, day-detail, fix/allowed.
Prehled tymu ukazuje vsechny ctyri ukazkove lidi, status rozdelanou smenu.

## VRACI 403 - SPRAVNE (7)
period-lock a rodina fix/* krome fix/allowed. Demo na opravy dochazky prava nema.

## VRACI PRAZDNO - NEDOLADENO (3)
daily, list, real. (announced-future vraci prazdno spravne - zadna ohlasena absence v datech.)

## DIAGNOSTIKA, KTEROU JSEM UDELAL - a co z ni plyne

Rozhodujici experiment: pridal jsem do att_list_demo docasny klic _diag do navratove
hodnoty. V DB se ulozil (verze 3, position('_diag' in zdroj) > 0), ale v odpovedi
endpointu se NEOBJEVIL. Tyz experiment na att_status_demo se propsal OKAMZITE
(odpoved obsahovala "_diag_test":42). Oba klice jsem po testu zase odstranil.

Z toho plyne, co uz NENI potreba znovu overovat
- guard funguje a bezi pro vsechny cesty - /app/devices (mimo whitelist) vraci fallback
  prazdno, /app/attendance/status (ve whitelistu) vraci demo data
- cache erp_registry NENI problem - zmena att_status_demo se projevila okamzite
- kod je nasazeny - origin/main i lokal maji vsechny tri cesty v _DEMO_DELEGATI
- data existuji - SELECT presne tim dotazem, ktery ma att_list uvnitr, vraci 16 radku
- demo.att_den_hodiny funguje - primo vraci 24 radku, pro emp 1 sest
- _att_employee vraci 1, _ATT_TENANT je 9999, v run() je jediny return

Zbyva rozpor, ktery jsem nerozlouskl: cesta JE ve whitelistu (jinak by vratila fallback
jako /devices), ale navratova hodnota neodpovida ani delegatu (nema _diag), ani fallbacku.
Dalsi krok pro toho, kdo navaze - pridat log primo do guardu (vypsat _dm_p a jestli se
_DEMO_DELEGATI.get trefil) a zavolat endpoint. Tim se to rozhodne.

## POZOR PRI ODVOZOVANI DELEGATU
Definice _ATT_TENANT NENI u vsech funkci na stejnem miste. U att_status je nahore,
u att_daily, att_list, att_real, att_day_detail a att_announced_future nahore neni
a regexp na odstraneni bloku _att_employee ji sezral. Projev - obrazovka bezi, NEHLASI
chybu, jen vraci prazdno. Po kazdem odvozeni kontroluj DELKU proti originalu I to,
ze vysledek obsahuje _ATT_TENANT = 9999.

## OSTATNI MODULY - NEZAPOJENO
Appka vola 243 ruznych API cest, zapojena je jen dochazka (18). Ukoly, kontakty, vyroba,
CRM, Bakalari, ISDS jsou v demu prazdne - kazdy by potreboval vlastni ukazkova data
i vlastni sadu delegatu. Rozsah na dny, ne na jednu session.

