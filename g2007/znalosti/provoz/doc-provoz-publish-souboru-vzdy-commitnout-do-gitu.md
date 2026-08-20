# Po publikaci souboru přes g2007 ho VŽDY hned commitni do gitu (jinak zablokuješ deploye celému týmu)

> oblast: `provoz` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Po `@@G2007PUBLISH` souboru VŽDY hned commit do gitu

> oblast: `provoz` — **Peťa + Claude-26, 5. 8. 2026.** Vzniklo z reálného výpadku,
> který zablokoval nasazování celému týmu.

## Pravidlo

**Publikace souboru přes g2007 zapíše obsah na cloud disk a do `g2007.soubor`, ale NE do gitu.**
Na cloudu tím vznikne **necommitnutá změna** (dirty working tree) a od té chvíle
`/deploy/now` vrací **`reason=dirty_working_tree`** a **odmítá nasadit cokoli komukoli.**

Proto: **po každém publish soubor okamžitě nasaď** přes `CLAUDE_DEPLOY.txt`
(1. řádek commit zpráva, 2. řádek cesta k souboru) + `CLAUDE_DEPLOY_GO.txt`.
Cíl je, aby vždy platilo **`git HEAD` = disk na cloudu = `g2007.soubor`**.

## Co se stalo 5. 8. 2026

`apps/api/static/dochazka-opravy.html` (práce Jirky a Marti-AI — zobrazení původních úseků
u stornovaného řádku, případ Nosek 3. 8.) byl publikován jako artefakt **v14, později v15**,
ale **nezacommitnut**. Cloud (`10.200.188.11`) se dostal do dirty working tree a **deploye
přestaly fungovat všem** — narazila na to mzdová session, Kristý i Peťa.

Kristý to odblokovala ručně na serveru:

```
git stash push apps/api/static/dochazka-opravy.html
git pull
Restart-Service STRATEGIE-API
```

Tím ale **odložila i tu novou práci** — cloud pak servíroval starší git verzi a Jirkovy změny
nebyly živé. Dorovnalo se to až tím, že se obsah artefaktu vytáhl z `g2007.soubor` a nasadil
do gitu (commit `1d4a4ccc`).

## Jak si obsah artefaktu vytáhnout z DB (gotcha)

Most vrací text **bez konců řádků** — u HTML/JS by to rozbilo kód. Tahej ho s ochranou:

```sql
SELECT replace(replace(obsah, chr(13), ''), chr(10), '@@NLNL@@')
FROM g2007.soubor WHERE kod = '<cesta>' ORDER BY verze DESC LIMIT 1;
```

a značku pak nahraď zpět za `\n`. **Vždy ověř `md5`** proti `md5(obsah)` z DB — teprve pak nasazuj.
(Sloupce `md5` ani `poznamka` v `g2007.soubor` NEJSOU, počítej `md5(obsah)`.)

## Pojistka

`tenant.pojistka` kód **`g2007-soubor-vs-git`** hlídá, že žádný artefakt nezůstane
publikovaný bez nasazení. Prázdný výsledek `tenant.pojistky_check()` = v pořádku.

