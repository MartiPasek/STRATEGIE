# Cloud Helios pro účetní přes prohlížeč — co dodělat (pro Michala)

**Kdy:** pondělí (potřebuju tvůj přístup k DNS) · **Odhad:** ~15 minut tvého času · **Stav:** lokálně už všechno běží, zbývá poslední krok = zveřejnit přes HTTPS.

---

## Proč to děláme

Účetní **Martia** (externí účetní firma) a **Peta** potřebují pracovat v **Heliosu**, ale:
- Helios desktop běží na cloudu (server **188.12**, u databáze — aby byl SQL provoz rychlý).
- Nechceme jim dávat **VPN** ani nic instalovat na jejich počítače.
- Web klient Heliosu (iNuweb) má jen omezenou agendu → potřebují **plný desktop**.

**Řešení:** webová brána (Guacamole), která Helios desktop „promítne" do běžného prohlížeče. Účetní jen otevře odkaz, přihlásí se, a má Helios v okně prohlížeče. Žádná VPN, žádná instalace.

---

## Jak to funguje (architektura)

```
prohlížeč účetní  →  HTTPS (Caddy, 188.11)  →  Guacamole (Docker, 188.11)  →  RDP  →  Helios desktop (188.12)
```

- **188.11** (APP server) = brána do internetu, už na něm běží Caddy + `strategie-ai.com`.
- **188.12** (DB server) = tam běží Helios desktop, ke kterému se účetní přihlašují.
- Guacamole běží v Dockeru na 188.11, dostupné jen lokálně (`127.0.0.1:8080`) — ven půjde **výhradně přes Caddy** (HTTPS).

---

## Co už je hotové (30.6., otestováno)

- ✅ Guacamole běží na 188.11 (Docker/WSL2), 3 kontejnery, port `localhost:8080`.
- ✅ Dvě připojení na Helios (188.12) — pro Martiu a pro Petu.
- ✅ Na 188.12 zapnuté RDP + Windows účty obou účetních + zástupci Heliosu.
- ✅ Vyzkoušeno lokálně: Helios desktop naběhl v prohlížeči.

---

## Co potřebuju od tebe, Michale (pondělí)

**Hlavní (a vlastně jediná) věc — DNS záznam:**

Přidej u registrátora/DNS **A záznam**:

| Název | Typ | Hodnota |
|---|---|---|
| `ucto.strategie-ai.com` | A | **stejná veřejná IP jako `strategie-ai.com`** |

To je celé. Míří to na tu samou veřejnou IP cloudu, na které už dnes jede `strategie-ai.com` — jen nová subdoména pro tuhle bránu.

**Ověř prosím ještě:**
- Že na tu veřejnou IP **chodí port 443** na 188.11 (mělo by, protože `strategie-ai.com` přes HTTPS funguje — pokud ano, není co řešit).

---

## Co dodělám já (Claude / Marti) hned po DNS

- **Caddy blok** pro `ucto.strategie-ai.com` → reverse proxy na `127.0.0.1:8080` (HTTPS + Let's Encrypt automaticky, stejně jako u hlavní domény).
- **Zapnout zpět 2FA** na bráně (pro testování bylo dočasně vyplé).
- Až budeme znát IP účetní firmy → přidat **IP allowlist** (jednoduchá změna v Caddy).

---

## Zabezpečení (mzdy/účetnictví na internetu — bereme vážně)

- **HTTPS** (Let's Encrypt) — žádný nešifrovaný provoz.
- **2FA** na přihlášení do brány (TOTP — Microsoft/Google Authenticator, zdarma).
- **RDP na 188.12 jen z 188.11** (ne z internetu).
- Účetní mají **běžné, ne admin** účty; vidí jen Helios, ne systém.
- Později **IP allowlist** (kancelář EUROSOFT + účetní firma).

---

## Checklist pondělí

- [ ] Michal: A záznam `ucto.strategie-ai.com` → veř. IP cloudu
- [ ] Michal: ověřit průchodnost 443 na 188.11
- [ ] Claude/Marti: Caddy blok + reload
- [ ] Claude/Marti: zapnout 2FA na bráně
- [ ] Test: Martia + Petra otevřou `https://ucto.strategie-ai.com` → 2FA → Helios v prohlížeči
- [ ] Až bude IP účetní: doplnit IP allowlist

---

*Detailní technický runbook (pro případ, že bys chtěl koukat hlouběji): `deploy/guacamole/RUNBOOK.md`.*
