# RUNBOOK — Cloud Helios pro účetní (Peta + Martia) přes Guacamole, bez VPN

Architektura: prohlížeč → HTTPS **Caddy (188.11)** → **Guacamole (Docker, 188.11)** → RDP →
**Helios desktop (188.12, u DB)**. Helios zůstává u DB (svižné lokální SQL). 2 souběžní = 2‑user licence.

## A) Server 188.12 — Helios (Martiho ruka, RDP na 188.12)
1. Helios desktop klient — nainstalovaný ✓.
2. **Zapnout RDP** na 188.12; ve firewallu povolit RDP (3389) **jen z 188.11** (odkud chodí Guacamole).
3. Založit **2 Windows usery** `martia`, `peta` (běžní, ne admini). Ideálně shell = Helios (po loginu naběhne rovnou Helios), nebo jen zástupce + AppLocker (ať nevidí systém).
4. V Heliosu založit **2 Helios usery** (martia, peta) s právy na účetnictví/mzdy dle potřeby.

## B) Guacamole na 188.11 (Docker) — můj compose, spouští Marti
1. Ověřit Docker na 188.11 (`docker --version`); když není → doinstalovat (Docker Desktop / Engine).
2. `deploy/guacamole/` → vedle compose vytvořit **`.env`** (gitignored):
   ```
   GUAC_DB_PASSWORD=<silné heslo, NE do gitu>
   ```
3. **Init schéma** Guacamole DB (jednorázově):
   ```
   mkdir initdb
   docker run --rm guacamole/guacamole:1.5.5 /opt/guacamole/bin/initdb.sh --postgresql > initdb/initdb.sql
   ```
4. `docker compose up -d` → Guacamole na `127.0.0.1:8080` (jen lokálně).
5. **První login** `guacadmin/guacadmin` → hned změnit heslo, zapnout si TOTP.
6. V Guacamole admin:
   - **2 connections (RDP):** `Helios-Martia` a `Helios-Peta` → hostname `188.12`, port 3389,
     username `martia`/`peta`, „security mode: NLA", „ignore certificate: true".
     (Volitelně RemoteApp: parametr `remote-app` = `||helios` → účetní vidí jen Helios okno, ne plochu.)
   - **2 uživatelé** `martia`, `peta` → každý má přiřazenou JEN svou connection + vlastní **TOTP 2FA** (naskenují QR).

## C) Caddy na 188.11 (můj díl — přidat do Caddyfile + reload)
```
ucto.strategie-ai.com {
    @allowed remote_ip <IP_KANCELAR>/32 <IP_MARTIA>/32   # DOPLNIT IP
    handle @allowed { reverse_proxy 127.0.0.1:8080 }
    handle { respond "Forbidden" 403 }
}
```
- HTTPS + Let's Encrypt automaticky. **IP allowlist** = kancelář EUROSOFT + Martia (mzdy na netu).

## D) DNS
- A záznam **`ucto.strategie-ai.com` → veřejná IP cloudu (188.11 NAT/public)** — přidat u registrátora/Cloudflare.

## E) Zabezpečení (povinné — mzdy na internetu)
- TOTP 2FA na Guacamole (zapnuto v compose) · IP allowlist v Caddy · silná hesla Windows+Helios · RDP jen z 188.11 · (volitelně RemoteApp = jen Helios okno).

## F) Test
- Peta i Martia: `https://ucto.strategie-ai.com` → Guacamole login + 2FA → Helios desktop v prohlížeči. Ověřit 2 souběžné (licence).

## Co potřebuju od tebe (Marti), ať dokončím svůj díl:
1. **IP adresy** pro allowlist: kancelář EUROSOFT + Martia (účetní firma). [nebo potvrdit „jen 2FA bez IP" — ale doporučuju IP].
2. **Docker na 188.11** — je tam, nebo doinstalovat?
3. **DNS** `ucto.` — zařídíš A záznam (na veřejnou IP cloudu), nebo přístup k DNS máme kde?
