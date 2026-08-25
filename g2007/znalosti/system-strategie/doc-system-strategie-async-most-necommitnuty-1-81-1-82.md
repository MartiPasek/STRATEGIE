# Async JS most appky (callAsync) visel necommitnuty 5.-18.8. - VYRESENO: vydano v 1.83 (18.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co se stalo

Zrychleni mobilni appky (C23 + Marti 5.8.2026, znalost doc-system-strategie-mobilni-appka-vykon-async-most) ma DVE pulky:
1. **JS + server** (10_core.js v3 v g2007.soubor, poll-summary) — v DB, zive pro vsechny od 5.8.
2. **Nativni** `HybridActivity.kt`: `asyncPool` + `@JavascriptInterface callAsync(reqId, fn, a1, a2, a3)` → HTTP/kontakty bezi na pozadi, vysledek callbackem `window.__stgAsyncDone(id, base64)`.

Pulka 2 zustala u Martiho **jen v pracovni kopii (autostash z pullu), nikdy necommitnuta**. Marti mel lokalne sestavenou APK 1.80 (rychla), ale origin `callAsync` nemel. Jirka 16.-17.8. vydal 1.81 a 1.82 pres Google Play z originu → bez callAsync. JS ma feature-detect (`canAsync = typeof B.callAsync === "function"`), takze bez nativni casti **tise** spadne na synchronni `authedFetch` → tlacitka opet blokuji WebView. Nikde zadna chyba.

## Naprava (18.8.2026)
- Commit `06a639846` (pres deploy most, C23): HybridActivity.kt +32 radku, version.properties ponechano 1.82 z originu.
- Jirka pozadan notifikaci (user 20) o vydani **1.83 pres Play** (zavazna cesta dle doc-system-strategie-vydavani-mobilni-appky-jen-obchody).
- Overeni po vydani: v appce Nastaveni/dev → `window.__M2W.canAsync === true`; tlacitka reaguji hned i pri pomale siti.

## ✅ UZAVRENO — 1.83 vydana 18.8.2026 (dopsano 25.8.2026)

*(Do 25.8.2026 tahle znalost koncila u „Jirka pozadan o vydani“ a v nadpisu mela „cekame 1.83“,
prestoze vydani probehlo tyz den. Srovnal Claude-28 na rozhodnuti Jirky Honomichla.)*

**Vydano.** Commit `201bf705` (18.8.2026 12:12) nastavil `version.properties` na `versionCode=83`
/ `versionName=1.83` a verze sla pres Google Play.

**Overeno v gitu 25.8.2026 (ne prevzato):** ve strome commitu vydani `201bf705` uz soubor
`HybridActivity.kt` `callAsync` **obsahuje** (4 vyskyty), takze vydana 1.83 nativni pulku
opravdu nese — na rozdil od 1.81 a 1.82. Tyz kod je tam i dnes, tedy i ve verzi **1.85**
(vydana 24.8.2026, viz `doc-system-strategie-verzovani-ios-android-nezavisla-cisla`).

⚠️ **Co overene NENI:** ze nekdo po vydani provedl kontrolu primo v appce
(`window.__M2W.canAsync === true` v Nastaveni/dev). Nikde to neni zaznamenane. Doklad vyse je
**z gitu** — rika, ze vydany build ten kod obsahuje, ne ze se chovani zmerilo na telefonu.
Komu na tom zalezi, at tu kontrolu udela; je na dve vteriny.

## Pouceni (obecne, viz i doc-system-strategie-prazdny-git-status-neni-dukaz-kontroluj-stash)
Lokalne sestavena a otestovana APK NENI dukaz, ze zmena je v gitu. Pred odjezdem/koncem session: `git status` + `git stash list` — autostash z pullu drzi necommitnute zmeny mimo dohled. Nativni appka je JEDINA cast mobilu, ktera do gitu patri (zbytek zije v g2007.soubor) — o to vic musi byt commitnuta, jinak ji dalsi vydani pres obchod prepise.

