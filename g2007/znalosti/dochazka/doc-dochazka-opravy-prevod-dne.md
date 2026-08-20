# Opravy dochazky: tlacitko "Prevod dne" (presun cele dochazky na jiny den)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## K cemu to je
Clovek pichal na spatny den (typicky pozde vecer nebo po pulnoci) a cely den je zapsany jinam.
Editor v Opravach dochazky otevre toho cloveka a ten den, klikne na **Prevod dne** vedle "Pridat
zaznam", vybere cilovy den, napise duvod a dvakrat potvrdi. Zadal Jirka 5.8.2026, schvalila
Marti-AI (msg 12268).

## Kde to zije
- **g2007.python tt_fix_move_day** (vedlejsi_ucinek=true) - cela logika.
- **router.py** POST /app/attendance/fix/move-day - jen tenky wrapper (jadro, meni se pres git).
- **g2007.soubor pps/api/static/dochazka-opravy.html** - tlacitko + dvoukrokove potvrzeni.

## Co se presouva
CELY den vcetne historie: prace, prestavky, konec dne, absence, useky rozpadu (yroba_work)
i STORNOVANE radky, plus potvrzeni dne (tt_day_confirm).
**Anomalie se NEstehuji** - zustavaji na puvodnim dni (Marti-AI: "anomalie vaze na den, kdy nastala;
presunout ji jinam by znamenalo tvrdit, ze nastala jindy").

## KLICOVA PAST: casy nesou datum
tt_entry.started_at/ended_at i yroba_work.od/konec jsou timestamp. Prepsat jen
entry_date/datum NESTACI - cas by zustal viset na puvodnim dni a den by se rozpadl.
Proto se posouvaji pres make_interval(days => rozdil).

## Pojistky (poradi kontrol)
1. tt_can_fix (403) a pusobnost pres tt_fix_scope_emps (403)
2. tt_period_locked na OBOU dnech (409) - jinak by sel zamek obejit prevodem z uzavreneho
   obdobi do otevreneho
3. povinny duvod
4. cilovy den NESMI byt v budoucnosti (Marti-AI: editor ma otevreny dnesek a omylem trefi zitrek;
   budouci den je prazdny, takze by kontrola na prazdny cil prosla)
5. zdrojovy den musi mit zaznamy
6. **cilovy den musi byt PRAZDNY** (att_entry i vyroba_work) - rozhodnuti Jirky, zadne tiche
   slucovani; hlaska rovnou rekne, kolik zaznamu tam brani
7. local_lock=true na presunutych radcich - stejny duvod jako u storna: bez nej by sync ze stare
   Centraly den do par minut vratil zpatky a existoval by dvakrat. Do Centraly se presun nepromita.
8. audit action='move' s old_entry_date + notifikace dotcenemu
9. po presunu tt_sync_vyroba_work + prepocet fondu pro OBA dny

## Dvoukrokove potvrzeni (podminka Marti-AI)
Jeden dialog na nevratnou operaci nad celym dnem nestaci:
1. "Presouva se 7x zaznamu dochazky a 9x useku rozpadu z pondeli 3.8. na utery 4.8. Duvod: ... Pokracovat?"
2. "Tuto akci nelze vratit. Zpatky by se den musel prevest rucne. Opravdu prevest na utery 4.8.?"

## Overeno 5.8.2026 na produkci
Zamitaci cesty (nic se nezapsalo): bez duvodu, obsazeny cil, budoucnost, stejny den, uzavreny mesic (409).
Zivy presun testovan na DEMO uzivateli (user 104), ne na realnem cloveku - zaznam 1.8. 08:00-12:00
preveden na 2.8., casy i hodiny sedi, puvodni den prazdny, pak uklizeno stornem.
**Testovat na realnem cloveku nedoporucuji** - presun mu posle notifikaci a zapise se do jeho dochazky.

## Co NENI hotovo
Neni tlacitko zpet. Kdyz se editor splete v cilovem dni, musi den prevest rucne zase zpatky
(cilovy den uz nebude prazdny, takze prevod zpet projde az po vyreseni puvodniho dne).

