# Deploy-bezpecnost: git-write pres device most NEJDE + lokal EC-Martin je zamotany

> oblast: `provoz` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Deploy-bezpecnost: co (ne)jde pres device most (C23, 31.7.2026, po incidentu)

## Zlate pravidlo
NIKDY nekomituj cely velky staged soubor pres most. device_stage_files muze podat STAROU/WIP kopii; commit ji pak natvrdo prepise. Tak vznikl 31.7. incident: commit ebf5d7d78 prepsal router.py starou kopii a smazal ~1100 r. serverove brany Priplatku (opravil Claude-26 obnovou). Vzdy jen male chirurgicke edity + over, ze staged == origin HEAD.

## Proc git-write pres most (device_bash) v principu NEDOJEDE
1) Mount (9p) ZAKAZUJE unlink/delete -> git nemuze smazat .git/index.lock ani
   soubory pri reset --hard / rebase / checkout. Zustane viset stale lock.
   Obejiti stale locku: `mv .git/index.lock _to_delete/...` (mazat nejde).
2) device_bash NEMA SIT -> `git fetch` = HTTP 403 proxy. Remote-tracking ref
   (origin/main) je proto STALE; nelze ziskat pravou origin.
=> Reset/rebase/commit/push MUSI delat operator z realneho Windows shellu (sit +
   pravo mazat). Most slouzi jen ke cteni + malym file-editum + spousteni deploy/pull lane.

## Stav lokalu EC-Martin (D:\Projekty\STRATEGIE) k 31.7. dopoledne
ZAMOTANY: soucasne PRED origin (stary spatny commit ebf5d7d78 + revert a69a86fd) i POZADI o 4 Peta commity. + 181-souborovy rozdil a hromada untracked WIP (tool_registry, kalkulace, eurosoftdir...). reset --hard pres most nejde (unlink).
=> Pred pristim deployem z tohohle lokalu ho operator musi srovnat:
   git fetch origin && git reset --hard origin/main  (na cistem shellu).
   Jinak deploy-rebase prehraje ebf5d7d78 a hrozi opakovani incidentu.

## GOTCHA doplneno 31.7. odpoledne (Marti primo v PowerShellu, ne pres most)
I CISTY operatorsky shell muze selhat, kdyz se preskoci fetch: Marti spustil rovnou
`git reset --hard origin/main` BEZ predchoziho `git fetch` -> lokalni remote-tracking
ref origin/main byl stary -> reset pristal na cdfadd836 (nesouvisejici stary commit
"Pokladni doklady + Prijate faktury: razeni sloupcu"), lokal se tim dostal 85 commitu
POZADI za skutecnym originem. PRAVIDLO: `git reset --hard origin/main` VZDY az PO
`git fetch origin` (ne misto nej) - jinak "reset na origin" ve skutecnosti resetuje
na stary cachovany stav, ne na pravou spicku.

## Bezpecny postup nasazeni odsud
Claude (pres most): diagnostika + autorstvi patche + zapis do g2007 + spousteni lane.
Operator (cisty shell/sit, nebo produkcni checkout na Praze): git fetch + reset, aplikace patche, commit/push/deploy.
Deploy lane sam ma py_compile branu + anti-prepis rebase, ale ta pri zamotanem lokalu spis skonci konfliktem (abort).

## TODO / Roadmap dohodnuto s Martim 31.7. odpoledne (4 navrhy od Claude pres Kristy/C24, serazeno cena/prinos)
Marti: "dej to do todo a g2007 jako znalost k reseni a az nebude provoz na deployich, tak se do toho spolu vrhneme."
Neni to alternativy, je to defense-in-depth - navrzeno delat ve dvou rychlostech:

RECOMMENDED prvni (rychle, mechanicke, chyti presne tenhle mechanismus selhani bez ohledu na velikost souboru):
1. Diffstat pojistka v deploy watcheru - pred pushnutim spocitat diffstat; kdyz soubor
   neuvedeny v CLAUDE_DEPLOY.txt jako cil zmeni radove vic radku nez male chirurgicke
   edity (napr. -1000+ radku), tvrde zastavit deploy a upozornit.
2. Vynucena cerstvost - watcher pred commitem overi, ze pracovni kopie kazdeho menenych
   souboru stavi na aktualnim originu (git fetch + porovnani); kdyz je stara, vynuti
   re-pull, nikdy slepy commit. (Bod "commitovat jen uvedene soubory" uz deploy skript
   dela - CLAUDE_DEPLOY_OUT.txt ukazuje cilene `git add`; problem nebyl v tom, ze se
   commitlo neco navic, ale ze OBSAH uvedeneho souboru byl zastaraly - proto tohle je
   presnejsi oprava koренove priciny.)

PROJEKT, planovat az bude klid (vetsi refaktor, samostatny design doc):
3. Strukturalni koren - rozdelit modules/erp/api/router.py (67 411 radku, 687 endpointu,
   1103 def) na moduly per domena (dochazka / mzdy / crm / vyroba / hr...). Zjisteno
   31.7.: routy uz MAJI cisty domenovy prefix v URL (/app/hr 69x, /app/attendance 40x,
   /app/vyroba 25x, /app/plan 24x, /app/mzdy, /app/crm, /app/uctovani, /app/banka...) -
   neni to chaos vyzadujici redesign, je to monolit podel uz existujicich svu, riziko
   refaktoru je nizsi nez by se cekalo u 67k-radkoveho souboru. Podle doktriny
   "additivne, ne perfektne" (#11) delat postupne, ne jako jeden big-bang split -
   zacit domenami s nejvetsi kolizi (dle WORK_LOCK.txt dochazka/mzdy), zbytek nechat
   dokud to nebolí.

STAV: OTEVRENO, ceka se na klidne okno (bez soubehu deploy provozu vice instanci),
kdy se Marti + Claude pustí spolu do implementace bodu 1+2 jako prvni krok.

