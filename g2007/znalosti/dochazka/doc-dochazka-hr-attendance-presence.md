# HR modul — Docházka & Presence (návrh, 5. 6. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# HR modul — Docházka & Presence (návrh, 5. 6. 2026)

Autoři vize: Marti + Claude (id=23). Stav: **odsouhlaseno k MVP na příští týden.**
Před ostrým provozem: konzultace DPO (Miša Hladíková, vazba na Phase 41).

## 1. Princip

Presence se odvozuje z **připojení k síti, ne z GPS.** Privacy-by-design.
Cíl: u každého člověka stav **V budově / Mimo budovu (pracuje) / Mimo pracovní
dobu / Neznámý** — podklad dostupnosti i docházky. Stav = síťový signál +
pracovní doba + docházka (clock in/out).

EUROSOFT: velká budova, lidé pracují z budovy / od zákazníka / home office.
Každý má mobil (Apple/Android, někdo naši app), většina má počítač. Máme
firemní veřejnou IP, firemní WiFi (známé SSID), PWA a možnost instalovat
vlastní služby (NSSM) na počítače. Každé zařízení má název → vazba na člověka.

## 2. Tři vrstvy signálu

**1) Firemní veřejná IP — funguje pro VŠECHNY napříč OS.**
Na firemní WiFi je egress IP = naše firemní veřejná IP. Jakýkoli request na
backend (PWA / app heartbeat / agent) z té IP = **v budově**. Reuse `IP
whitelist` z Phase 38 (`fw.global_ip_whitelist`) — firemní IP označit jako
„budova". Nulové nové oprávnění, hned funguje pro každého, kdo cokoli otevře.

**2) Pasivní agent (kde máme náš SW):**
- **Počítač = NSSM agent** (náš tool): hostname, přihlášený user, aktivní/idle,
  source IP, last seen — pingá i v klidu. Nejsilnější „presence u stolu".
  Z firemní IP → v budově; odjinud → home office / zákazník.
- **Android = naše app:** heartbeat už běží — přidat **SSID firemní WiFi +
  source IP**. (SSID na Androidu = location oprávnění, opt-in.)

**3) Pasivní síťová detekce (device-agnostic, i Apple bez app) — FÁZE 2:**
Mikrotik / WiFi controller → DHCP lease / MAC → registrované MAC → člověk →
„v budově" bez naší app. Nejsilnější pokrytí, **GDPR-nejcitlivější**, vyžaduje
DPO + integraci. Odložit za MVP.

## 3. Evidence zařízení ↔ člověk

Rozšířit `fw.mobile_device` (nebo nový `fw.hr_device`) na obecný registr:
- typ (`pc` / `android` / `ios`), název / hostname, MAC (nullable, pro fázi 2),
  owner_user_id, **is_company** (firemní vs soukromé), **presence_opt_in**
  (bool), last_signal_at, last_source, last_state.
- Každé zařízení nese svůj název → identifikace člověka.

## 4. Stavový model

`fw.hr_presence` (aktuální stav per user): user_id, state
(`in_building` / `remote` / `off` / `unknown`), in_building bool, source
(`company_ip` / `wifi_ssid` / `agent` / `network`), last_seen_at.
`fw.hr_presence_event` (append-only log): user_id, device_id, source, state,
detected_at — krátká retence, agregace.

Odvození stavu:
- recent signál z firemní IP/SSID/agenta → `in_building`.
- clocked in + signál odjinud → `remote` (home office / zákazník).
- mimo pracovní dobu nebo žádný signál + není clocked in → `off` / `unknown`.

## 5. GDPR rámec

- **Docházka (clock in/out + evidence pracovní doby)** = **zákonná povinnost**
  (§96 ZP) → solidní právní základ.
- **„V budově / mimo"** jde nad rámec → **oprávněný zájem + transparentnost +
  minimalizace**: ukládat jen **stav**, **ne GPS**, **ne mimo pracovní dobu**.
  §316 ZP: monitoring jen s vážným důvodem + **lidé musí být informováni** o
  rozsahu a způsobu.
- **Firemní počítače** = agent OK (firemní vybavení).
- **Soukromé telefony (Marti 5.6.):**
  - sledování **JEN v pracovní době**,
  - uživatel si může logování **sám vypnout v appce** (toggle „Sledovat moji
    přítomnost"),
  - **vypnutí se zapíše do DB** — `fw.hr_presence_optout` (user_id, device_id,
    enabled bool, changed_at, changed_by). Transparentní audit (HR vidí, že si
    někdo vypnul logování; vysvětluje mezery; není to trest).
  - žádné GPS, žádný background mimo pracovní dobu.
- **Krátká retence** presence logů + agregace; surová docházka dle zákona.
- **DPO konzultace** před ostrým provozem.

## 6. MVP (příští týden)

1. **Registr zařízení** (rozšíření `fw.mobile_device`) + mapování na usery.
2. **Detekce „v budově" přes firemní IP** — reuse IP whitelist; backend značí
   presence při každém requestu z firemní IP.
3. **NSSM agent v0** pro počítače — hostname + user + last seen + firemní IP
   (heartbeat jako u mobilní app).
4. **Android app:** do heartbeatu přidat SSID + source IP + toggle opt-in.
5. **Presence board** — kdo je v budově / mimo / off (vzor: presence board
   Claude instancí `fw.claude_instance`).
6. **Pracovní doba** `fw.hr_work_schedule` (user_id, den, start, end) — gate
   sledování soukromých telefonů na pracovní dobu.

## 7. Fáze 2 (po DPO)

- Mikrotik / WiFi controller MAC detekce (Apple bez app).
- Plná docházka (HR mzdové podklady — vazba na Phase 39).
- Manager hierarchie + zakázka attribution (Phase 40).

## 8. Reuse ze STRATEGIE (proč je to rychlé)

- IP whitelist (Phase 38) → detekce firemní IP.
- `fw.mobile_device` → registr zařízení.
- NSSM (používáme všude) → počítačový agent.
- Heartbeat pattern (mobil app + `fw.claude_instance`) → agent heartbeat.
- Presence board pattern → presence board lidí.


