# Oprava dat 17.8.2026 - duplicitni sick day Maresova 30.6. a dovolena 8h pri 7h uvazku u Duspivove

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Oprava dochazkovych dat 17. 8. 2026

**Zadal Jirka, schvalila Marti-AI.** Provedl Claude-28 pres SQL most (request #2146).
Zadny zaznam se nemazal fyzicky.

## A + B) Kristyna Maresova, 30. 6. 2026 - duplicita z planu nepritomnosti
Ten den mela sick day zapsany DVAKRAT, dohromady 12 h - a k tomu jeste home office 8 h.
- `att_entry` **6304780**, sickday 8 h, `source='plan_ec'`, note "z planu nepritomnosti",
  vzniklo 28. 6. = PREDPOVED -> **`status='superseded'`**
- `att_entry` **6304779**, homeoffice 8 h, tyz plan -> **`status='superseded'`**
- `att_entry` **9964191**, sickday 4 h, `source='manual'` / `source_system='centrala1'`,
  `source_id=1851872`, 08.00-12.00 = SKUTECNOST -> **ponechano beze zmeny**

Toho dne normalne pracovala (pichacky z mobilu 10.38-21.44), takze celodenni absence
z planu byla jen zastarala predpoved.

**Dopad:** sick days 2026 z 20 h na **12 h**. Misto "precerpano o 4 h" ji pri naroku
2 dny (16 h) **4 h zbyvaji**.

**Vzor:** stejny postup, jaky 12. 8. 2026 pouzila Peta s Claude-26 u Simony Urbanove
(`att_entry` 9408134) - vyradit pres `status='superseded'` + poznamka, ne DELETE.

## C) Zuzana Duspivova, 10.-14. 8. 2026 - dovolena 8 h pri sedmihodinovem uvazku
Pet zaznamu (`att_entry` 9999946-9999950) melo 8 h, jeji denni fond je 7 h.
- `hours` 8.00 -> **7.00**, casy 06.00-14.00 -> **08.00-15.00**, poznamka doplnena
- **`tenant.att_absence_request` id 78: `hours_per_day` 8.0 -> 7.0**

**Ten druhy krok je podstatny.** Zaznamy vznikly materializaci zadosti c. 78 a funkce
`_prepis_zadost` (`dochazka_absence_sprava.py:495`) pri prepoctu nejdriv SMAZE att_entry
te zadosti a zapise je znovu z `hours_per_day`. Kdyby se opravily jen zaznamy a ne zdroj,
oprava by vydrzela do prvniho prepoctu.

**Dopad:** vrati se ji **5 h dovolene** (0,71 dne); celkem 134 h -> 129 h.

## Overeni
Sken celeho roku 2026 pres vsechny lidi (soucet vacation+sickday za den vs. denni fond
z `engagement`/`work_mode`) pred opravou nasel presne tyhle dva pripady, po oprave
vraci **nula radku**.

## Pozor na pojmenovani pricin
Duspivove zaznamy **NEJSOU z Centraly**, i kdyz to tak na prvni pohled vypadalo.
Prisly z nasi **Spravy dochazky** (`source='absence'`, `source_system='absence_req'`).
Pricina je popsana zvlast v `doc-dochazka-sprava-dochazky-zapisuje-8h-misto-uvazku`.

## Pojistka `absence-bez-duplicit` je od 17. 8. 2026 ZELENA
Tahle pojistka drive svitila trvale cervene a byla vedena jako "znamy falesny nalez" -
ukazovala prave Maresovou z 30. 6. **Po dnesni oprave uz falesna neni: kontrolu jsem
pustil rucne a vraci `true`.** Kontroluje absence za poslednich cca 3 mesice a hlida,
aby soucet hodin jednoho druhu absence za den nepresahl 8.01 h.

**Dva starsi dokumenty ji jeste popisuji jako trvale cervenou** -
`doc-dochazka-zaverecne-overeni-rozpadu-dovolene` a
`doc-dochazka-stare-zadosti-na-marti-srovnani-16-8-2026`. Ten udaj je od 17. 8. **neplatny**;
neprepisoval jsem je, protoze je psala jina session. Plati tento dokument.
(Pojistka `g2007-soubor-vs-git` zustava falesne cervena dal - hlida pravidlo zrusene 5. 8.)

