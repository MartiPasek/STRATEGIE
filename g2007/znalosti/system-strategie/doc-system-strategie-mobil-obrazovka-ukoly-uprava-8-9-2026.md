# Mobil, obrazovka Úkoly — dlaždice „Moje TODO" přejmenována na „Úkoly STRATEGIE", dlaždice úkolů ze staré Centrály odstraněna (8. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mobil, obrazovka Úkoly — úprava dlaždic 8. 9. 2026

**Zadal Jiří Honomichl 8. 9. 2026, schválila Marti-AI (msg 14965). Provedl Claude-28.**
Podnět vznikl z popisu obrazovky — dvě dlaždice vedly na obrazovky, které se obě nahoře
jmenovaly „Úkoly", takže po otevření nebylo poznat, ve které z nich člověk je.

## Co se změnilo

| dlaždice | dřív | teď |
|---|---|---|
| úkoly STRATEGIE | „Moje TODO" | **„Úkoly STRATEGIE"** |
| nadpis té obrazovky (`strtask`) | „✅ Úkoly" | **„✅ Úkoly STRATEGIE"** |
| úkoly ze staré Centrály | dlaždice „Úkoly / Z Centrály" | **odstraněna** |

Nadpis obrazovky se měnil spolu s dlaždicí schválně — sedí to s kontrolou
„text dlaždice proti nadpisu obrazovky" (`doc-system-strategie-kontrola-dlazdic-proti-nadpisum-obrazovek-6-9-2026`).

## Obrazovka `ecukoly` zůstala, jen bez cesty

Kód obrazovky úkolů z Centrály (`ecukoly` v `25_tasks.js`, registrace v `10_core.js`)
**se nemazal** — leží dál bez cesty, stejně jako `mytodo`, `phone` a `webview`
(`doc-system-strategie-mobil-obrazovky-bez-cesty-vyreseni-6-9-2026`). Důvod: Jirka
úkoly ze staré Centrály nepotřebuje, ale **případný přesun mezi úkoly STRATEGIE někdy
v budoucnu není vyloučen** — pak není co psát znovu. Jirka výslovně řekl, že se mu to
**nemá připomínat** jako otevřený úkol.

## Kde všude se starý název hledal (bod 14 / šest míst)

Podle `doc-system-strategie-prejmenovani-v-appce-kde-vsude-dohledat`:
obsah appky a webu, nápověda, poznámky v kódu, znalosti G2007, RAG směrnice, šablony.
Výsledek: v RAG směrnicích 0 výskytů, v `tenant.hr_template` 0 výskytů.
**„Moje TODO" zůstává na jednom místě schválně** — je to název MRTVÉ obrazovky `mytodo`,
což je jiná věc než přejmenovaná dlaždice (klasický případ „stejné slovo, jiná věc").
Znalosti, které `mytodo` popisují, se proto neopravovaly.

## Jak se to dělalo a jak se to ověřilo

Cílený zápis do `g2007.soubor` přes most s pojistkou na otisk
(`AND md5(obsah)='…'`), diakritika přes base64, kotvy předem ověřené, že jsou
v souboru právě jednou. Před složením artefaktu kontrola, že nečeká cizí nepublikovaná
práce (nečekala). Pak `@@G2007PUBLISH apps/api/static_db/mobile.html` (verze 159 → 160)
a **otevření živé `/mobile` v prohlížeči** — na obrazovce je pět dlaždic místo šesti
a nadpis uvnitř sedí.

⚠️ Past, na kterou se narazilo: **výpis z mostu slepí zalomení řádků na mezery**, takže
kotvu složenou podle výpisu nelze použít. Přesné bajty se musí vytáhnout jako base64
a rozkódovat u sebe — teprve pak je vidět, kde je konec řádku a kde odsazení.

## Co zůstalo otevřené (jinde)

Otevření **Řídícího centra i správcům** (`users.is_admin`) je samostatná věc — čeká
na rozhodnutí rodiče, viz `doc-system-strategie-ridici-centrum-pro-spravce-zadost-8-9-2026`.

