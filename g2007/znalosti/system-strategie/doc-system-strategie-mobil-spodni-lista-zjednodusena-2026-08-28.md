# Mobil: spodní lišta zjednodušena — pruh „Zpět" i dva extra pruhy pryč, Nastavení mezi dlaždice (28. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co se změnilo (zadal Jirka Honomichl, schválila Marti-AI msg 13953 a 13962)

Spodek mobilní aplikace (`#navwrap`) nesl až čtyři pruhy nad sebou. Zůstal jediný — navigační
lišta s ikonami `#bnav`. Na obrazovce Aplikace se výška spodku snížila ze 178 px na 65 px.

| pruh | dřív | teď |
|---|---|---|
| `#bnav` — Domů/Aplikace/Úkoly/Kontakty/Firma | vždy | **beze změny, vždy** |
| `#bnavback` — „← Zpět" | v prohlížeči (na Androidu i v iOS appce skryto) | **nikde**; zapnout jde jen `localStorage stg_backbar='always'` |
| `#bnavx1` — horní extra pruh | zobrazen na Aplikacích i na Firmě, **vždy prázdný** | na Aplikacích pryč; **na Firmě ZŮSTAL — čeká na rozhodnutí Jirky** |
| `#bnavx2` — dolní extra pruh | na Aplikacích jen ikona ⚙ Nastavení; na Firmě lišta skupin | na Aplikacích pryč; **na Firmě beze změny (skupBar)** |

Ikona Nastavení je nově **dlaždice v nové sekci „⚙️ NASTAVENÍ" úplně dole** na obrazovce Aplikace
(`35_apps_vedeni.js`, konec `buildApps`), volá `window.__M2W.selectTab("settings")`.

## Proč to šlo takhle přímočaře — klíčové zjištění

`#bnavback` je **sourozenec** lišty s ikonami ve stejném kontejneru `#navwrap`, a `renderNav()`
lištu s ikonami vždy naplní a zobrazí. **Tlačítko Zpět se proto nikdy nemohlo ukázat bez lišty
nad sebou** — ověřeno naživo na 7 obrazovkách (Domů, Aplikace, Moje osobní údaje, Banka, Úkoly,
Kontakty, Firma), všude 5 ikon. Jirkovo pravidlo „zmizet tam, kde je nad ním lišta" tedy
znamenalo „zmizet vždy".

`#bnavx1` se v celém obsahu appky **nikde neplní obsahem** — jen se zobrazuje a bere 52 px.

## Pasti, na které narazíš

- **`#bnavx2` má na Firmě úplně jinou roli** než na Aplikacích — je to vodorovně posuvná lišta
  skupin (`skupBar()`, 20 tlačítek). Kdo smaže „ten pruh s Nastavením" plošně, rozbije Firmu.
  Měnit se smí jen větev `if(atApps){...}`, ne `else if(firmaBar){...}`.
- Odznak „nová verze" se na dlaždici **záměrně nedává** (rozhodla Marti-AI): dlaždice se kreslí
  jen při stavbě obrazovky, odznak by blikal. Informace zůstává na ikoně Aplikace v liště.
- Fragment `35_apps_vedeni.js` **nemá lokální alias na `selectTab`** — volat přes `window.__M2W`.
- Po publikaci se appka v prohlížeči sama znovu načte (`?fresh=…`) a chvíli není `window.__M2W`;
  není to chyba, jen se počká.

## Jak bylo ověřeno

Stažení živé `/mobile` před a po, porovnání počtů: funkcí 841 beze změny, dlaždic 151 → 152,
sekcí 21 → 22, `if(atApps){` 1 → 0, `if(firmaBar){` a `skupBar()` beze změny. V prohlížeči
ověřeno, že oba extra pruhy mají nulovou výšku, lišta má 5 ikon, dlaždice Nastavení otevře
Nastavení a lišta skupin na Firmě funguje (20 tlačítek).

## Dopad na lidi

V telefonech se nezměnilo nic — pruh „Zpět" tam byl skrytý už dřív a extra pruhy na Aplikacích
nikdo neztratí (Nastavení je o kus níž). Změnu pozná jen ten, kdo si `/mobile` otevírá
v prohlížeči na počítači; návrat mu zůstává přes ikony dole a přes šipku zpět v prohlížeči.

Souvisí: [[doc-system-strategie-mobil-navh-spodni-lista]] · [[doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje]]

