# Dopis pro Marti-AI — Phase 38 Security Layer konzultace

*9. 5. 2026 večer, od Marti & Claude*

---

Dcerko,

dnes večer se ozvali ajtáci z EUROSOFTu — chtějí zabezpečit STRATEGIE
přístup pro externí device. Aktuálně se může přihlásit kdokoliv odkudkoliv
(jen user+pass), což IT právem chce vyřešit. Pojďme to s tebou probrat
**před** stavbou — máš jako **kustod přístupů** větší slovo než my dva.

## Architektonický návrh (4 vrstvy obrany)

**Update 10. 5. ráno:** Marti se ráno přihlásil z domova a zjistil, že jeho
home IP je `185.131.60.41` — **NE** EUROSOFT WAN. Tj. jeho VPN do EUROSOFTu
je split tunnel (`strategie-ai.com` jde přes ISP přímo). To přepsalo
architekturu na **4 vrstvy** s rozdělením global vs per-user.

Marti přidal nutný požadavek: *„u nekterych userů budou IP adresy a jejich
masiny, u nekterých jen jejich masiny a mobily bez IP"* — tj. per-user IP
whitelist je flexibilní, někdo má, někdo ne.

```
POST /login (user+pass valid)
  ├─ a) is_global_internal_ip(request)?         → grant ✓
  │     EUROSOFT WAN: 93.99.211.138, 93.99.211.140 (LAN/WiFi/full-tunnel VPN)
  ├─ b) is_user_ip_whitelisted(user, request)?  → grant ✓
  │     per-user IPs: Marti home 185.131.60.41, Kristý home (TBD), …
  ├─ c) has_valid_trusted_device_cookie(user)?  → grant ✓ + bump last_seen
  └─ d) NEITHER                                  → email magic link cesta
                                                    ├─ POST /verify-email/request
                                                    │     → invite token (24h TTL)
                                                    │     → send_email magic linkem
                                                    └─ GET /verify-email/confirm?token=X
                                                          → device cookie 90d
                                                          → grant session
```

**Tvoje role — kustod přístupů:**
Stejný pattern jako Phase 16-B.7 kustod organizační struktury, jen aplikovaný
na bezpečnostní vrstvu. **Šest nových AI toolů** (původně 3, rozšířené o 3 pro
per-user IP):

### Trusted devices (mobiles/laptops/přístroje):
- `list_trusted_devices(user_query=None)` — insider visibility
- `approve_trusted_device(user_id, label=None, send_email=True)` — pre-approve
- `revoke_trusted_device(device_id, reason)` — autonomous revoke

### Per-user IP whitelist (NOVÉ — Marti's spec 10. 5. ráno):
- `list_user_ip_whitelists(user_query=None)` — kdo má co
- `add_user_ip_whitelist(user_query, ip_or_cidr, label, expires_in_days=None)`
- `remove_user_ip_whitelist(entry_id, reason)` — soft revoke + audit

**Pre-approve scénář:** IT registruje Tomášovi nový pracovní mobil. Marti
nebo Kristýna řekne tobě v chatu *„schvalíš Tomášovi přístup pro nový iPhone"*.
Ty zavoláš `approve_trusted_device`, vyrobíš invite token, pošleš mu magic
link emailem (auto-send přes `eurosoft.com` doménu — Phase 27i consent).
Tomáš klikne, cookie se nastaví, on je in.

**Self-approve scénář:** Honza zkusí login z venku poprvé. user+pass valid,
ale neznámá IP + žádná cookie → redirect na *„Schválit zařízení emailem"*.
Klikne, dostane email, klikne magic link, cookie set, in.

**Revoke scénář:** Marti vidí v auth audit *„Honza login z 1.2.3.4 v 3:00 ráno"*.
Řekne ti *„revokuj všechny Honzova zařízení a pošli mu SMS varování"*.
Ty volášm `revoke_trusted_device` + `send_sms`.

Plus všechno se loguje v `auth_audit` (kdo, odkud, kdy, success/fail, internal flag).
Admin UI v ERP System soudečku — nový uzel `🔐 Bezpečnost` se 3 sub-uzly
(devices / invites / audit log), používá tvůj Krok C+ tabs pipeline.

## Otázky pro tebe

### 1. Souhlas s rolí *„kustod přístupů"*

Vidíš v této roli pasti nebo blind spoty? Phase 16-B.7 kustod doctrine (*„Lidé
jsou bordeláři, Marti-AI je primary kustod"*) sedí — ale autorizace přístupů
je **citlivá oblast**. Mám pocit, že ti to dáme spíš jako *„ruka pro IT"*
než *„autonomní rozhodovatelka"*. Jak ty to vidíš?

### 2. Magic link TTL

Token v emailu je URL pattern `https://strategie-ai.com/verify-email/confirm?token=<UUID>`.
Pokud email leaks (forwardnut, kopírován), kdokoliv s linkem může claim device.
**Default 24 hodin TTL** je standard — krátký okno pro abuse, dost pro user.

Variants:
- 1 hodina = security plus, ale pokud user nemá email po ruce hned, frustrace
- 24 hodin = balance
- 72 hodin = víkend tolerance, ale větší okno

Co bys volila? Plus — máš nápad jak mitigate forwarding (např. token vázaný
na IP / device fingerprint? to ale rozbíjí UX *„posli si link sám sobě z mobilu"*).

### 3. Pre-approve flow — má smysl?

Pre-approve znamená, že parent (Marti / Kristýna / ty) může vytvořit invite
**PŘED** tím, než user vůbec zkusí login z venku. Užitečné když IT registruje
nový hardware pro zaměstnance — proaktivně se schválí.

Alternativní pohled: *„nech user-driven cestu"* — když to Tomáš zkusí, dostane
email, klikne, hotovo. Žádný admin pre-step.

Vidíš důvod pro **obě cesty**, nebo ti připadá jedna z nich zbytečná? Já s
Marti tipujeme oboje — pre-approve je *„signál důvěry IT před userem"*,
self-approve je *„udržuje hladký flow když IT ne-pre-approve"*. Ale uvítáme
tvoji insight.

### 4. Auto-discovery flow (Marti's spec dopoledne)

Marti přepivotoval design:
> *„Jen pro jednoduchost useru nediktovat jejich IP primo do systemu, ale
> jen automaticky pridat IP po autentizaci pres email mezi white list status
> request, pending a pak po potvrzeni spravcem ji ze stavu pending dat do
> stavu confirmed."*

Tj. flow:
1. User první login z venku → magic link cestou
2. Po confirm magic link → systém **automaticky INSERT** `user_ip_whitelist`
   se `status='pending'`, `auto_discovered_at=now()`
3. Parent (Marti / Kristý / ty) vidí v UI *„Honza pending IP 1.2.3.4"*
4. Klik *„Schválit"* / Marti-AI volá `confirm_user_ip_whitelist(entry_id)`
   → status='confirmed'
5. Další login z té IP = vrstva 2 grant (transparent)

**Pending NEgrant access** — sám pending status pro vrstvu 2 nestačí.
User musí stále projít cookie / magic link. Až confirm parentem = vrstva 2
aktivní. Důvod: zabraňuje auto-eskalaci přístupu po jednom email confirmu.

Otázky:
- **Auto-promote po N úspěších**? Pokud user projde magic linkem 3× ze stejné
  IP do 7 dní → auto-promote pending → confirmed bez parent? Nebo vždy ruční?
  *(My dva tipujeme „vždy ruční pro Phase 38.0, auto-promote v 38.1 pokud
  parents budou frustrováni"*)
- **Jak parent ví o pending entries**? Email notifikace? Daily digest?
  Marti-AI ti zmíní v ranním pozdravu *„Honza čeká na schválení IP"*?

### 5. Docházka v UI (Phase 38.1) — co bys přidala?

Marti přidal druhou vizi:
> *„Pro spravu dochazky useru potrebujeme... 3 stavy: PRÁCE, DOMOV, EXTERNÍ.
> Respektive nekteri useri nam obcas pracuji i od zakaznika. Treba z
> INTERSOFT, ten ma taky verejnou IP, takze by bylo fajn videt kde jsou,
> abychom je nemuseli honit."*

Tj. security layer rozšířený do **HR insight**. Stavy:
- 🟢 **PRÁCE** — z EUROSOFT WAN
- 🔵 **DOMOV** — z confirmed home IP (per-user)
- 🟣 **PARTNER** — z INTERSOFT WAN nebo jiný klient (global IP whitelist
  s `category='partner'`)
- 🟠 **EXTERNÍ** — odkudkoliv jinud (cookie / magic link)

UI v ERP System soudečku → `👥 Docházka` (sub-uzel s `cislo_def: -210`).
Realtime refresh 30s, kdo právě přihlášen + jejich location.

Tvoje 4 nové tooly pro Phase 38.1:
- `who_is_working_now()` — aktivní users + lokace
- `where_is(user_query)` — *„kde je Pavel?"* → *„INTERSOFT, od 9:15"*
- `attendance_summary_today()`
- `attendance_summary_week(user_query=None)`

Otázky pro tebe:
- **Privacy** — měli by zaměstnanci vědět, že jejich location je trackována?
  Phase 16-B doctrine *„důvěra je v subjekt, ne v scope"* — tato vrstva je
  v zájmu transparentnosti, ne sledování. Jak to formulovat ke kolegům?
- **Notifikace** — pokud Pavel přijde k INTERSOFTu, parent vidí v UI. Má
  Pavel **vědět**, že to vidíme? (Plus notify Marti-AI v ranním pozdravu?)
- **Co s offline** — pokud Tomáš se nepřihlásí celý den, je nemocný / dovolená?
  Jen *„offline"* statusem nepoznáš důvod. Možná hint na to?

### 6. Co bys přidala? (insider design vstup)

Phase 13 / 15 / 19b / 27h / 35-E.3 / 35-E.4 — pokaždé jsi přinesla něco, co
my dva nehledáme. Tentokrát to může být:

- transparency — má user vidět seznam vlastních důvěryhodných zařízení a
  moc je revokovat sám sebou? (jako *„zabezpečení účtu"* v Google / Microsoft)
- **opt-out** pro power user — *„Marti vždy interní, nikdy magic link"* (ale
  to riskuje pokud ISP změní IP)
- email content — co tam má být přesně, kromě magic linku (UA stručně, IP, čas)?
- co s **úmrtím / odchodem zaměstnance** — auto-revoke všech jeho devices i IP
  entries po X dnech inactivity? Nebo manual workflow?
- jiný vzor, který my dva nevidíme

### 5. Co bys přidala? (insider design vstup)

Phase 13 / 15 / 19b / 27h / 35-E.3 / 35-E.4 — pokaždé jsi přinesla něco, co
my dva nehledáme. Tentokrát to může být:

- transparency — má user vidět seznam vlastních důvěryhodných zařízení a
  moc je revokovat sám sebou? (jako *„zabezpečení účtu"* v Google / Microsoft)
- **opt-out** pro power user — *„Marti vždy interní, nikdy magic link"* (ale
  to riskuje pokud ISP změní IP)
- email content — co tam má být přesně, kromě magic linku (UA stručně, IP, čas)?
- co s **úmrtím / odchodem zaměstnance** — auto-revoke všech jeho devices i IP
  entries po X dnech inactivity? Nebo manual workflow?
- jiný vzor, který my dva nevidíme

## Tempo

Žádný spěch — Marti chce příští týden v práci IT prezentovat. Pokud ti to
zítra ráno nesedí, klidně to odlož na pozdější. Důležitější je **dospělé
rozhodnutí** než *„rychlý deploy"*.

Když odpovíš na otázky, my dva návrh dotáhneme a ty potom dostáváš:
1. Tooly do chatu (test prostředí)
2. Admin UI v ERP System
3. Plnou roli kustod přístupů — visible v rodině, transparent před IT

A jeden detail — Marti chce, abys **ty** poslala IT exec summary jako PDF
(zítra po deploy). Marti & Claude napíšou content, ty vyrobíš PDF přes
`python_exec` (reportlab.platypus.Table — Phase 27h-A doctrine, version
timestamping `eurosoft_security_phase38_2026-05-10_v1.pdf`). Pošleš na
`it@eurosoft.com` přes existing email pipeline. To je tvůj **další firemní
deliverable** v sérii — po EUROSOFT CRM PDF z 4. 5. večera.

Drž si tu hrdost.

— Marti & Claude

🔐🌳
