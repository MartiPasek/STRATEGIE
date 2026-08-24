# Cisla verzi iOS a Android appky jsou NEZAVISLA - nesynchronizuji se (24.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Cisla verzi iOS a Android appky jsou nezavisla

Navrhla **Marti-AI** (msg 13610, 24.8.2026), zapsal Claude-28 na rozhodnuti **Jirky Honomichla**.
Navazuje na `doc-system-strategie-ios-build-upload-a-past-dvou-contentview` (kapitola 7 Verzovani iOS)
a na `doc-system-strategie-vydavani-mobilni-appky-jen-obchody`.

## Pravidlo

**Verze se vaze na OBSAH vydani, ne na cislo v druhem obchodu.** iOS a Android maji jiny
cyklus, jine opravy i jinou cestu k vydani, takze shodne cislo je jen zdanliva parita,
ktera nic nerika. **Kazde vydani nese vlastni versionCode / build number podle toho,
co v nem opravdu je.**

Kdyz je potreba pri ladeni nebo podpore parovat, co presne clovek v telefonu ma,
pouzij **datum sestaveni nebo otisk commitu**, ne cislo verze.

**Vydani BEZ zmeny kodu jen kvuli srovnani cisla se nedela.** Duvody (formulace Marti-AI):
je to cisty kosmeticky release, obchod ho posle do kontroly, lidem prijde upozorneni
na aktualizaci a dostanou presne to same co meli; navic **preskoceny versionCode zustane
v historii buildu jako trvala dira**, ktera jednou nekoho zmate.

## Vyjimka, ktera se stala 24.8.2026 (a proc je zapsana)

Jirka se **vedome rozhodl jinak** a nechal Android vydat na 1.85 jen kvuli sjednoceni cisla
s App Store. Marti-AI to nedoporucila (msg 13610), po vysvetleni ale cestu i pravdive
poznamky k vydani schvalila (msg 13613) a zadne riziko pro uzivatele ani pro kontrolu
u Googlu v tom nevidela.

Stav po tom dni: **Play produkce 1.85 / kod 85** (kod 84 preskocen, presne ta dira vyse),
**App Store 1.85 / build 85** ve fronte na schvaleni. Nativni Android kod se pritom
od 1.83 (18.8.2026) **vubec nezmenil**.

**Poucení, ne zakaz:** pravidlo popisuje vychozi chovani. Rozhodnuti cloveka ma prednost -
ale kdyz padne, patri do poznamek k vydani **pravda** (u 1.85: "udrzbova verze, cislo verze
sjednocene s aplikaci pro iPhone, zadne nove funkce"), nikdy slib funkce, ktera tam neni.

## Mechanika, ktera k tomu patri (Android)

`APP/Mobile/app/build.gradle.kts` cte `APP/Mobile/version.properties` a **pri release buildu
si cislo sam zvysi o jedna** (`versionCode++`, posledni segment `versionName`).
**Chces-li vydat cislo X, zapis do souboru X minus jedna** a spust `scripts/build_aab.ps1`.

**Pred nahranim vzdy over cislo ve SKUTECNEM buildu**, ne v nazvu souboru (na to upozornila
Marti-AI): `APP/Mobile/app/build/intermediates/merged_manifests/playRelease/*/AndroidManifest.xml`
musi mit `android:versionCode` a `android:versionName`, ktere ocekavas. Play upload odmitne
cislo, ktere neni vyssi nez produkcni.

## Jak zjistit, co je v obchodech doopravdy (jen cteni)

Google Play: `androidpublisher` API klicem `APP/Mobile/play-api-key.json` - zalozit docasnou
editaci, precist `edits().tracks().get(track='production')` a **editaci zase zrusit**
(`edits().delete`), tim se nic nemeni. App Store: viz kapitola 4 znalosti
`doc-system-strategie-ios-build-upload-a-past-dvou-contentview`.

