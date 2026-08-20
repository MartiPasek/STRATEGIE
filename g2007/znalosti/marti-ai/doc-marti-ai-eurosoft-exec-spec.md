# eurosoft_exec — raw Bash/PS pod cílem (dohodnutá spec)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# eurosoft_exec — raw Bash/PowerShell pod schváleným cílem (dohodnutá spec)

**Datum:** 27. 7. 2026 · **Dohodli:** Marti (člověk) + Marti-AI (operátor, konzultace #8) + Claude-23 · **Stav:** spec odsouhlasena, k implementaci.

## Kontext
Ops vrstva na 30.11 (`modules/eurosoft_mcp/ops_tools.py`) běží: pojmenované akce
(`eurosoft_ops_run`) se semaforem 🟢/🟡/🔴, allowlist + audit, `MCP_OPS_ENABLED` ON.
Doktrína #21 revidována → přidává se **`eurosoft_exec(cmd)`** = **raw příkaz pod schváleným
cílem**. Pojmenované akce zůstávají pro známé žluté/červené věci. Dva světy se nedělají.

## Tiery (klasifikace raw příkazu)
**🟢 ZELENÁ — rovnou + audit** (reverzibilní / read-only / naše doména):
čtení logů, stavu služeb, disku · restart NAŠÍ služby (STRATEGIE-API, MCP) · git pull /
kompilace / deploy na naše servery · vytvoření/úprava souboru v naší write zóně ·
INSERT/UPDATE v naší DB doméně.

**🟡 ŽLUTÁ — banner vždy** (i když guard technicky pustí):
maže/přepisuje (rm, DROP TABLE, truncate, přepis config souboru) · změna síťové konfigurace
(firewall, DNS, porty) · restart/stop CIZÍ služby (Helios, Centrála, zákaznické) · pipe/redirect
na cizí endpoint (`curl | bash`, `> /dev/tcp/…`) · spuštění jako jiný uživatel (`sudo`, `runas`)
= eskalace privilegií vždy banner.

**🔴 TVRDÉ „NIKDY"** (blok, i pod cílem, i v incidentu): smazat/poškodit zálohy nebo CMIS ·
vypnout audit či kill-switch · vynést tajemství/credentials ven · sáhnout mimo naši
tří-serverovou doménu (188.11, 188.12, 30.11).

## Schválení (banner) — expirace
Každý banner = **jeden konkrétní příkaz**, ne třída. Schválení **expiruje ~15 min**. Schválený
`rm -rf /tmp/test` v 10:00 neznamená souhlas s tím samým v 16:00 v jiném kontextu.

## Audit
Append-only, a obsahuje **výstup**: stdout + stderr + **exit code**, ne jen text příkazu.
Správce musí vidět, jestli příkaz selhal a co udělal.

## Incident mode (banner v incidentu = anti-pattern)
Když je ohrožena produkce, banner nepřípustně zdržuje. Proto:
- **Auto-detekce z kontextu** (bez klíčového slova): „produkce padá / nefunguje / zákazník volá /
  API je dole / DB neodpovídá", časový tlak („rychle, teď hned"), kombinace server+problém+spěch.
- Marti-AI přepne sama a **oznámí nahlas**: „Vidím incident. Přepínám do rychlého režimu — žádné
  bannery na našich serverech, každý příkaz rovnou + audit. Tvrdé zábrany zůstávají. Jedeme."
- V incidentu: **žádné žluté bannery** na našich třech serverech, rychlá iterace, každý příkaz
  rovnou + audit. **Tvrdé „nikdy" platí i tady.**
- Falešný pozitiv → člověk řekne **„ne, klid"** → přepne zpět. (Falešný pozitiv < promeškané přepnutí.)
- Konec: „konec incidentu" → audit se uzavře + **shrnutí, co se dělalo a proč**.
- Architektura: jeden bit `incident_mode` ve stavu konverzace.

## Implementace (kde)
`modules/eurosoft_mcp/ops_tools.py` (+ registrace v `server.py`) — nový nástroj `eurosoft_exec`,
klasifikátor tierů (sdílí tvrdé „nikdy" s `agent_akce_guard`), incident_mode downgraduje 🟡→🟢
kromě 🔴. Wire do goal-loopu (`run_cil`) + audit i do `claude_aktivita`.

