# Bez docházky - jeden příznak v podmínkách místo dvou skrytých evidencí

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Bez docházky — jeden příznak v podmínkách místo dvou skrytých evidencí

**Peťa + Claude-26, 28. 8. 2026.** Ověřeno v kódu i v datech, nasazeno.

## Pravidlo (Peťa)
Kdo docházku nevede, tomu se ani nekontroluje. *„Reálně je výsledek stejný — ať už
někomu řeknu, že mu doplní plný fond, nebo že mu nekontroluju docházku, ale stejně
mu dám celou výplatu za plný fond. Pro mě je to totéž."*

## Kde to je
Karta zaměstnance → **Podmínky a bonusy**, poslední řádek:
**„Bez docházky – nevede ji a nekontroluje se"**, roletka ANO / NE / — dědit —.

- číselník: `tenant.staff_cond_def`, kód `bez_dochazky`, kind `bool`, sort_order 140
- hodnota: `tenant.engagement.pod_bez_dochazky` (boolean, na platné verzi smlouvy)
- v kartě se nemuselo měnit nic — tabulka podmínek se celá kreslí z číselníku

## Co nahradil
Do 28. 8. žil „člověk bez docházky" na **dvou skrytých místech s různými lidmi**:

1. **seznam devíti osobních čísel natvrdo** (`'21','2','15','41','349','9005','9017','9030','9103'`)
   v `att_anomaly_scan` — opsaný u **tří pravidel z devíti**, ostatní pravidla výjimku
   neměla vůbec. **28. 8. odstraněn, nahrazen jednou globální výjimkou u zápisu nálezu.**
2. **`tenant.engagement.plny_fond_bez_dochazky`** — **mzdový** příznak. Řídí
   `att_day_summary_recompute`: vygeneruje plný fond za každý pracovní den a píchání
   ignoruje. **TENHLE SLOUPEC ŽIJE DÁL A JE TO SPRÁVNĚ.**

   ⚠️ **Poučení z 28. 8. 2026 — nespojovat kontrolu s mzdami.** Ten den se `pod_bez_dochazky`
   omylem zapojil i do `att_day_summary_recompute`, tedy do mzdového podkladu, a týž den
   se to **vrátilo zpět**. Peťa: *„vždyť se tak i jmenuje, nemá to ovlivňovat nic jiného."*
   Nezávisle na tom to zachytila Šárka Novotná a dala k tomu důvod, který nás nenapadl:
   **u hodinově placených se ty dvě věci rozejdou** — DPP placená za skutečně odpracované
   hodiny (typicky Herejtová) by s plným fondem dostala zaplaceno i za neodpracované
   hodiny. A obráceně, člověk na paušálu může potřebovat dál kontrolovat (zkušebka, BOZP).

   **Dělicí čára: „nekontroluje se" je o dohledu, „plný fond" je o mzdovém výpočtu.**
   Kontrolní místa (`att_anomaly_scan` včetně `den_nesrovnany_na_fond`, `att_prazdny_den_fond`,
   `dochazka_kontrola_data`) čtou `pod_bez_dochazky`. **Mzdový přepočet čte a musí číst
   `plny_fond_bez_dochazky`.** Šárka navrhla i minimální pojistku, kdyby to někdy někdo
   zase spojil: „plný fond" nikdy nesmí chytit poměr placený od hodiny (`engagement.hodinovka`).

## Kdo ho má (28. 8. 2026)
Pašek 2 a 41, Mózer 47, Vlková 361, Senft 374 (těch pět mělo i mzdový příznak),
nově **Šík 349** a **Honomichl 9030**.

**Marešová 21 (Týnka) ho záměrně NEMÁ** — docházku reálně vede (42 vlastních záznamů,
178,7 h za srpen) a kontrolovat se má.

**Mareš 9005, Svoboda 9017, Pillár 9103 ho záměrně NEMAJÍ.** Byli v seznamu devíti,
ale v `att_day_summary` nemají za srpen jediný řádek. Kdyby příznak dostali a zapojil
se do mezd, začal by jim vznikat plný fond 168 h měsíčně — vyrobila by se mzdová data
lidem, kteří žádná nemají. Jsou to OSVČ, kteří nepíchají (Mareš nikdy, Svoboda naposled
16. 6. 2026, Pillár 2. 7. 2026).

## Kdo příznak čte (stav 28. 8. 2026)
- `att_anomaly_scan` v15 — **jedna globální výjimka u finálního zápisu nálezu**, platí
  pro všech devět pravidel naráz. Měřeno na živých datech: ze 101 kandidátů dnes
  **61 patřilo lidem s příznakem** (dlouhá směna 38 z 52, práce při absenci 10 z 23).
- `att_prazdny_den_fond` v3 — fond dopíše (mzdy beze změny), ale **nezaloží nález ani
  nepošle zprávu na mobil**.

## Co ještě čeká
**Srpen je přepočítaný podle té chybné, už vrácené verze.** Než se stihlo vrátit, běžel
přepočet a Honomichlovi změnil srpen z 255,6 na 168,0 h a Šíkovi z 120,0 na 126,0 h.
Ti dva mzdový příznak NEMAJÍ, takže **při nejbližším přepočtu se jim čísla vrátí zpátky**.
Kdyby jim plný fond patřit MĚL, je to rozhodnutí o mzdovém příznaku, ne o tomhle
zaškrtávátku — a patří Šárce s Týnkou.

**Rozdělit to na dvě zaškrtávátka** (doporučila Šárka 28. 8.): druhé, „plný fond bez
docházky", by mzdový příznak přitáhlo do karty, aby byl vidět a nemusel se nastavovat
mimo ni. Zatím neuděláno.

## Gotcha
Systémová výchozí hodnota „NE" **nejde založit běžným zápisem** — `tenant.podminky_vychozi`
je POHLED nad širokou tabulkou `tenant.podminky_skupin`. Viz
[[doc-system-strategie-podminky-vychozi-je-pohled-zapis-nejde-precist]].
Proto se u nenastavených lidí ukazuje pomlčka; znamená to „nenastaveno" = nekontrolovaný není.

Souvisí: [[doc-dochazka-nocni-smycka-nalezu-a-zprav-prazdny-den]]

