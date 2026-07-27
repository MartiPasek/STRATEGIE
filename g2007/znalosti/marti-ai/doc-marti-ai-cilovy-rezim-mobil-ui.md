# Cílový režim — mobilní UI (nativní obrazovka) + gotcha auth iframe vs nativní appka

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Cílový režim — mobilní UI (nativní obrazovka) + gotcha auth

Navazuje na `doc-marti-ai-cilovy-rezim-workflow-api`. UI Cílového režimu v mobilní appce (Kristý + C24, 24.7.2026). Ověřeno na PC i mobilu.

## Jak je to postavené
Obrazovka je **nativní modul appky** `apps/api/static/mobile_parts/73_zcil.js` (screeny `cil` = seznam, `cil_detail` = detail + přechody, `cil_new` = návrh), registrované do `SCREENS`. Dlaždice „🎯 Cíle" v `35_apps_vedeni.js` (sekce ŘÍZENÍ & SYSTÉM, jen rodiče `par`) volá `go("cil")`. Volá appkovou `api()` → `/app/cil*`. Commity `88823312` + `2e6017da`.

## ⚠️ KLÍČOVÁ GOTCHA — auth ve vnořené (iframe) stránce vs nativní appka
Nejdřív jsem to postavila jako samostatnou stránku `cil.html` + routa `/cil`, otevíranou přes `openInApp()` (iframe, `extview` v `30_contacts_settings.js`). **Na PC (web) to fungovalo, na mobilu hlásilo „Nejsi přihlášen" (401).**

Příčina (ověřeno v `_resolve_uid_raw`, router.py): **nativní appka se autentizuje `Authorization: Bearer <token>`** (CardDAV device token z `"user".carddav_token`), **ne cookie**. Web/PWA jede na cookie. Vnořená (iframe) stránka otevřená přes `openInApp` má opaque origin a hlavně **nevidí Bearer token** appky (nativní most `B.authedFetch` z iframu nedosáhne, ani `window.parent.B`) → cookie chybí → 401. **Týká se to VŠECH iframe app‑stránek na nativní appce** (ověřeno: Plán absencí atd. taky 401), ne jen Cílů.

**Řešení = nativní obrazovka** (mobile_parts modul registrovaný v `SCREENS`, volaný `go(...)`), která používá appkovou `api()` z `10_core.js` — ta jede přes `B.authedFetch` (token) na mobilu a cookie na webu. Funguje všude.

**Pravidlo pro příště:** cokoli v mobilní appce, co volá autentizované API a má fungovat i v nativní appce, stav jako **nativní `mobile_parts` obrazovku přes `go()`/`SCREENS`**, NE jako `openInApp("/stranka")` iframe. `openInApp` je OK jen pro věci, co snesou 401 na mobilu (nebo čistě web/PWA).

## Další gotchy
- **Zpět na Androidu:** `renderNav` (74) zobrazuje spodní lištu „← Zpět" jen když `stack.length>1 && (stg_backbar==='always' || !Android)` — **na Androidu je defaultně skrytá** (počítá se systémovým Zpět/gestem od levého okraje). Nativní obrazovka si proto má dát **vlastní viditelné „← Zpět"** (tlačítko volající `back()`) — jinak uživatel na Androidu žádné Zpět nevidí. (V `73_zcil.js` helper `_cilBack()` v každé obrazovce.)
- **Service worker cache:** po deployi statiky (mobile.html/partial) drží appka starou verzi i po restartu. Uživatel musí **Nastavení → 🧹 Vyčistit a načíst** (odregistruje SW + smaže cache). Zavření appky nestačí.
- Registrace do `SCREENS`: modul musí být v souboru, který se sesbírá **za** `73_pref_poptavka.js` (kde je `var SCREENS`) a **před** koncem IIFE v `74_claude27_render_init.js` → název `73_zcil.js`. Soubor za `74` by byl mimo closure.
- Build: `python scripts/build_mobile.py` slepí `mobile_parts/` → `mobile.html` (generovaný, needitovat přímo). Deploy partial + mobile.html spolu.

## Stav
Ověřeno end-to-end: PC (cookie) i mobil (token) — seznam, detail, přechody, vlastní Zpět. Backend endpointy beze změny (viz workflow-api doc).

