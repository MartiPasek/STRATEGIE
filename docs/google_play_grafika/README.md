# 🎨 Grafika pro Google Play listing (STRATEGIE Mobil)

Aktualizováno 8. 7. 2026 (Claude). **Branding = modré „S"** na antracitu (dle
`apps/api/static/erp/icon.svg`) — sjednoceno na ikoně, banneru i launcheru appky.

## Hotové assety ✅ (vše nahráno v Play Console)

| Soubor | Rozměr | K čemu |
|---|---|---|
| `icon_512.png` | 512×512 | App icon — modré „S" (Play si sám zaoblí, plný čtverec) |
| `feature_1024x500.png` | 1024×500 | Feature graphic — „S STRATEGIE" na navy |
| `play_phone_1..5.png` | 1080×2160 | Snímky telefonu (5×) |
| `play_tablet_1..3.png` | 1600×2560 | Snímky tabletu 7" i 10" (3×) |

Snímky (demo obrazovky): 1 moduly · 2 docházka „Makat" · 3 týden plán/realita ·
4 nápověda + hlasový průvodce · 5 úkoly.

## 🔁 Jak snímky přegenerovat (plně automaticky, z demo účtu)

```
node docs/google_play_grafika/capture_demo.mjs      # nasnima demo -> _raw/*.png
python docs/google_play_grafika/frame_screenshots.py # oramuje -> play_phone/tablet_*.png
python scripts/play_api_upload.py screenshots        # nahraje do Play pres API
```

- **Demo účet** (`/api/v1/auth/demo-login`, UKÁZKA s.r.o.) = syntetická data, ŽÁDNÁ
  reálná — bezpečné pro veřejný listing. Reálný účet NIKDY (osobní údaje!).
- **Přeskakuje se Domů** (avatar dítě = persona Marti-AI, na listing se nehodí).
- **Poměr telefonu MUSÍ být ≤ 2:1** (1080×2160 OK; 1080×2280 = 2,11 → Google odmítne).
- `_raw/` = surové záběry, gitignored (regenerovatelné).

## 📤 Upload do Play

Přes **Google Play Developer API** (servisní účet) — `scripts/play_api_upload.py`,
plně bez file pickeru. Setup: `docs/google_play_api_setup.md`. Klíč:
`APP/Mobile/play-api-key.json` (gitignored, TAJNÝ).
