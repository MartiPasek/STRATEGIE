# Mobil: spodní lišta zjednodušena — pruh „Zpět" i dva extra pruhy pryč, Nastavení mezi dlaždice (28. 8. 2026, dokončeno 31. 8. 2026; 7. 9. 2026 nové složení, jméno člověka místo popisku docházky a srovnaná nápověda)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co se změnilo (zadal Jirka Honomichl, schválila Marti-AI msg 13953 a 13962)

Spodek mobilní aplikace (`#navwrap`) nesl až čtyři pruhy nad sebou. Zůstal jediný — navigační
lišta s ikonami `#bnav`. Na obrazovce Aplikace se výška spodku snížila ze 178 px na 65 px.

| pruh | dřív | teď |
|---|---|---|
| `#bnav` — hlavní lišta s ikonami | vždy | **beze změny, vždy** (složení ikon se 7. 9. 2026 změnilo, viz rámeček na konci) |
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

## ⚠️ Od 7. 9. 2026 má lišta jiné složení — a je jich šest, ne pět

**Zadal Jirka Honomichl, provedl Claude-28.** Výčty ikon výše (a měření „všude 5 ikon")
popisují stav do 6. 9. 2026 — **jako datované pozorování zůstávají, ale už neplatí.**

Nové složení zleva: **🏠 Domů · 🕒 Moje docházka · 🏢 Firma · 🔔 Úkoly · 💡 Světla · Aplikace.**
*(Druhá položka se týž den odpoledne změnila na jméno člověka se siluetou — viz poslední oddíl.)*

- **👤 Kontakty ze spodní lišty zmizely** — jsou nově dlaždice na obrazovce Aplikace, sekce 🧑 MOJE.
- **🕒 Moje docházka je nově přímo v liště** (druhá zleva) a zároveň **zmizela z lišty skupin
  na Firmě**, kde do té doby byla posledním tlačítkem vpravo. Lišta skupin proto najíždí
  na začátek (`scrollLeft=0`), ne na konec.
- **💡 Světla jsou zatím bez cíle** — po klepnutí se záměrně nic nestane.
- Ikon je **šest**. ~~Popisek „Moje docházka" se jako jediný láme na dva řádky.~~ **NEPLATÍ od 7. 9. 2026 odpoledne** — popisek je nově jméno člověka, viz poslední oddíl.

Ověřeno naživo na `/mobile` po publikaci: pořadí sedí, docházka se z lišty otevírá,
lišta skupin na Firmě končí u „IT", konzole bez chyb, sestavená stránka má dál 31 skriptových
bloků a 139 dlaždic.

## ⚠️ Doplněno 7. 9. 2026 odpoledne — druhá ikona nese jméno člověka, ne slovo „docházka"

**Zadal Jirka Honomichl, schválila Marti-AI, provedl Claude-28.**

Druhá ikona zleva vede pořád na Moji docházku, ale:

- popisek **„Moje docházka" nahradilo křestní jméno přihlášeného člověka** (u uživatele 20 je to „Jiří"),
- **ikona hodin se změnila na siluetu postavy.**

Tím pádem **věty výše o popisku „Moje docházka" a o jeho lámání na dva řádky už neplatí.**

Jméno dává `g2007.python` kód `mobile_domu_stav` (vrací křestní jméno, příznak „je správce nebo
rodič" a stav přepínače); v dílku `74_claude27_render_init.js` ho čte `_navJmeno()`. Než odpověď
dorazí, drží se dočasně původní popisek, aby lišta neproblikávala prázdná. **Jádro se kvůli tomu
neměnilo** — volá se přes už existující adresu `/app/erp_registry/run`.

⚠️ **Vědomý ústupek, o kterém padlo rozhodnutí:** z lišty tím zmizelo jakékoli slovo „docházka"
i hodiny — a to zrovna ve chvíli, kdy se tam lidem cesta nově přesunula (viz oddíl výše).
Upozornily na to dvě instance nezávisle na sobě; **rozhodl Jirka Honomichl 7. 9. 2026**, že to
tak má být.

⚠️ **Past, která stála jedno kolo nasazení:** odpověď z `/app/erp_registry/run` chodí **zabalená**
ve tvaru `{ok, verze, vysledek:{…}}`. Kdo čte `j.jmeno` místo `j.vysledek.jmeno`, dostane
`undefined` a popisek **tiše zůstane původní** — nikde to nenahlásí chybu.

### Spolu s tím se opravila i nápověda docházky (7. 9. 2026 večer)

Změna popisku si vynutila opravu na dvou místech v `60_dochazka.js` — obojí se lidem **předčítá
nahlas**, takže rozpor by byl slyšet, ne jen vidět. **Rozhodl Jirka Honomichl** („nápověda
docházky je moje doména, oprav co je třeba"), schválila Marti-AI.

1. Věta v nápovědě „Docházku najdeš dole ve spodní liště: 🕒 Moje docházka" → nově
   **„druhá ikona zleva — je na ní tvoje jméno a panáček"**.
2. Snímek hlasového průvodce „Kde docházku najdeš" posílal lidi přes **Firmu**, odkud se
   tlačítko docházky týž den odstranilo — slepá cesta. Text i mluvené znění přepsáno na
   spodní lištu.

⚠️ **U toho snímku se odebral obrázek** (`img` prázdný, soubor `pruvodce_firma.png` na disku
zůstal). Ukazoval starý stav hned dvakrát — lištu ještě s Kontakty a tlačítko docházky na Firmě.
**Nový snímek udělat nejde:** popisek té ikony je u každého člověka jiné jméno, takže žádný
jediný obrázek není správný pro všechny. Text to unese sám.

⚠️ **Zbývá vědět:** ostatní obrázky průvodce (`pruvodce_prehled.png` a další, pořízené
5. 9. 2026) mají ve spodním okraji ještě starou lištu. Na obsah těch snímků to nemá vliv —
ukazují obrazovku docházky, ne cestu k ní — ale při jejich příštím pořizování to stojí za pohled.

Ověřeno naživo po publikaci: v liště je silueta a „Jiří", ostatní ikony beze změny, ostatní
obrazovky (Nastavení, Úkoly, Firma, Aplikace) se kreslí a konzole je bez chyb.

Souvisí: [[doc-system-strategie-mobil-navh-spodni-lista]] · [[doc-system-strategie-mobil-kde-se-edituje-a-jak-se-nasazuje]]

