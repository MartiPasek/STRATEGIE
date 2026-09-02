# Velikosti pisma v mobilu se sjednocovat NEBUDOU - rozhodl Jirka Honomichl 2. 9. 2026

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Velikosti písma v mobilní appce se sjednocovat nebudou

**Rozhodl Jiří Honomichl, 2. 9. 2026.** Píšu to sem výslovně jako rozhodnutí, ne jako popis
stavu — jinak to za pár měsíců někdo najde jako nedodělek a bude to navrhovat znovu.

## Co se rozhodovalo

Appka má **29 různých velikostí písma** a **12 poloměrů rohů**. Byl připraven návrh sjednotit
písmo na šestistupňovou škálu 12 / 13 / 15 / 18 / 22 / 28. Návrh vznikl výpočtem — ze osmi
kandidátů byla vybraná ta, která nejméně hýbe současným stavem (443 výskytů beze změny,
mění se 308, většina o jeden pixel).

K posouzení bylo vyrobené srovnání před a po na čtyřech obrazovkách. Nešlo o kreslené návrhy,
ale o skutečné vykreslení živé appky s dočasně přepsanou velikostí písma.

## Rozhodnutí

**Nedělá se.** Jirkovo zdůvodnění: *„já v tom nevidím rozdíl."*

To je platný a dostatečný důvod. Změna by měnila 308 míst v appce, kterou denně používá
kolem šedesáti lidí, a přínos by byl **výhradně pro toho, kdo appku udržuje** — uživateli
by nepřinesla nic viditelného. Změřeno navíc bylo, že na obrazovce docházky by se tři popisky
zalomily na dva řádky, tedy drobné zhoršení.

## Co se naopak UDĚLALO a platí

Sjednotilo se jen to, co **není vidět**:
- velikosti písma 36 na 29 (sloučeny půlpixely, například 13,5 na 13),
- poloměry rohů 19 na 12 (sloučeny rozdíly do 1 px, například 9 na 10).

Tuhle část nikdo nepozná a je nasazená.

## Pro příště

Kdyby se k tématu někdo vracel, potřebuje **nový souhlas Jirky**, ne odkaz na tenhle rozbor.
Doporučený způsob, kdyby se rozhodl jinak: **stupnici zavést jako pravidlo pro nové obrazovky**
a staré převádět při každé úpravě, ne jedním velkým přepisem.

Podklady zůstaly na Jirkově síťové složce ve složce STRATEGIE-mobil-design-2026-09-01
(soubor typografie_navrh.html se srovnáním před a po).

## Související

- [[doc-system-strategie-mobil-pojmenovane-barvy-a-struktura-stranky]] — co se naopak sjednotilo
- [[doc-system-strategie-audit-vzhledu-mobilni-appky-postup]] — čím se vzhled měří

