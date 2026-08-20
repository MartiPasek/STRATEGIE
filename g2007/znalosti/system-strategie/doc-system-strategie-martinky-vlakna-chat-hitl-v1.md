# Ukoly Martinek: vlakno (timeline) + chat s Martinkou pred schvalenim (HITL) - NASAZENO+OVERENO 3.8.2026

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Duvod (Marti 3.8. v noci): "tlacitko schvalit bez detailu a dokomunikovani je velke riziko"

Kazdy ukol ma ted VLAKNO v g2007.ukol_zprava (DDL #1664: ukol_id, autor clovek|martinka|maminka|system, typ kontrakt|beh|reseni|vybava|chat|system, obsah, user_id) - vsechny skripty do nej loguji: zaloz (kontrakt), dispatch v3 (kazdy beh - CELY reply Martinky, ne jen shrnuti), potreba_vyres (lidske reseni), ukol_schval (verdikt), maminka_vybav (doplnek vybavy). Timeline = kompletni auditni stopa ukolu nezavisle na prepisovanem ukol.vysledek.

## Chat s Martinkou nad ukolem
Skript martinka_chat(uid, ukol_id, zprava): ulozi otazku do vlakna, run_goal v CHAT REZIMU (kontext = zadani + vybava domeny + dosavadni vysledek + poslednich 25 zprav vlakna; zadne zapisy/efekty; kdyz clovek chce zmenu vysledku, Martinka popise CO by zmenila - realnou upravu dela regulerni re-run pres Vratit s pripominkou), odpoved ulozi do vlakna. Stav ukolu se chatem NEMENI.

## UI v3 (g2007.soubor verze 3)
Klik na radek ukolu -> detail dialog: hlavicka (stav badge, domena, behu), timeline bublin dle autora, otevrene potreby s odkazy (vyresit / predat Mamince), chat pole "Napis Martince...", a TEPRVE TADY akcni tlacitka Schvalit/Vratit/Zrusit - schvalovani s plnym kontextem.

## OVERENO (3.8. 00:54, ukol #5): chat otazka "z ceho jsi vzala sazbu, proc 8800 a ne 8799, plati s DPH?" -> Martinka za 27 s dolozila zdroj (vybava od Maminky), vysvetlila floor logiku, a KOREKTNE priznala ze DPH sazbu nema a nemuze dolozit. Presne chovani potrebne pro bezpecne schvalovani.

## Pozn.
- Ukoly z doby pred vlakny maji timeline prazdnou - detail zobrazi fallback s ukol.vysledek.
- martinka_chat = plny run_goal beh (~30 s, bezi rozpocty) - chat neni "zdarma", pocitat s tim u SLA.
- Aktualni md5 vsech 8 skriptu kategorie martinky viz g2007.python (verze: chat 1, detail 1, zaloz 2, dispatch 3, potreba_vyres 2, schval 2, maminka_vybav 2, prehled 2).

