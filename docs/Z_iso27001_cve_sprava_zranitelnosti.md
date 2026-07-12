# Správa technických zranitelností (ISO 27001 — A.8.8)

> **Verze:** 1.0 (návrh) · **Datum:** 21. 6. 2026 · **Entita:** STRATEGIE – System s.r.o.
> **Vlastník:** Claude + Marti (technika) · **Klasifikace:** Interní
> **Pokrývá:** A.8.8 (řízení technických zranitelností), návazně A.5.21 (ICT dodavatelský řetězec).

---

## 1. Cíl

Mít **definovaný, opakovatelný proces** detekce a řešení zranitelností v softwarových
závislostech STRATEGIE, s jasnými **lhůtami nápravy** podle závažnosti a s **auditním záznamem**
každého běhu. Auditor u A.8.8 chce vidět proces + důkaz, že běží — ne jen jednorázový sken.

## 2. Rozsah a nástroje

| Vrstva | Co | Nástroj | Pozn. |
|---|---|---|---|
| **Python závislosti** | `poetry.lock` (130 balíčků) | **pip-audit** (OSV/PyPI advisory DB) | hlavní |
| **Frontend** | vanilla JS, žádné npm balíčky | — | `package.json` neexistuje → není co skenovat |
| **OS / runtime** | Windows Server, Python 3.13 | Windows Update + Python patche | EUROSOFT infra + Marti |
| **MSSQL / PostgreSQL** | DB enginy | dodavatelské patche | ČMIS / EUROSOFT |

## 3. Příkaz ke spuštění (produkční poetry prostředí)

> **Pozn.:** scan se musí spouštět v prostředí se **stejným Pythonem jako produkce (3.13)**, jinak
> resolver selže na verzích vázaných na 3.13 (ověřeno: v Pythonu 3.10 padá na `numpy 2.4.4`,
> `audioop-lts`). Proto se pouští na cloud APP v poetry venv.

```powershell
# Na cloud APP (C:\Projekty\STRATEGIE), v poetry prostředí:
python -m poetry run pip-audit --desc --format columns
# strojově (pro archiv/CI):
python -m poetry run pip-audit --format json > C:\Data\STRATEGIE\cve\cve_%DATE%.json
```

pip-audit načte aktuální resolved prostředí (= co reálně běží), dotáže se na OSV/PyPI advisory DB
a vypíše balíček, zranitelnou verzi, ID (GHSA/CVE/PYSEC) a opravnou verzi (fix).

**Návrh: přidat jako pojmenovanou ops akci** `cve_scan` do whitelistu (`_OPS_ACTIONS`) →
spustí pip-audit na cloudu, výsledek uloží do `C:\Data\STRATEGIE\cve\` + audit `fw.ops_request`.
Tím se sken dělá z UI (rodič), bez ručního PowerShellu (doctrine #21), se stopou.

## 4. Cadence (frekvence)

| Spouštěč | Frekvence | Kdo |
|---|---|---|
| Plánovaný sken | **1× týdně** (scheduled task / ops akce) | automaticky → notifikace rodičům |
| Před/po deploy | při významné změně závislostí (`poetry.lock` diff) | součást deploy review |
| Ad-hoc | při zveřejnění závažné zranitelnosti (zero-day) | Claude/Marti |

## 5. Lhůty nápravy (SLA podle závažnosti)

| Závažnost (CVSS) | Lhůta opravy | Akce |
|---|---|---|
| **Kritická** (9.0–10.0) | **do 24 h** | okamžitý bump verze + deploy; pokud není fix, mitigace/izolace |
| **Vysoká** (7.0–8.9) | do 7 dní | naplánovaný bump v nejbližším deploy |
| **Střední** (4.0–6.9) | do 30 dní | zařadit do běžné údržby |
| **Nízká** (< 4.0) | do 90 dní / akceptovat | rozhodnutí + záznam (akceptace rizika) |

Oprava = `poetry update <balíček>` na opravnou verzi → `pip-audit` ověří → AUTO-DEPLOY
(py_compile gate + blue-green). Pokud oprava není dostupná: zaznamenat jako riziko (DOC-05)
+ mitigace (omezit expozici, virtual patch).

## 6. Záznam o běhu (auditní stopa A.8.8) — šablona

| Datum | Provedl | Nalezeno (K/V/S/N) | Opraveno | Akceptováno (s odůvodněním) | Odkaz na výstup |
|---|---|---|---|---|---|
| | | | | | |

Strojové výstupy `cve_*.json` se archivují (`C:\Data\STRATEGIE\cve\`), souhrn se zapíše do
tabulky výše (do DOC-11/registru rizik dle nálezu).

## 7. Stav a otevřené body

- ✅ Nástroj zvolen (pip-audit), frontend bez npm → bez expozice.
- 📋 **První ostrý běh** v produkčním poetry venv (T3) → vyplnit záznam §6.
- 📋 Přidat ops akci `cve_scan` + týdenní scheduled task + notifikaci rodičům.
- 📋 Zaznamenat SLA (§5) do politiky a odsouhlasit na management review.

---

*Návrh — promítne se do SoA A.8.8 a do registru rizik (DOC-05). Navazuje na `iso27001_dorazeni_2026.md` (§5 B12).*
