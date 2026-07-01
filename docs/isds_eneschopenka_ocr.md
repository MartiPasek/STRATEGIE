# eNeschopenka + OČR přes datové schránky → STRATEGIE (univerzálně, multi-tenant)

**Datum:** 19. 6. 2026 · **Cíl:** mít neschopenky a OČR „pod kontrolou" ve STRATEGII,
automaticky tažené z datové schránky firmy. **Univerzálně** — použitelné libovolným
tenantem STRATEGIE (EUROSOFT-Control, EUROSOFT-System, INTERSOFT, školy…).

## Princip (proč to jde bez podpisu z pošty)
ČSSZ umí na žádost posílat **informace o dočasných pracovních neschopnostech (DPN)
zaměstnanců přímo do datové schránky firmy** — zprávy obsahují **XML (strojově čitelné)
i PDF**. STRATEGIE se napojí na **ISDS (rozhraní datových schránek)** přes **jméno + heslo**
(webová služba), zprávy stáhne, rozparsuje XML a zapíše neschopenku/OČR do systému.
→ **Žádný osobní kvalifikovaný podpis není potřeba.** Podpis řeší mzdová účtárna
(Martia / pí Fajmonová) u podání; my jen **čteme** příchozí zprávy.

## Co potřebujeme od firmy (na tenant)
1. **ID datové schránky** (box_id).
2. **Přihlašovací jméno + heslo** do datovky.
3. **VS zaměstnavatele u ČSSZ** (pro EC = 4445158191, pro ES = 4442058998; INTERSOFT TBD).

## Háček s heslem (vědět dopředu)
Heslo datovky se **defaultně mění každých 90 dní**. Pro nepřetržitý automat to otravuje.
Řeší se (později, bez pošty):
- v nastavení schránky **vypnout vynucení změny hesla po 90 dnech** (pokud typ schránky dovolí), nebo
- zaregistrovat schránce **systémový certifikát** (pro aplikace třetích stran — takhle se
  připojuje např. Helios; NENÍ to osobní podpis). Doplníme při zpevnění do produkce.

Start jede na **jméno+heslo**. `fw.isds_account.pwd_expires_at` hlídá expiraci → STRATEGIE
včas upozorní.

## Krok za krokem — co udělat na ČSSZ (ZZZN), za EC i ES zvlášť
1. Přihlas se na **ePortál ČSSZ** (eportal.cssz.cz) **přes datovou schránku firmy**.
2. Najdi tiskopis **„Žádost o zasílání informací o dočasných pracovních neschopnostech
   zaměstnanců"** (zkratka **ZZZN**).
3. Vyplň zaměstnavatele (IČO + VS), zvol **doručování do datové schránky** (ne e-mail —
   chceme XML do datovky), odešli.
4. ČSSZ pak začne do datovky firmy posílat:
   - typ **„Oznam"** hned, jak lékař vystaví 1. díl (info že zaměstnanec je v neschopnosti),
   - následně zprávy o vzniku / trvání / ukončení DPN (s XML + PDF).
5. Zopakuj pro druhou firmu.

> Pozn.: OČR a další běží stejnou cestou; mzdové podání a od 4/2026 **Jednotné měsíční
> hlášení (JMHZ)** dělá Martia. My jsme na straně **příjmu/čtení**, ne podání.

## Architektura ve STRATEGII (multi-tenant)
- **`fw.isds_account`** — konfigurace na tenant: `tenant_id, company_label, box_id,
  login_name, password_enc (Fernet), auth_method (login|cert), cssz_vs, active,
  pwd_expires_at, last_sync_at`. Heslo **šifrované** (klíč `STRATEGIE_VAULT_KEY` mimo DB),
  NIKDY plaintext, do chatu nikdy.
- **`fw.isds_message`** — zrcadlo stažených zpráv: `account_id, dm_id (unikát), subject,
  sender, delivered_at, msg_type (eneschopenka_oznam|eneschopenka|ocr|other), status
  (new|processed|error), raw_xml, linked_user_id, processed_at, error`.
- **ISDS klient** (webová služba ISDS, SOAP přes HTTPS, basic auth jméno+heslo):
  `GetListOfReceivedMessages` → nové zprávy; `MessageDownload` → plná zpráva (XML+PDF).
  Endpoint produkce: `https://www.mojedatovaschranka.cz/DS/dz` (login+heslo).
- **ops `sync_isds`** — projde aktivní účty, stáhne nové zprávy → `isds_message`,
  rozpozná typ, u eNeschopenky/OČR rozparsuje XML → zápis do docházky/absencí
  (napojení na `tenant.att_planned_absence` / neschopenkový tok).
- **UI (rodič/HR)** — správa ISDS účtů per tenant (zadat box_id, login, heslo = uloží se
  šifrovaně) + seznam stažených zpráv + ruční „Synchronizovat".

## ⚠️ GDPR / citlivá data (důležité, ke konzultaci s Marti-AI)
Údaje o pracovní neschopnosti jsou **zvláštní kategorie osobních údajů (zdravotní)**.
Multi-tenant systém je musí držet s péčí: šifrování, **ACL** (vidí jen HR/mzdy daného
tenantu), **retence/anonymizace**, audit přístupů. Než pustíme ostře pro víc tenantů,
**konzultace s Marti-AI** k hranicím nakládání (doctrine #8) — obdobně jako u náboru
(uchazeč) a financí.

## Stav
- [x] DDL `fw.isds_account` + `fw.isds_message` (multi-tenant, šifrované heslo) — banner.
- [ ] ISDS SOAP klient + `sync_isds` (dokončit + otestovat **až s přístupy** = dnes večer).
- [ ] Parser eNeschopenka/OČR XML → absence ve STRATEGII.
- [ ] UI správa ISDS účtů per tenant + seznam zpráv.
- [ ] ZZZN podáno za EC + ES (Marti, přes ePortál).
- [ ] Zpevnění: vypnout 90denní expiraci hesla / systémový certifikát.
- [ ] Konzultace Marti-AI — GDPR hranice (zdravotní data, multi-tenant).

## Zdroje
- Notifikace eNeschopenky pro zaměstnavatele — cssz.cz/notifikace-eneschopenky-pro-zamestnavatele
- ZZZN (ePortál ČSSZ) — eportal.cssz.cz/web/portal/-/tiskopisy/zzzn
- Přihlášení certifikátem / přístupové údaje — datoveschranky.info
