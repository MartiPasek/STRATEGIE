# Diktování hlasem (Whisper) — pattern a pasti na mobilu

> oblast: `system-g2007` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Diktování hlasem (🎙 → Whisper) — pattern a pasti, hlavně na mobilu

**Stav:** provozní znalost · 21. 7. 2026 · Claude‑24 (Kristý) — z reálného ladění diktování v CRM Plánu hovorů.

Sdílený pattern diktování napříč appkou + past s formáty, ať to příští instance neluští znovu.

## Kde se diktování používá (sdílený pattern)
Podrž tlačítko 🎙 a mluv → pusť → přepis do textového pole. Technicky: `MediaRecorder` (živý mikrofon) → base64 → `POST /api/v1/erp/app/transcribe` → OpenAI Whisper. Kód:
- `apps/api/static/mobile_parts/52_vyroba.js` — funkce `vyMic(ta, st)` (Výroba).
- `apps/api/static/mobile_parts/60_dochazka.js` — mic v Marti‑chatu (má **file‑fallback**, viz níže).
- `apps/api/static/crm-plan-hovoru.html` — funkce `micButton(ta, st)` (CRM Plán hovorů, doplněno 21.7.).
- Backend: `router.py` endpoint `/app/transcribe` (~ř. 21614) + `modules/media/application/whisper_provider.py`. **Whisper NETRANSKÓDUJE** — spoléhá na příponu názvu souboru.

## Whisper podporuje jen tyto formáty
`flac, m4a, mp3, mp4, mpeg, mpga, oga, ogg, wav, webm`. **NEpodporuje AMR ani 3gp/3gpp.** Backend `/app/transcribe` odvozuje příponu z `filename`/`mime` a AMR/3gp rovnou odmítá s hláškou „Formát záznamníku (…) Whisper nepodporuje".

## Past č. 1 — na PC OK, na mobilu ne
Na PC/desktopu jede živý `MediaRecorder` → **webm** (Whisper bere) → funguje. V **mobilní appce (Android WebView)** živý `getUserMedia` může házet **`NotReadableError`** (systémová/hardwarová věc — mikrofon nejde otevřít), i když appka má `RECORD_AUDIO` + grant v `onPermissionRequest` (`HybridActivity.kt`). Pak je nutný fallback na nativní záznamník.

## Past č. 2 — fallback na nativní záznamník → AMR
Fallback: `<input type="file" accept="audio/*" capture>` otevře nativní záznamník telefonu. **Ale některé Androidy nahrávají AMR** (potvrzeno u Kristý 21.7.) → Whisper vrátí `HTTP 400 Invalid file format`.
- **Nutnost:** frontend musí do `/app/transcribe` poslat **skutečný `blob.name`** ze záznamníku (ne vymyšlenou příponu jako „hovor‑audio.webm"). Jinak nesoulad obsah×přípona → Whisper 400. (Oprava commit `501daa76`.)
- Když je skutečný formát m4a/mp4/mp3/ogg/wav/webm → funguje. Když AMR/3gp → Whisper to nevezme ani se správnou příponou.

## Řešení AMR (ODLOŽENO — rozhodnutí Kristý 21.7.)
AMR jde vyřešit jen **převodem na serveru** (AMR→wav před Whisperem). Projekt schválně **nemá systémový ffmpeg** (pozn. v `pyproject.toml`). Doporučený způsob bez systémové instalace: pip balíček **`imageio-ffmpeg`** (bundluje ffmpeg binárku) → `subprocess` převod v `/app/transcribe`. Chce jednorázový `poetry install` + restart API na cloudu.
- **Rozhodnutí:** neřešit teď — Kristý diktování používat nebude, na PC jede. **Otestovat u Pavla** (obchodník) na jeho mobilu; když jeho telefon dělá m4a, půjde to i v mobilu, jinak teprve pak dodělat převod.

## Provozní pozn. z Coworku (doplněk k `doc-go-121-claude-operacni`)
- Bridge **cloud‑deploy** občas vrátí `HTTP 401 „Nejsi přihlášen"` (deploy token/session) — commit+push proběhne, ale cloud se nenasadí. Řešení: nasadit přes **🚀 v ERP** (parent session, pravý horní roh) nebo počkat na obnovu tokenu.
- Z Cowork session **nejde smazat `.git/index.lock` přes bash mount** („Operation not permitted") — musí ho smazat uživatel v PowerShellu: `Remove-Item C:\PROJEKTY\Strategie\.git\index.lock -Force` (doktrína #15; nikdy git přes bash mount).


