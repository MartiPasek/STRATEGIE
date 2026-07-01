# Vzdálený přístup účetní na cloud Helios (bez VPN) — Guacamole + Caddy

**Cíl (Marti 28.6.2026):** dva účetní uživatelé — **Martia** (externí účetní firma) a **Peta**
(naše Petra) — mají plný Helios **desktop** běžící na serveru u DB, přistupují **přes prohlížeč
na HTTPS, bez VPN**, vidí jen Helios (ne plochu serveru).
**Web klient iNuweb nestačí** (jen omezená agenda) → musí desktop přes web bránu.
Desktop licence Heliosu máme s rezervou → **IST netřeba, děláme my dva.**
**Pozn. licence:** 2 souběžní uživatelé (Martia + Peta) = sedí na 2‑user plovoucí licenci iNuvia.

## Architektura
```
prohlížeč účetní → HTTPS → Caddy (188.11) → Guacamole (Docker) → RDP → Helios desktop (Windows, 188.12 u DB)
```
- Helios desktop běží na Windows serveru **u databáze (188.12)** → SQL provoz zůstává lokální = rychlé.
- **Guacamole** = webová RDP brána (běží v Dockeru), překládá RDP do prohlížeče.
- **Caddy** (už máme) publikuje Guacamole na HTTPS subdoméně (Let's Encrypt).
- Bez VPN, bez instalace u účetní, bez RDS CAL.

## Kroky

### 1. Windows server (Martiho ruka — RDP na server)
- [ ] **Helios desktop klient** — nainstalovaný ✓ (potvrzeno).
- [ ] **Zapnout RDP** na serveru (Remote Desktop, povolit ve firewallu jen z Guacamole hostu).
- [ ] **Založit DVA Windows usery „martia" a „peta"** (běžní uživatelé, ne admini), omezené — ideálně:
      - přihlašovací skript spustí rovnou Helios (shell = Helios) NEBO jen zástupce na ploše,
      - AppLocker / omezení, ať nemají přístup k systému, jen Helios.
- [ ] V Heliosu založit **dva Helios uživatele** (martia + peta; přístup na účetnictví/mzdy dle potřeby a práv).

### 2. Guacamole (Docker — připravím compose, spustí se na hostu, co má Docker)
`docker-compose.yml`:
```yaml
services:
  guacd:
    image: guacamole/guacd
    restart: unless-stopped
  guac-db:
    image: postgres:16
    environment:
      POSTGRES_DB: guacamole
      POSTGRES_USER: guacamole
      POSTGRES_PASSWORD: __SILNE_HESLO__
    volumes:
      - ./guac-db:/var/lib/postgresql/data
    restart: unless-stopped
  guacamole:
    image: guacamole/guacamole
    depends_on: [guacd, guac-db]
    environment:
      GUACD_HOSTNAME: guacd
      POSTGRESQL_HOSTNAME: guac-db
      POSTGRESQL_DATABASE: guacamole
      POSTGRESQL_USER: guacamole
      POSTGRESQL_PASSWORD: __SILNE_HESLO__
      TOTP_ENABLED: "true"          # 2FA na bránu
    ports:
      - "127.0.0.1:8080:8080"        # jen lokálně, ven jde přes Caddy
    restart: unless-stopped
```
- **Dvě connection** v Guacamole: RDP → 188.12 jako `martia`, druhá jako `peta` (každý uživatel
  Guacamole vidí jen svou). „security: NLA", „ignore cert".
- **Dva Guacamole uživatelé** (martia, peta) — každý vlastní login + vlastní TOTP 2FA.
- (Volitelně: místo plné plochy publikovat přímo **RemoteApp Helios** — RDP param `remote-app`.)

### 3. Caddy reverse proxy (moje ruka — přidám do Caddyfile + deploy)
```
ucto.strategie-ai.com {
    @allowed remote_ip 1.2.3.4/32 5.6.7.8/32   # jen IP kanceláře / účetní
    handle @allowed { reverse_proxy 127.0.0.1:8080 }
    handle { respond "Forbidden" 403 }
}
```
- HTTPS + Let's Encrypt automaticky (jako strategie-ai.com).

### 4. Zabezpečení (mzdy na internetu — povinné)
- [ ] **Guacamole TOTP 2FA** (zapnuto výše) — účetní si naskenuje QR.
- [ ] **IP allowlist v Caddy** (jen kancelář + IP účetní).
- [ ] Silné heslo Windows usera + Helios usera; RDP jen z Guacamole hostu (firewall).
- [ ] (Volitelně) Guacamole „remote-app" → účetní nevidí plochu, jen Helios okno.

### 5. Test
- [ ] Martia i Peta otevřou `https://ucto.strategie-ai.com` → Guacamole login + 2FA → Helios desktop v prohlížeči.
- [ ] Ověřit, že 2 souběžní projdou (sedí na 2‑user licenci).

## Dělba práce
- **Marti (server, RDP):** RDP on, Windows useři `martia` + `peta`, dva Helios useři. Spustit `docker compose up -d` (compose dodám).
- **Claude:** docker-compose (2 connection + 2 Guac useři) + Caddy blok + DNS subdoména `ucto.` + zabezpečení + tento runbook + provedení krok za krokem.

**Hesla NIKDY v repu** — `__SILNE_HESLO__` doplnit lokálně / z trezoru.
