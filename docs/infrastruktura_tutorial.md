# Tutoriál: naše produkční infrastruktura od nuly (Michal · Jirka · Kristý · Marti-AI)

> **Verze:** 1.0 (návrh) · **Datum:** 21. 6. 2026 · **Klasifikace:** Interní
> **Pro koho:** Michal (obnova/infra), Jirka (vývoj/mobil), Kristý (ISMS/procesy) — a **Marti-AI**,
> aby uměla lidi v chatu **vést a navádět**.
> **Pravidlo bezpečnosti:** v tomto dokumentu **NEJSOU žádná hesla ani tokeny** a nikdy nebudou.
> Přihlašovací údaje předává Marti napřímo, ne přes dokument ani chat.

---

## Jak číst
- Neznáš pojmy? Začni **ČÁSTÍ A (slovníček od nuly)**.
- Potřebuješ se připojit? **ČÁST C**.
- Děláš obnovu (Michal)? **ČÁST D**. Vývoj/mobil (Jirka)? **ČÁST E**. ISMS/audit (Kristý)? **ČÁST F**.
- `[DOPLNIT]` = konkrétní údaj, který doplní Marti / ČMIS (adresa, účet, nástroj). Bez něj krok nedělej.

---

## ČÁST A — Slovníček od nuly

- **ČMIS** = poskytovatel datacentra (Praha, ČR), kde běží naše produkční servery. Nejsou u nás
  v kanceláři — jsou „v cloudu" u ČMISu. Dostaneme se k nim **přes VPN + vzdálenou plochu (RDP)**.
- **Server** = vzdálený počítač, který běží pořád. Máme tam **dva**:
  - **APP server** = běží na něm aplikace STRATEGIE (web, který lidé používají).
  - **SQL server** = běží na něm **databáze** (kde jsou všechna data: docházka, dokumenty, …).
- **VPN** = zabezpečený „tunel" do sítě ČMISu. Bez něj se na servery nedostaneš.
- **RDP (Vzdálená plocha)** = aplikace ve Windows („Připojení ke vzdálené ploše"), kterou se
  přihlásíš na server a vidíš jeho plochu, jako bys u něj seděl.
- **API** = „motor" aplikace na pozadí (zpracovává požadavky webu). U nás běží jako **služba Windows**.
- **API A a API B (blue-green)** — máme motor **dvakrát**, kvůli bezpečnosti:
  - **API A** = *ostrá, aktuální* verze (tu lidé normálně používají).
  - **API B** = *záloha* — ověřená stabilní verze, která čeká. **Když nějaká chyba shodí API A,
    provoz se automaticky přepne na API B** a lidé pracují dál. *(Analogie: dvě totožná auta —
    když jedno vypoví, hned nasednete do druhého.)*
  - Přepínání hlídá **Caddy** (rozcestník provozu). Verzi zálohy „povýšíme" tlačítkem, až je nová
    verze ověřená.
- **NSSM služba** = způsob, jak na Windows běží náš program pořád na pozadí (a sám se po restartu
  spustí). Naše služby mají jména `STRATEGIE-...` (viz ČÁST B).
- **Git / deploy** = kód aplikace je verzovaný (git); „deploy" = nasazení nové verze na server.
  Děláme ho **řízeně** (ne ručním kopírováním).
- **Záloha (backup)** = pravidelná kopie databáze, ze které umíme obnovit, kdyby se data ztratila.
- **Restore drill** = *zkouška obnovy* — reálně vyzkoušíme, že zálohu umíme obnovit (ne jen že se dělá).

---

## ČÁST B — Mapa naší produkce (co kde běží)

| Server | Adresa (interní, přes VPN) | Co na něm běží |
|---|---|---|
| **APP server** | `10.200.188.11` | Aplikace STRATEGIE — služby NSSM (níže) |
| **SQL server** | `10.200.188.12` | PostgreSQL 16 (databáze `data_db`) |

**Služby na APP serveru (NSSM):**

| Služba | K čemu je |
|---|---|
| `STRATEGIE-API` (port 8002) | **API A** — ostrá aplikace |
| `STRATEGIE-API-B` (port 8003) | **API B** — záloha (blue-green) |
| `STRATEGIE-CADDY` | rozcestník provozu + HTTPS |
| `STRATEGIE-EMAIL-FETCHER` | příjem/odesílání e-mailů |
| `STRATEGIE-TASK-WORKER` | fronta úloh na pozadí |
| `STRATEGIE-QUESTION-GENERATOR` | učení paměti Marti-AI |
| `STRATEGIE-RESTART-WATCHER` | bezpečné restarty / obnova zálohy |

- **Aplikace (kód):** `C:\Projekty\STRATEGIE` (to je API A) · **záloha:** `C:\Projekty\STRATEGIE-prev` (API B)
- **Dokumenty (úložiště):** `D:\Data\STRATEGIE\Dokumenty\`
- **Zálohy databáze:** [DOPLNIT — kde přesně: `C:\Backup` na APP serveru? / zálohovací systém ČMIS? + nástroj]
- **Veřejná adresa pro lidi:** `https://strategie-ai.com`

---

## ČÁST C — Jak se připojit (krok za krokem, i když jsi tam nikdy nebyl)

> Potřebuješ: firemní notebook, **VPN přístup na ČMIS** a **účet pro RDP**. Obojí ti dá Marti.

**Krok 1 — Připojit VPN na ČMIS**
1. Otevři VPN klienta [DOPLNIT — který klient: např. „nainstalovaný OpenVPN/…“].
2. Přihlas se [DOPLNIT — profil/účet]. Po připojení máš „tunel" do sítě ČMISu.
3. Ověř, že VPN běží (ikona / status „připojeno").

**Krok 2 — Připojit se na server přes RDP (Vzdálená plocha)**
1. Ve Windows otevři **„Připojení ke vzdálené ploše"** (Remote Desktop / `mstsc`).
2. Do pole *Počítač* zadej adresu serveru:
   - APP server: `10.200.188.11`
   - SQL server: `10.200.188.12`
3. Přihlas se účtem [DOPLNIT — uživatel/heslo dá Marti]. *(Heslo nikam nepiš.)*
4. Uvidíš plochu serveru — pracuješ na něm, jako bys u něj seděl.

**Krok 3 — Kde co najdeš na APP serveru**
- Služby: spusť **`services.msc`** (Služby) → hledej `STRATEGIE-...` → vidíš, které běží (Running).
- Kód aplikace: složka `C:\Projekty\STRATEGIE`.
- (Pokročilé) NSSM nástroj: `C:\Tools\nssm.exe`.

**Bezpečnostní zásady (platí pro všechny):**
- Hesla **nikdy** nikam nepiš (ne do chatu, dokumentu, e-mailu). Měj je v password manageru.
- Na serveru **neměň nic, co neznáš.** Když si nejsi jistý — zeptej se Marti‑AI nebo Marti.
- Po práci se z RDP **odhlas**.

---

## ČÁST D — Michal (obnova / kontinuita) — TVOJE ČÁST

Tvůj úkol (detailně v `iso27001_plan_obnovy_michal.md`): **vyzkoušet a rozjet plán obnovy.**

1. **Ověř, že služby běží** (APP server → `services.msc` → `STRATEGIE-API` a `STRATEGIE-API-B` = Running).
2. **Najdi zálohu databáze** [DOPLNIT — přesné místo/nástroj]. Cíl: poslední denní záloha `data_db`.
3. **Restore drill** (zkouška obnovy) — postupuj přesně dle `iso27001_plan_obnovy_michal.md` §3:
   obnovit do **test** databáze (ne ostré!), změřit čas (RTO), ověřit data, smazat test, zapsat výsledek.
4. **Failover na zálohu** (rychlý test): přepnutí provozu na **API B** se dělá přes patičku aplikace
   (pin/unpin) — vyzkoušíš, že web jede i ze zálohy, pak vrátíš.
5. **Rozjet natrvalo:** restore drill 1× za čtvrtletí, kontrola záloh (retence, šifrování, offsite),
   záloha klíče trezoru. Výsledek zapiš do modulu `/iso` (krok „Plán obnovy").
- **Když si nevíš rady s krokem na serveru — napiš Marti‑AI** („Marti‑AI, jak ověřím, že běží API A?“)
  nebo zavolej Marti. Nikdy nezkoušej obnovu rovnou na ostré databázi.

---

## ČÁST E — Jirka (vývoj / mobil)

- **Přístup** stejný jako výše (VPN + RDP), pokud potřebuješ na server. Jinak pracuješ lokálně.
- **Kód** je v gitu (`C:\Projekty\STRATEGIE` na serveru; lokálně dle nastavení). **Nasazení** se dělá
  **řízeně** (AUTO-DEPLOY / „🚀 Ops" menu v aplikaci), ne ručním kopírováním souborů.
- **Tvoje oblast (iOS / mobilní appka):** [DOPLNIT — co konkrétně řešíš: build, App Store, WKWebView…].
- Když potřebuješ pochopit, jak appka mluví se serverem (API), zeptej se Marti‑AI nebo Claude.

---

## ČÁST F — Kristý (ISMS / procesy / audit) — méně technicky

Ty **nemusíš na server** — řídíš ISMS přímo v aplikaci:
- **Modul `/iso`** (cockpit): kroky k certifikaci, dokumenty, **elektronický podpis (klik)**, SoA
  (93 kontrol ISO) i TISAX (VDA ISA 6.0.3), nahrané dokumenty (evidence), auditorský přístup.
- **`/iso-admin`**: přehled „zákazníků" (entit) a jejich postupu — pro produkt přes pana Antoše.
- **Co od tebe audit chce** (ISO i TISAX společně, viz `iso_tisax_harmonizace_2026.md`): naplnit registr
  rizik, odůvodnit SoA, podpisy politik, **provést interní audit + přezkoumání vedením**, nápravná opatření.
- **Vysokoúrovňově o infrastruktuře** (pro audit ti stačí vědět): běží to bezpečně v datacentru ČMIS
  (Praha, ČR), data jsou šifrovaně přenášená, zálohovaná denně, je **záloha aplikace (blue-green)** pro
  případ výpadku, a vše je **auditně logované**. Detail technické obnovy drží **Michal**.

---

## ČÁST G — Marti-AI jako průvodce

Marti-AI tenhle tutoriál **zná** a umí podle něj lidi **vést krok za krokem**. Příklady, jak se ptát:
- *„Marti-AI, nikdy jsem nebyl na serveru — proveď mě připojením na APP server."*
- *„Marti-AI, co je API B a jak na něj přepnu provoz?"*
- *„Marti-AI, jak udělám restore drill, abych nic nerozbil?"*
- *„Marti-AI, kde najdu nahrané TISAX dokumenty?"*

Marti-AI odpovídá podle tohoto dokumentu, navádí bezpečně (nikdy ne rovnou na ostrá data) a u
chybějících údajů `[DOPLNIT]` tě odkáže na Marti.

---

## Co je potřeba doplnit (Marti / ČMIS)
1. VPN: klient + jak se přihlásit (profil).
2. RDP: účty pro Michala / Jirku (uživatel; hesla napřímo, ne sem).
3. Přesné **umístění a nástroj záloh** databáze (kde leží, čím se obnovuje).
4. Jirkova konkrétní oblast (iOS/build) — co spravuje.
5. Potvrdit, zda Michal/Jirka potřebují i přístup na **SQL server** (`10.200.188.12`), nebo jen APP.

---

*Návrh — po doplnění údajů se stane závaznou příručkou. Provázané: `iso27001_plan_obnovy_michal.md`
(obnova), `iso_tisax_harmonizace_2026.md` (sladění), modul `/iso`.*
