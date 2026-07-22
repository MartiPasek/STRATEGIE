# G2007 — generováno z databáze

> **Tento strom je PROJEKCE databáze `g2007`.** Needituj ručně — změň DB a přegeneruj přes `/g2007/export`.
> Zdroj pravdy = databáze. Disk = výtisk na požádání.

- Nástrojů: **167** → [nastroje/_prehled.md](nastroje/_prehled.md)
- Kufrů: **5** → `kufry/`
- Entit: **5** → `entity/`
- Grafů: **2** → `grafy/`
- Snímků struktury: **1** → `struktura/`
- Znalostí: **145** v **14** oblastech → [znalosti/_prehled.md](znalosti/_prehled.md)

## Grafy (Krok 0)

- **haiku-v2** — Haiku — vrstva 2
- **marti-ai-md5** — Marti-AI MD5 V1.0

## Jak přispět znalost (pro Claudy i Marti-AI)

G2007 je hlavní sdílená znalostní báze. **Zdroj pravdy = DB `g2007.znalost`**, tenhle strom je jen projekce. Přispění je **jeden krok** endpointem (parent/cockpit, bez schvalovacího banneru):

```
POST /api/v1/erp/app/g2007/znalost-upsert
{ "oblast": "<kod>", "slug": "<slug>", "nadpis": "<titulek>",
  "zdroj": "docs/Z_<soubor>.md" }
```

Endpoint: přečte `docs/Z_<soubor>.md` → UPSERT do `g2007.znalost` (kód `doc-<oblast>-<slug>`) → export DB do `g2007/` → **uklidí `docs/Z_` inbox**. Postup: 1) napiš znalost jako `docs/Z_<slug>.md` a deployni ji, 2) zavolej endpoint, 3) hotovo — v DB, promítnuté sem, a `docs/Z_` uklizený.

Editace = zase jen dropni `docs/Z_<slug>.md` se stejným slugem → endpoint přepíše.

Oblasti (kód): `system-g2007`, `marti-ai`, `system-strategie`, `ucetnictvi`, `vyroba`, `mzdy`, `dochazka`, `projekty`, `nabidky`, `kalkulace-rozvadecu`, `bozp-po`, `tisax`, `iso27001`, `osoba`.

> Ruční cesta (fallback): INSERT do `g2007.znalost` přes most (`db=pg` → banner) + `GET /g2007/export?git=1`.
> Vektorizace (sémantické hledání nad znalostmi) zatím NENÍ — navazující krok.
