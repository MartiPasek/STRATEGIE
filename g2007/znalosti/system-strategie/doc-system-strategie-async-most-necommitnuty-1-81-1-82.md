# Async JS most appky (callAsync) visel necommitnuty 5.-18.8. - vydane 1.81/1.82 ho nemaji, tlacitka zase pomala; commit 06a639846, cekame 1.83

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

## Pouceni (obecne, viz i doc-system-strategie-prazdny-git-status-neni-dukaz-kontroluj-stash)
Lokalne sestavena a otestovana APK NENI dukaz, ze zmena je v gitu. Pred odjezdem/koncem session: `git status` + `git stash list` — autostash z pullu drzi necommitnute zmeny mimo dohled. Nativni appka je JEDINA cast mobilu, ktera do gitu patri (zbytek zije v g2007.soubor) — o to vic musi byt commitnuta, jinak ji dalsi vydani pres obchod prepise.

