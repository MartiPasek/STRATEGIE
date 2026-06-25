# 🎨 Grafika pro Google Play listing

Vygenerováno 25. 6. 2026 (Claude). Generátor: `gen.mjs` (Playwright Chromium →
PNG v přesných rozměrech). Přegenerovat: `node docs/google_play_grafika/gen.mjs`.

## Hotové assety ✅

| Soubor | Rozměr | K čemu | Stav |
|---|---|---|---|
| `icon_512.png` | 512×512 | App icon (povinné) | ✅ hotovo |
| `feature_1024x500.png` | 1024×500 | Feature graphic (povinné) | ✅ hotovo |

Branding: logo STRATEGIE = 3 rostoucí sloupce teal→zelená (#2DD4BF/#34D399/#4ADE80)
+ datový bod (#A7F3D0) na tmavém podkladu — přesně dle ikony appky.

> Pozn.: Play si **app icon sám zaoblí** — proto je 512 plný čtverec, bez vlastního
> zaoblení. Důležitý obsah je v bezpečné zóně (od krajů).

## Screenshoty (min. 2, povinné) — 2 hotové, doplnit z účtu s daty 🟡

Screenshoty **musí ukazovat reálné obrazovky appky** (pravidlo Play). Pořídil
jsem je z **veřejného demo režimu** živého webu (`▶️ Vyzkoušet ukázku`, read-only,
1080×1920) a zarámoval do telefonu s titulkem.

**Hotové (reálné, listing-ready):**
| Soubor | Obrazovka | Titulek |
|---|---|---|
| `play_ss_1_moduly.png` | Aplikace (mřížka modulů) | „Všechny firemní moduly na jednom místě" |
| `play_ss_2_ukoly.png` | Úkoly / oznámení | „Úkoly a oznámení pod kontrolou" |

Surové záběry: `ss_tab_Aplikace.png`, `ss_tab_ukoly.png`.
Nástroje (reprodukovatelné): `_capture.mjs` (zachytí demo), `frames.mjs` (zarámuje).

**⚠️ Omezení demo režimu:** demo účet má **málo dat** → docházka, přehledy, firma
jsou prázdné/placeholder, a domovská obrazovka ukazuje **fotku (demo avatar)**,
která se na veřejný byznys listing nehodí. Proto z dema bohaté obrazovky nejdou.

**Doplnit (až bude účet s daty / přihlášený telefon):** docházka (vyplněný týden),
přehledy/FLOW, AI asistent, plán absencí. Postup: zachytit (systémový screenshot
nebo `_capture.mjs` s přihlášením) → prohnat `frames.mjs` (jen přidat řádky do SHOTS).
Ideálně mít **4–6** screenshotů.

## Další volitelné assety (Play je nevyžaduje pro start)
- Promo video (YouTube odkaz) — později.
- Tablet screenshoty — jen pokud budeme cílit i tablety.
