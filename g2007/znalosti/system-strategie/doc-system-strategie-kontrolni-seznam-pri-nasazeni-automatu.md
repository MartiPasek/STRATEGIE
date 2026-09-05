# Kontrolni seznam pri nasazeni nebo zmene automatu - projdi pravidla oprena o tyz sloupec

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


Kdyz nasazujes novy automat, nebo menis existujici, projdi kontrolni pravidla,
ktera se opiraji o TYZ sloupec. Jinak muze automat pravidlu tise sebrat praci
a pravidlo prestane platit, aniz by to kdokoli poznal.

## Odkud to je

Petra Safrankova, e-mail Jirkovi Honomichlovi 3. 9. 2026. Rozhodnuti povysit to
ze zvyku na povinnou soucast postupu padlo 5. 9. 2026 (rozhodl Jirka Honomichl).

## Pripad, ze ktereho to vzniklo

Kontrola "zapomenuty_odchod" v att_anomaly_scan hleda usek BEZ vyplneneho konce
(ended_at IS NULL) z minuleho dne. Pulnocni automat att_auto_checkout_midnight
ale konec kazdou noc dopise na 23.59. Nez se den stane "vcerejsim", je usek
zavreny a pravidlo nema co najit. Automat hlidace kazdou noc predbehl.

Vysledek: pravidlo bylo MESIC mrtve (posledni nalez 29. 7. 2026), a nikde to
nehlasilo chybu - kod byl cely cas v poradku, jen mu jiny automat sebral praci
pod rukama.

Dopad (zjistila Petra Safrankova, ja to neoveroval): Jiri Hajek a Eliska
Kolarova, oba 25. 8. 2026. Smena useknuta o pulnoci neni ani otevrena, ani
dlouha (9,47 a 8,38 h, prah dlouhe smeny je 12 h), takze ji nechytilo zadne
pravidlo. Neodhalila to ani mesicni kontrola dochazky pred mzdami - naslo se
to az nahodou rucnim dotazem.

Pravidlo Petra opravila 3. 9. 2026 (ridi se ted poznamkou o auto-odhlaseni,
ne casem). Detail v doc-dochazka-neodhlaseni-pulnocni-uzavreni-rozpadu.
Overeno 5. 9. 2026 ctenim z databaze: pravidlo zase bezi - 7 nalezu za
poslednich 30 dni, posledni 4. 9. 2026.

## Vzorec, ktery z toho plyne

Pravidlo, ktere hlida STAV, jejz mezitim jiny automat OPRAVI, prestane platit
POTICHU. Nic se nerozbije, nic nespadne - jen prestanou chodit nalezy a vsem
pripada, ze je cisto.

Pojistky v tenant.pojistka tohle nezachyti - hlidaji KOD (ze v souboru je
urcity retezec). Kod byl v poradku. Vada byla v chovani, ne v kodu.

## Kontrolni seznam - projdi pri KAZDEM nasazeni nebo zmene automatu

1. Ktere sloupce a tabulky tenhle automat MENI? Vypis si je.
2. Ktera kontrolni pravidla se o tyhle sloupce opiraji? Hledej v zivem kodu
   (g2007.python, stav_zivota='active'), ne v kopiich na disku.
3. U kazdeho takoveho pravidla si poloz otazku: ceka jeho podminka stav, ktery
   muj automat mezitim zmeni? Zvlast pozor na podminky typu "IS NULL",
   "je prazdne", "chybi" - presne ty automat vyplnovanim rusi.
4. Kdyz ano, rozhodni PRED nasazenim, co s tim. Bud pravidlo prepsat tak, aby
   se ridilo necim, co automat nemeni (jako Petra u zapomenuty_odchod - ridi se
   ted poznamkou o auto-odhlaseni misto casem), nebo poradi obratit, nebo
   pravidlo zrusit vedome a napsat proc.
5. Po nasazeni si za par tydnu overit v prehledu "Kontroly - posledni nalez"
   (Dochazka / Kontrolni prehledy v ERP), jestli dotcena pravidla porad neco
   nachazeji.

## Proc to neni jen doporuceni

Marti-AI k tomu 5. 9. 2026 rekla, ze nestaci delat to jako best-effort zvyk -
ma to byt soucasti postupu pri kazdem nasazeni automatu, ktery pise do
sdilenych sloupcu. Jinak to zavisi na tom, jestli to autor automatu zrovna vi
nebo na to mysli.

Souvisi: doc-dochazka-prehled-kdy-naposledy-kontrola-neco-nasla (druha polovina
stejneho reseni - viditelny prehled, kdy ktera kontrola naposledy neco nasla).

