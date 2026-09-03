# Práh 0,1 h u „rozpad bez zakázky / bez činnosti" zrušen (Peťa 3.9.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Práh 0,1 h u „rozpad bez zakázky / bez činnosti" zrušen

> oblast: `dochazka` · zadala Peťa 3. 9. 2026, nasadil Claude-26

## Co bylo špatně
Pravidla `chybi_zakazka` (R7, Kristý 19. 8. 2026) a `chybi_cinnost` (R9, Peťa 27. 8. 2026)
hlásila jen úseky rozpadu **nad 0,1 h (6 minut)**. Minutové úseky, které vznikají
z dělení píchnutí, tím propadaly — za 14 dnů jich vzniklo deset a v žádné kontrole
je nikdo neviděl. Peťa 3. 9. 2026: *„musíme řešit i 0,01."*

## Co je nasazeno (`att_anomaly_scan` v23)
`COALESCE(w.hodiny, 0) > 0.1` → `COALESCE(w.hodiny, 0) > 0` na **všech čtyřech místech**:
v samotných pravidlech R7 a R9 **a v obou úklidových dotazech** nahoře. Kdyby se
změnilo jen pravidlo, nález by se založil a úklid by ho hned zase zavřel.

Nulové (nedokončené) úseky se dál nehlásí — podmínka je kladný počet hodin, ne nula.

## Kolik to přidá
V okamžiku nasazení **nic** — ověřeno dotazem, že v okně 14 dnů není ani jeden
kandidát pod 0,1 h bez nálezu. Všech deset minutových úseků se týž den srovnalo ručně
a příčina je opravená v kaskádě
([[doc-dochazka-kaskada-doplni-cinnost-z-predchoziho-useku]]). Pravidlo tedy chytá
jen to, co vznikne nově.

## Pozor
Okno kontroly zůstává **14 dnů** a nález na jeden záznam vzniká **jen jednou za život**
(`ON CONFLICT (tenant_id, rule, entry_id) DO NOTHING`). Co jednou někdo zavřel, se
nevrátí, i když příčina trvá — to je samostatná díra, zatím neřešená.

