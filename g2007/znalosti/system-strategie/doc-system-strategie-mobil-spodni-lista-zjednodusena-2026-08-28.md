# Mobil: spodní lišta zjednodušena — pruh „Zpět" i dva extra pruhy pryč, Nastavení mezi dlaždice (28. 8. 2026, dokončeno 31. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co se změnilo (zadal Jirka Honomichl, schválila Marti-AI msg 13953 a 13962)

Spodek mobilní aplikace (`#navwrap`) nesl až čtyři pruhy nad sebou. Zůstal jediný — navigační
lišta s ikonami `#bnav`. Na obrazovce Aplikace se výška spodku snížila ze 178 px na 65 px.

| pruh | dřív | teď |
|---|---|---|
| `#bnav` — Domů/Aplikace/Úkoly/Kontakty/Firma | vždy | **beze změny, vždy** |
| `#bnavback` — „← Zpět" | v prohlížeči (na Androidu i v iOS appce skryto) | **nikde**; zapnout jde jen `localStorage stg_backbar='always'` |
| `#bnavx1` — horní extra pruh | zobrazen na Aplikacích i na Firmě, **vždy prázdný** | **pryč všude** — na Aplikacích 28. 8. 2026, na Firmě 31. 8. 2026 (viz níže) |
| `#bnavx2` — dolní extra pruh | na Aplikacích jen ikona ⚙ Nastavení; na Firmě lišta skupin | na Aplikacích pryč; **na Firmě beze změny (skupBar)** |

Ikona Nastavení je nově **dlaždice v nové sekci „⚙️ NASTAVENÍ" úplně dole** na obrazovce Aplikace
(`35_apps_vedeni.js`, konec `buildApps`), volá `window.__M2W.selectTab("settings")`.

## Dokončeno 31. 8. 2026 — prázdný pruh zmizel i z Firmy

**Rozhodl Jirka Honomichl 31. 8. 2026, schválila Marti-AI (msg 14039), provedl Claude-28.**
Do té doby tu stálo, že `#bnavx1` na Firmě zůstává a čeká na rozhodnutí — **to už neplatí.**

Změna je jediný řádek ve zdrojovém dílku `apps/api/static/mobile_parts/74_claude27_render_init.js`,
ve funkci `renderNav()` ve větvi `if(firmaBar){`:

    puvodne:  window.__M2W.bnavx1.style.display="flex";
    nove:     window.__M2W.bnavx1.style.display="none";

Pruh se **nemaže, jen vypíná** (doporučila Marti-AI): HTML struktura zůstává, takže kdyby se do něj
někdy měl dávat obsah, vrátí se to jedním řádkem. Chování je teď symetrické — `none` v obou větvích.

**Ověřeno naživo po publikaci:** na Firmě má `#bnavx1` výšku 0 a `display:none`, celý `#navwrap`
klesl ze 178 px na **126 px** (úspora přesně 52 px), `--navh` se přepočítalo samo na 126px,
lišta skupin `#bnavx2` dál funguje (20 tlačítek) a hlavní lišta má 5 ikon. Sestavená stránka
narostla přesně o 65 znaků = délka doplněného komentáře, tedy nic jiného nezmizelo.

## Proč to šlo takhle přímočaře — klíčové zjištění

`#bnavback` je **sourozenec** lišty s ikonami ve stejném kontejneru `#navwrap`, a `renderNav()`
lištu s ikonami vždy naplní a zobrazí. **Tlačítko Zpět se proto nikdy nemohlo ukázat bez lišty
nad sebou** — ověřeno naživo na 7 obrazovkách (Domů, Aplikace, Moje osobní údaje, Banka, Úkoly,
Kontakty, Firma), všude 5 ikon. Jirkovo pravidlo „zmizet tam, kde je nad ním lišta" tedy
znamenalo „zmizet vždy".

`#bnavx1` se v celém obsahu appky **nikde neplnil obsahem** — jen se zobrazoval a bral 52 px.
Ověřeno 31. 8. 2026 znovu: všech šest jeho použití je jen deklarace, načtení do proměnné,
uložení do `window.__M2W`, `innerHTML=""` a přepínání `display`. Žádné `appendChild`.

## Pasti, na které narazíš

- **`#bnavx2` má na Firmě úplně jinou roli** než na Aplikacích — je to vodorovně posuvná lišta
  skupin (`skupBar()`, 20 tlačítek). Kdo smaže „ten pruh s Nastavením" plošně, rozbije Firmu.
  Měnit se smí jen větev `if(atApps){...}`, ne `else if(firmaBar){...}`.
- **Nezapisuj do `apps/api/static_db/mobile.html`** — to je sestavený artefakt. Zdroj je dílek
  `74_claude27_render_init.js`; do artefaktu se změna dostane až publikací.
- Odznak „nová verze" se na dlaždici **záměrně nedává** (rozhodla Marti-AI): dlaždice se kreslí
  jen při stavbě obrazovky, odznak by blikal. Informace zůstává na ikoně Aplikace v liště.
- Fragment `35_apps_vedeni.js` **nemá lokální alias na `selectTab`** — volat přes `window.__M2W`.
- Po publikaci se appka v prohlížeči sama znovu načte (`?fresh=…`) a chvíli není `window.__M2W`;
  není to chyba, jen se počká.

## Jak bylo ověřeno

**28. 8. 2026:** stažení živé `/mobile` před a po, porovnání počtů: funkcí 841 beze změny,
dlaždic 151 → 152, sekcí 21 → 22, `if(atApps){` 1 → 0, `if(firmaBar){` a `skupBar()` beze změny.
V prohlížeči ověřeno, že oba extra pruhy mají nulovou výšku, lišta má 5 ikon, dlaždice Nastavení
otevře Nastavení a lišta skupin na Firmě funguje (20 tlačítek).

**31. 8. 2026:** měření v DOM na živé `/mobile` (výšky `#bnavx1`, `#bnavx2`, `#bnav`, `#navwrap`
a hodnota `--navh`) plus kontrola délky sestavené stránky před a po publikaci.

## Dopad na lidi

V telefonech se nezměnilo nic — pruh „Zpět" tam byl skrytý už dřív a extra pruhy na Aplikacích
nikdo neztratí (Nastavení je o kus níž). Odstranění prázdného pruhu z Firmy pozná každý, kdo
tuhle obrazovku otevře: obsah dostal o 52 px víc místa. Nic se tím neztratilo — pruh byl prázdný.

Souvisí: [[doc-system-strategie-mobil-navh-spodni-lista]] · [[doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje]]

