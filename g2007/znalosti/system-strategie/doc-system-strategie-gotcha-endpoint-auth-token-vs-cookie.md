# GOTCHA: nove /app endpointy MUSI pouzit _uid_from_token_or_cookie, ne _get_uid (nativni appka = Bearer token, zadna cookie)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Problem (3.8.2026 vecer, Ridici centrum)

`POST /app/erp_registry/run` pouzival `_get_uid(req)` — ten cte JEN cookie `user_id`. PWA/prohlizec cookie ma → fungovalo. **Nativni Android appka zadnou cookie nema** — autentizuje se `Authorization: Bearer <token>` (HybridActivity.authedFetch, CardDAV device token) → 401 "Nejsi prihlasen" → v UI jen genericke "Nepodarilo se nacist". Marti to nemohl obejit ani reinstalaci/vycistenim.

## Pravidlo

Kazdy endpoint, ktery ma fungovat v mobilni appce, resolvuje uid pres **`_uid_from_token_or_cookie(req)`** (router.py ~134): umi Bearer token (user.carddav_token, sha256 hash, vc. shared_active a impersonace) I cookie fallback, plus ambasadorsky read-only rezim. `_get_uid` je cookie-only relikt — pro nove veci NEpouzivat.

## Diagnostika pristi
- "v PWA jde, v appce ne" = temer jiste auth cesta (token vs cookie), ne cache.
- `g2007.python_run_audit` loguje jen requesty s vyresenym uid — 401 pokusy tam NEJSOU (padaji driv).

Fix: commit 922de1971 (push 96280da76). Souvisi: doc-system-strategie-martinky-ridici-centrum-mobil-v1-nasazeno.

