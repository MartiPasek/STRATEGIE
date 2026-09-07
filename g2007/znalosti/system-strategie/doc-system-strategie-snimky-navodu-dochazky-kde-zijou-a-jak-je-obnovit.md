# Snímky v návodu docházky — žijí v gitu (ne v databázi) a jak je bezpečně obnovit

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Snímky v návodu docházky — kde žijí a jak je obnovit

**Ověřeno 7. 9. 2026** při obnově po změně spodní lišty. Zadal Jirka Honomichl, provedl Claude-28.

## Kde žijí

`apps/api/static/navod_dochazka/*.png` — tedy **na disku a v gitu, NE v databázi.**
Rozhodl Jirka Honomichl 7. 9. 2026: *„obrázky do DB ne, ale mít je ve složce a tedy i na gitu."*
Ověřeno téhož dne: v `g2007.soubor` **není ani jeden obrázek** (52 živých artefaktů, všechny
textové) a `@@G2007PUBLISH` skládá jen textové soubory. Mění se běžným uložením a nasazením.

Odkazuje na ně `60_dochazka.js` (hlasový průvodce, pole `SL`, dvojice `{t, img, cap, v}`),
který **v databázi je** — takže změna odkazu na obrázek a výměna souboru jsou dvě různé cesty.

## Jak snímky pořídit

1. **Ukázkový (demo) účet na tohle nejde použít.** Vykresluje přes celou šířku červený pruh
   „UKÁZKOVÝ REŽIM — nepracujete s daty své firmy" a k tomu vyskakovací okno. Do návodu
   se to nehodí.
2. Fotí se tedy **z účtu skutečného člověka v prohlížeči**. Na obrazovky se přepínej příkazem
   `window.__M2W.stack=['home']; window.__M2W.selectTab('dochazka')` a **klikej jen přes kód**
   (`element.click()`), ne myší — část tlačítek na docházce odesílá akci hned prvním klepnutím.
   Bezpečné je rozbalit menu „Potřebuji ti něco říct…" a otevřít výběr zakázky nebo činnosti.
3. **Rozlišení:** na monitoru vyjde snímek asi **436 bodů na šířku** (appka má pevnou šířku
   a monitor má poměr 1:1). Původní snímky měly 780 bodů, protože se fotily z telefonu.
   Rozhodnuto 7. 9. 2026: **pravdivý a měkčí obrázek je lepší než ostrý a neplatný.**
4. **Zákaznická data:** výběr zakázky ukazuje skutečná čísla a názvy zakázek. Před focením
   názvy přepiš na neutrální (čísla můžou zůstat) — v živé appce je člověk vidí tak jako tak,
   ale ve statickém obrázku by zůstaly natrvalo i po skončení zakázky.

## Co nafotit nejde bez zásahu do dat

`pruvodce_odchod.png` (konec práce) a `pruvodce_potvrzeni.png` (potvrzení dne) ukazují stavy,
které existují jen když má člověk **rozdělanou směnu nebo nepotvrzený den**. Vyrobit je znamená
založit záznam v ostré docházce — 7. 9. 2026 se to proto **neudělalo** a zůstaly staré snímky.

## Past: popisek v liště je u každého jiný

Druhá ikona spodní lišty nese **křestní jméno přihlášeného člověka**. Žádný jediný snímek proto
není správný pro všechny — obrázek „kde docházku najdeš" ukazuje lištu s jedním jménem jako
příklad a text u něj musí říkat „ikona s **tvým** jménem", ne konkrétní jméno.

Souvisí: [[doc-system-strategie-mobil-spodni-lista-zjednodusena-2026-08-28]]

