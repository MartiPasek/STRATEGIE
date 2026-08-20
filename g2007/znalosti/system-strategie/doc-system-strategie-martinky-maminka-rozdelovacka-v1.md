# Maminka-rozdelovacka: ukol bez domeny prideli Maminka dle profilu - NASAZENO+OVERENO E2E 3.8.2026 (Smer 1 KOMPLETNI)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co je nasazeno (#1692 + UI v5)
- martinka_ukol_zaloz v3 (md5 d160aece...): domain_kod je VOLITELNY - bez domeny vznika ukol ve stavu 'nezarazen' a event spousti maminka_pridel misto dispatche. UI v5: dropdown ma default "🌸 Nech Maminku vybrat (podle profilu)" + ruzovy badge stavu nezarazen.
- maminka_pridel v1 (md5 5937147e...): vezme 'nezarazen' ukoly, postavi Mamince katalog profilu (tool_domain.schopnosti + vytizeni front), jeji beh vybere domenu markerem [PRIDELIT domena=X] se [ZDUVODNENI] (jde do vlakna, typ 'prideleni' - AUDITOVATELNE, metrika "kolik prideleni clovek prehodil" je citelna z vlakna), nebo [NEVIM co=...] -> potreba typu 'chybi_martinka' + ceka_na_cloveka ("na tohle nemam Martinku"). Po prideleni event dispatch.

## OVERENO E2E (ukol #10, 3.8. ~11:10): CELY RETEZ SMERU 1
Ukol bez domeny ("orientacni cena rozvadece FLEX+ pro TESTFIRMA, kusovnik, 15kW") -> Maminka SPRAVNE pridelila kalkulace_specificka (zduvodneni: zakaznicka rada ABSAUGWERK, marze/floor dle kW - NE obecna kalkulace; profily vc. CO NEUMIM funguji) -> dispatch -> Martinka pouzila nastroj sve domeny (1 tool volani) -> kalkulace shodna s referencnimi behy (GESAMT 1185.18 / nabidnout 1190) -> ke_schvaleni.

## Stav smeru organizace-v2
SMER 1 (Maminka prideluje dle schopnosti): HOTOVO - profily, nastroje per domena, rozdelovacka. SMER 2 (Martinka vlastni oblast, automaty zakladaji ukoly): ceka na vecerni deploy okno (automat->ukol helper + registrace checku) dle doc-system-strategie-todo-martinky-vecerni-deploy-3-8. DALSI BLOK dle Marti: UI prehled nad celym systemem.

