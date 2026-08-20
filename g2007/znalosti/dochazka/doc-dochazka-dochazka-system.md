# Dochazka System

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Jeden systém att_entry (příchod/odchod/absence + zakázka); automat fond; skupina 24 = fond/den**

Docházka = tenant.att_entry (jeden systém): work bloky s project_ref=zakázka, absence, break. Zdroj: EC_Dochazka mirror ~5 min → att_entry + app píchání (mobile_app) + tablet + Centrála.
AUTOMAT /dochazka-automat: fond per úvazek (úvazek/5, JEN Po–Pá), dopíchávání/odpíchávání, kategorie.
ŽELEZNÉ PRAVIDLO (Marti ~8×): skupina 24 (dopichavat_fond) MUSÍ mít KAŽDÝ pracovní den PŘESNĚ fond (40h úvazek = 8,00/den). Strop přetažení + dopich prázdných, vč. Martiho/Honomichla.
GOTCHA: mirror STRATEGIE→EC docházky je VYPNUTÝ (přepisoval tablet, SumaDen se generuje měsíčně). Přehled = /prehled (vrstvený kalendář).

_Souvisi:_ absence-do-mezd

