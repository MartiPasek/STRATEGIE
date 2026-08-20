# Vecerni deploy balicek HOTOV (3.8.2026): __uid__ v /run, sweeper automat, zruseni uzavira potreby

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


Uzavira doc-system-strategie-todo-martinky-vecerni-deploy-3-8. Vse nasazeno a overeno naostro:

1. __UID__ PLACEHOLDER (commit 568e8e98f, +3 radky router.py): /app/erp_registry/run nahrazuje string "__uid__" v args skutecnym uid volajiciho. UI martinky.html v6 ho posila vsude -> ukoly maji realne zadavatele/schvalovatele (overeno ukol #11: zadal_user_id=1). Zpetne kompatibilni.
2. SWEEPER AUTOMAT martinky_sweeper (commit 568e8e98f, +53 radku automat_domeny.py + radek g2007.automat, interval 10 min, spousteni='interval' - POZOR: bez spousteni='interval' scheduler automat NIKDY nespusti, INSERT na to musi myslet): rychly SQL check -> status_block "STAV MARTINEK" (pocty ukolu, potreby, zasekle behy) do g2007.automat; pri fronte/nezarazenych/zaseknutych odpali maminka_pridel + martinka_dispatch v daemon threadu (runner NEblokuje - behy trvaji minuty). Eskalace L1 Haiku. OVERENO: prvni beh 20:52 ok, status_block se stavi. Tim je watchdog nezavisly na otevrenem UI a zaklad Smeru 2 (automat sam rozjede praci) zije; status_block je pripraveny pro budouci inject do promptu Marti-AI (jeji pozadavek b).
3. FIX: zruseni ukolu ted uzavira jeho otevrene potreby jako 'zrusena' (martinka_ukol_schval v3, md5 13c1e899...) - nalezena mezera pri uklidu sirotci potreby z testu #6.

Stav orchestrace po dnesku: Smer 1 kompletni (profily, nastroje per domena, rozdelovacka), Smer 2 zaklad (sweeper + kick; domenove automaty zakladajici ukoly = dalsi krok pri stavbe konkretnich automat-oci per domena), HITL kompletni (vlakna, chat, inbox, budicky vlastnikum), mobile.html pipeline zdrava. Zbyva z vecera: NIC. Dalsi velke bloky: mobilni UI Ridici centrum (po pripominkach k mockupum), ABSAUGWERK ostra data (Eliska), charta Eliscine Maminky (schvaleni).

