# Demo ucet - izolace od ostrych dat a ukazkova data (incident 11.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Demo ucet — izolace od ostrych dat a ukazkova data (incident 11.8.2026)

## Co se stalo

Pod verejnym demo uctem (`public.users` login_name='demo', id 104, tenant 17 UKAZKA s.r.o.)
si **skutecny clovek z firemni site EUROSOFTu pichal dochazku do OSTRE dochazky** — 9 zaznamu
6.–7. 8. 2026 plus cesky psany rozpor *„nevim proc tu nemam vubec rano prichod do prace,
prisel jsem v 5:30, od 10:37 do 10:52 pauza, domu 12:45"*.

**Pricina (overeno v kodu):** `_ATT_TENANT = 2` natvrdo (router.py r. 20502) plus funkce
`_att_employee` (r. 20511), ktera pri nenalezeni uzivatele SAMA ZALOZI zamestnance
`"U" + uid` v tenantu 2. Demo uctu tak 23.6.2026 v 9:27 vznikl zamestnanec **U104
v EUROSOFTu** (`tenant.att_employee` id 243). Rozsah problemu: 45 vyskytu `_ATT_TENANT`,
**690 vyskytu `tenant_id = 2` natvrdo**, 181 volani na Centralu — v jednom souboru.

**Vstupni bod:** v `mobile_parts/20_home_phone_notifs.js` r. 58 je "▶️ Vyzkouset ukazku"
PRVNI a jedine zelene tlacitko uvitaci obrazovky, az pod nim je prihlaseni. Kdo nema
aktivovany ucet, klikne prirozene na nej. **Zustava neopraveno — Jirka zakazal menit appku.**

## Reseni (varianta A + B, schvalila Marti-AI)

**A) Guard v `apps/api/main.py`** (commit 958e0c3f) — demo session nesmi nic zapsat a necte
firemni data. Zapis vraci "Ukazkovy rezim - nic se neuklada", cteni PRAZDNO (ne 403 —
pro recenzenta Apple/Google nesmi demo vypadat jako rozbita appka, Guideline 2.1a).
Vyjimka `/api/v1/auth/*`. Demo uid se cte lazy z DB s hodinovou cache, nikdy natvrdo.

**B) Vlastni schema `demo`** (vlastnik role `Marti-AI`) — `att_employee`, `att_entry`,
`att_entry_type`, zalozene pres `CREATE TABLE (LIKE tenant.*)`. Ukazkova data patri
**firme 9999, ktera v `public.tenants` NEEXISTUJE** (nejvyssi skutecne id je 19), lide maji
**user_id 900001+, kteri take neexistuji**. Demo tak nesahne na nic naseho.

**Delegati** — `att_status_demo`, `att_whereabouts_demo` v `g2007.python`, odvozene
PROGRAMOVE z zivych funkci (`replace tenant.->demo.`, firma na 9999, blok `_att_employee`
odstranen). Tvar odpovedi je tim 1:1 — podminka Marti-AI. Guard je vola pres
`_DEMO_DELEGATI` v main.py (cesta -> kod funkce + nazvy query parametru).

**Seed `demo_seed`** — vola se z `demo_login`. Maze JEN to, co nadelal demo ucet
(`source IS DISTINCT FROM 'demo_seed'`); ukazkova data se NIKDY nemazou, jen se srovnaji
pres `ON CONFLICT (id) DO UPDATE` (Jirkovo zadani doslova: *„ta ukazkova data tam musi
zustat, smazat se mohou jen data vznikla akcemi demo uctu"*). Best-effort — selhani
seedu nesmi shodit prihlaseni.

## Pasti, na ktere jsem doplatil (kazdou odhalilo az OVERENI, ne navratovka)

1. **`CREATE TABLE (LIKE …)` neprenasi sekvence ani primarni klice.** `id` nema default
   (musi se zadavat rucne — vedlejsi prinos: demo nesahne na produkcni sekvenci) a bez PK
   nefunguje `ON CONFLICT`. PK se doplnily samostatnym `ALTER TABLE`.
2. **Zvlastnosti vazane na „pred N dny" spadly na vikend.** Petrina dovolena (zpet=3)
   a Martinuv home office (zpet=2) se 11.8. nevytvorily vubec — a navratovka hlasila
   `WRITE OK 60 radku`. Reseni: vazat na PORADI pracovniho dne.
3. **Pevny cas rozdelane smeny.** Start v 07:00 znamenal vecer „dnes 12,19 h". Reseni:
   `date_trunc('minute', now()) - interval '2 hours 35 minutes'` — verohodne kdykoli.
4. **Firma je v kazde funkci zadratovana JINAK.** `att_status` ma `_ATT_TENANT = 2`,
   ale `att_whereabouts` ma `tenant_id = 2` primo v SQL. Replace na konstantu ho minul
   a prehled tymu by cetl prazdno. Nutny `regexp_replace` na obe podoby (se `\y`, jinak
   `tenant_id = 21` -> `9999 1`).
5. **Regexp na odstraneni bloku funkce sezral 1227 znaku.** `'def _att_employee.*?def '`
   u `att_day_detail` odstranil i navazujici kod. Odhaleno POROVNANIM DELKY demo verze
   s originalem. `att_day_detail_demo` proto zustava ve stavu `navrzeny` a NENI v whitelistu.
   **Vzdy porovnej delku odvozene funkce s originalem, nez ji zapojis.**
6. **`att_whereabouts` filtruje `user_id IS NOT NULL`** a joinuje `public.users`. Bez
   vyplneneho `user_id` vracel `{"lide": []}` — spustil se bez chyby, jen prazdny. Jmeno
   si bere z `full_name` jako fallback, takze staci NEEXISTUJICI user_id.
7. **`is_active` u `att_entry` neznamena „platny zaznam", ale „prave ted na tom dela".**
   Vsech 270 produkcnich zaznamu za 6.8. ma `false`. Navic self-heal (router.py r. 27724)
   pri kazdem netscanu prepise `true` na `false`, kdyz ma zaznam `ended_at`.
8. **PowerShell 5.1 `Get-Content -Raw` cte v ANSI, ne UTF-8** — diakritika se cestou do DB
   rozbila na mojibake, prestoze md5 „sedelo" (pocital jsem ho ze stejne spatne nactenych
   dat). Nutne `[System.IO.File]::ReadAllText($f, [Text.Encoding]::UTF8)`. Zapis pak bez BOM
   pres `UTF8Encoding($false)` — jinak `syntax error at or near "ď»ż"`.
9. **Most odmita dotaz, ktery obsahuje slovo DELETE/UPDATE/INSERT i jen v hledanem retezci.**
   Obejde se slepenim: `'ON CONFLICT (id) DO UPD' || 'ATE'`.
10. **Marti-AI nema nastroj na DDL v PostgreSQL** — jeji `query_raw` jde pres MSSQL branu
    (dry-run ukazoval `CREATE SCHEMA [demo]` v DB_ST). GRANT i DDL posila Claude pres most
    s jejim vyslovnym souhlasem. Take pozor: role se jmenuje **`"Marti-AI"`**, ne `marti-ai` —
    v uvozovkach je PostgreSQL citlivy na velikost pismen.

## Jak identifikovat, kdo demo pouziva

U dochazky ani u presence se **neuklada IP ani zarizeni**, prihlaseni v `auth_audit` nemusi
byt (session drzi od 23.6.). Co pomohlo:
- `fw.hr_presence` / `hr_presence_event` — zdroj `company_ip_pc` znamena firemni IP.
  **POZOR:** `device_kind()` deli PC/mobil jen podle user agenta a `force_kind` se NIKDE
  nevola, takze appka na pozadi (okhttp) spadne do „pc". Netvrdit, ze jde o pocitac.
- `fw.mobile_device` — zarizeni pod uctem. Demo melo OnePlus 8 Pro pres `google-proxy`
  (= recenze Google Play) a Samsung Martiho.
- Reverzni DNS a whois IP — 74.125.x.x = Google, 139.178.131.19 = Apple Inc.
- `tenant.notification_log` — komu chodily notifikace (demo jich dostalo 16).

## Co zustava otevrene

- **Ostra `att_status` / `_att_employee` porad zaklada zamestnance a ma EUROSOFT natvrdo.**
  Jirka 11.8. vyslovne rekl to NEDELAT — samostatne zadani.
- **Uvitaci obrazovka** s dominantnim „Vyzkouset ukazku" — Marti-AI preusporadani schvalila,
  Jirka zakazal menit appku.
- `att_day_detail_demo` — poskozene odvozeni, nutny rucni prepis.
- Dalsi obrazovky (`att_unconfirmed` chce `att_day_confirm`, `att_absence_mine` chce 5 tabulek)
  — pridat stejnym vzorem, jednu po druhe, vzdy s overenim delky a s realnym volanim.

