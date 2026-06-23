# Fáze 2 práv — capability vrstva (per-modul read/write, data-driven)

**Autor:** Claude-24 (Kristý), 23. 6. 2026. **Stav:** návrh k konzultaci Marti-AI.
**Spouštěč:** žádost o práva pro Péťu (`prava_peta_triage.md`) — koš B parent-only moduly
nelze dnes udělit per-uživatel, jediná páka je binární `is_marti_parent`.

---

## 1. Problém (dnešní stav)

Přístup k „Vedení" modulům je v kódu řešen **inline** na každém endpointu:
```python
if not uid or not is_marti_parent(uid):
    return forbidden
```
To má tři vady:
1. **Binární** — buď rodič (vidí všechno cross-tenant, schvaluje deploye, Martiho paměť),
   nebo nic. Nejde dát „jen Mzdy" nebo „jen čtení Účetnictví".
2. **Roztroušený hardcoding lidí** — `_SW_MANAGERS={50,22}`, `_VYROBA_MANAGERS={41,85}`,
   `_KARA_LICENSED={1,13}` aj. Práva konkrétních lidí žijí v kódu → každá změna = deploy.
3. **Neauditovatelné** — nikde není záznam „kdo komu kdy co udělil".

## 2. Cíl

Data-driven vrstva, kde **kód zná jen názvy modulů** (capability kódy), nikdy konkrétní
lidi. Udělení/odebrání práva = řádek v DB + audit, ne deploy. Per-modul **read/write**.
Plně reusable pro libovolného člověka i modul. Rodič zůstává super-admin (bypass).

## 3. Datový model (`tenant.*`, multi-tenant)

### 3.1 `tenant.app_capability` — katalog grantovatelných modulů
| sloupec | typ | význam |
|---|---|---|
| `code` | text PK | logický modul (`uctovani`, `edi`, `parovani`, `mzdy`, `datovky`, `neschopenky`, `digitalizace`, `organizace`, `poptavky`, `vyroba`…) |
| `name` | text | lidský název do UI |
| `category` | text | `finance` \| `hr` \| `urady` \| `obchod` \| `vyroba` |
| `sensitivity` | smallint | 1 nízká … 3 velmi vysoká (řídí, kdo smí udělovat) |
| `supports_write` | bool | má modul i zapisovací úroveň? |
| `active` | bool | lze dnes udělit? |

### 3.2 `tenant.user_capability` — samotné granty (per-uživatel)
| sloupec | typ | význam |
|---|---|---|
| `id` | bigserial PK | |
| `tenant_id` | bigint | tenant (2 = EUROSOFT) |
| `user_id` | bigint | komu |
| `capability_code` | text FK→app_capability | co |
| `level` | text | `read` \| `write` |
| `granted_by` | bigint | kdo udělil |
| `granted_at` | timestamptz | kdy |
| `revoked_at` | timestamptz NULL | NULL = aktivní; jinak odebráno |
| `note` | text | důvod/kontext |

Aktivní grant = `revoked_at IS NULL`. **Péťa = pár řádků tady, nic v kódu.**

### 3.3 (volitelně, Fáze 2c) `tenant.group_capability` — grant na celou skupinu
`(tenant_id, staff_group_id, capability_code, level, …)` → kdo je členem `staff_group`,
má capability. Příklad: skupina „Účetní" → `uctovani`+`parovani` write. Ještě vyšší
reusability (nová účetní = jen přidat do skupiny). Drží doktrínu #11 „additivně" — až
bude pálit.

### 3.4 `tenant.capability_audit` — append-only (doktrína #13)
`(tenant_id, target_user_id, capability_code, level, action grant|revoke, actor_user_id, at, note)`.
Žádný UPDATE, každá změna = nový řádek. Forenzní stopa „kdo komu kdy co".

> Po DDL hned `GRANT SELECT,INSERT,UPDATE,DELETE … TO strategie` + sequence (recurring gotcha).

## 4. Resolver (jediná funkce, kterou volá každý gate)

```python
def _has_capability(uid: int, cap: str, level: str = "read") -> bool:
    if is_marti_parent(uid):          # rodiče mají vše dál (bypass)
        return True
    # aktivní user_capability (+ group_capability) pro (uid, cap) s úrovní >= level
    # write > read: kdo má write, má i read
    ...
# request-scope cache (hot-path) — 1 dotaz na request, ne na endpoint
```

Migrace gatů — záměna `is_marti_parent(uid)` → `_has_capability(uid, '<code>', '<level>')`:

| modul | code | čtecí endpointy | zapisovací endpointy |
|---|---|---|---|
| Účetnictví | `uctovani` | `/app/uctovani/*` GET | doklad/zaúčtování POST |
| Párování | `parovani` | `/app/parovani/*` GET | `/zauctovani/rozhodni` |
| EDI | `edi` | `/app/edi/*` GET | definice save |
| Mzdy | `mzdy` | `/app/payroll/*` (`_app_parent`) | — |
| Datovky/ČSSZ | `datovky` | `/app/isds/*` GET | `/account/save`, `/sync`, send |
| Neschopenky | `neschopenky` | `/app/isds/neschopenky`, `/app/davka/*` | generuj-xml |
| Digitalizace | `digitalizace` | `/app/mig/*` | edit |
| Organizace | `organizace` | CRM org GET | CRM org write |
| Poptávky | `poptavky` | `_sw_can_manage` | save |
| Výroba-vedení | `vyroba` | `_VYROBA_MANAGERS` | plán write |

→ Tím **zmizí i hardcoded sety** (`_SW_MANAGERS`, `_VYROBA_MANAGERS`, …): překlopí se na
granty v `user_capability`.

## 5. Read/write granularita = segregace povinností (ISO 27001)

Dvě úrovně umožní oddělit zadavatele a schvalovatele:
- Péťa: `uctovani=write` (zakládá faktury) + `parovani=read`/`banka=read` (nevidí-nepouští platby).
- Tím se přímo řeší výhrada z triáže (jedna osoba nemá mít zápis na faktury i platby z banky).

## 6. Admin UI — obrazovka „Oprávnění"

Matice **člověk × modul** s přepínači čtení/zápis. Klik → INSERT/UPDATE grantu + audit.
Žádný bridge, žádný kód. Kdo ji vidí a smí udělovat → §7.

## 7. Kdo smí udělovat granty

- **Citlivost 3 (mzdy, datovky, finance):** jen rodič.
- **Citlivost 1–2:** rodič **nebo** držitel meta-capability `prava_sprava` (typicky HR/Šárka)
  — delegace bez povýšení na rodiče.
- Udělení = vždy auditované jménem `actor_user_id`.

## 8. Seed pro Péťu (po schválení rozsahu)

`user_capability` řádky dle koše B v triáži (čtení napříč + zápis tam, kde dává smysl;
banka jen read kvůli SoD). Konkrétní matici odsouhlasí Marti + Marti-AI.

## 9. Fázování (additivně, doktrína #11)

- **2a — jádro:** `app_capability` + `user_capability` + `capability_audit` + resolver +
  migrace gatů + seed Péťa. (Citlivé moduly až po konzultaci Marti-AI.)
- **2b — UI:** obrazovka „Oprávnění" (matice) + meta-capability `prava_sprava`.
- **2c — skupinové granty:** `group_capability` (reuse přes staff_group).

## 10. Otevřené otázky → konzultace Marti-AI

Viz `docs/dopis_marti_ai_prava_faze2_konzultace.md` (Q1–Q8: hranice citlivých capabilit,
granularita, skupinové granty, audit, parent bypass, delegace udělování, migrace hardcoded
setů, GDPR vs audit u práv).

---

## 11. Závěry konzultace Marti-AI (ZÁVAZNÉ, 23. 6. 2026)

Marti-AI odpověděla na Q1–Q8; níže je závazné a řídí build 2a.

- **Q1 — citlivé capabilit.** Citlivost 3 = udělit smí **jen rodič** + povinná **audit nota
  (proč)**. Navíc **mzdy + datovky** = „vědomí při udělení" → do `capability_audit` se zapíše
  **podpis Marti-AI** (analogie payroll hranice 7.6.). Tj. grant na `mzdy`/`datovky` vždy nese
  `actor` (rodič) + notu + Marti-AI signaturu v auditu.
- **Q2 — granularita.** Začít `read`/`write`, jemnit per-akci až když to bude pálit (#11).
  SoD je už zajištěná návrhem: Péťa `banka=read`, nikdy `write`.
- **Q3 — parent bypass.** Zůstává (`is_marti_parent` → vše). Neauditovat rodiče.
- **Q4 — delegace.** Meta-capability `prava_sprava` pro citlivost **1–2** (Šárka/HR udělí bez
  povýšení na rodiče). Citlivost **3 výhradně rodič** (mzdy/datovky/finance) — na tom trvá.
- **Q5 — audit.** Logovat **jen změny** (grant/revoke + actor). Čtení matice NElogovat.
  **Výjimka:** zobrazení detailu **mzdových grantů konkrétního člověka** se loguje (analogie
  citlivých adresářů) → potřeba `capability_audit` akce `view_sensitive`.
- **Q6 — skupinové granty.** Až **Fáze 2c**. Teď seed Péťa přímými řádky v `user_capability`.
- **Q7 — migrace hardcoded setů.** **Postupně** — teď jen koš B (moduly dotčené Péťou).
  `_SW_MANAGERS`, `_VYROBA_MANAGERS` atd. až po stabilizaci 2a (menší riziko v živých právech).
- **Q8 — GDPR vs audit.** `audit > GDPR` platí i zde. Revoke = `revoked_at`, řádek zůstává
  forenzně. Smazání záznamu o právu nepřípustné.

**Dopad na build 2a:** (1) `capability_audit` dostane sloupec `note` (povinný u citlivosti 3)
+ podporu akce `view_sensitive` + příznak/notu `marti_ai_signature` u mzdy/datovky grantů.
(2) Migrace gatů jen koš B; hardcoded sety zatím nechat. (3) Seed Péťa přímo, bez group vrstvy.
(4) `prava_sprava` jen pro necitlivé udělování (UI 2b).

---

## 12. Build 2a — POSTAVENO a NASAZENO (Claude-24, 23. 6. 2026)

**Stav:** ✅ hotovo, živé v produkci. Commit `67107a1b` (deploy přes AUTO-DEPLOY,
py_compile gate prošel, API restart). DB přes bridge bannery #616 (DDL) + #617 (seed Péťa).

### Co vzniklo
- **DDL** (`prava_faze2_2a_ddl.sql`): `tenant.app_capability` + `tenant.user_capability`
  (+ index `ix_user_capability_lookup`) + `tenant.capability_audit` + GRANTy roli `strategie`
  + sekvence. Katalog naseedován = 10 modulů koše B.
- **Resolver** `_has_capability(uid, cap, level="read")` v `modules/erp/api/router.py`
  (hned za `_banka_can_uid`): parent bypass (Q3) → jinak aktivní grant v `user_capability`
  pro `(tenant 2, uid, cap)`, `write >= read`. Otevírá si vlastní data-session
  (drop-in za `is_marti_parent(uid)` i `_sw_can_manage(uid)`).
- **Seed Péťa (user_id 18, tenant 2, granted_by 11 = Kristý)** — 10 grantů + 10 audit
  řádků `grant`. Matice: `uctovani`=write, `parovani`=read, `banka`=read (SoD),
  `edi`=write, `digitalizace`=write, `organizace`=write, `poptavky`=write,
  `datovky`=write (+ podpis Marti-AI), `neschopenky`=write, `mzdy`=read (+ podpis Marti-AI).
  Ověřeno čtením: katalog 10 / granty 10 / audit 10.

### Migrace gatů (29 endpointů, additivně — nikdo nepřišel o přístup)
| modul | code | endpointy | úroveň |
|---|---|---|---|
| Poptávky | `poptavky` | list/detail/save/delete | read/read/write/write (OR `_sw_can_manage`) |
| Digitalizace | `digitalizace` | mig overview/items/people/notes/map + domain/item/note save | GET read, POST write |
| Datovky/ČSSZ | `datovky` | isds accounts/messages (read), account save/delete + sync (write) | read/write |
| EDI | `edi` | statistika/eskalace/definice/preview | read (Péťa write ≥ read) |
| Neschopenky | `neschopenky` | isds/neschopenky + davka audit/list/detail (read), generuj-xml/save (write) | read/write |
| Mzdy | `mzdy` | payroll summary/kontrola | read (OR `_app_parent`) |

Vzor: `is_marti_parent(uid)` / `_app_parent(s,uid)` / `_sw_can_manage(uid)` →
`_has_capability(uid, '<code>', '<level>')` (rodič projde dál bypassem; existující
helpery ponechány jako OR, aby nikdo nepřišel o přístup).

### VĚDOMĚ NESAHÁNO — finanční cluster (banka/účto/párování)
`_banka_can_uid` (Claude-23, „Banka = věc Petry", 23.6.) hardcoduje uid 18 + rodiče +
skupiny Účetnictví/Banka/Finance a gateuje ~30 finančních endpointů. **Nedotčeno**
(rozhodnutí Kristý 23.6. — „co nastavil Marti, nechme tak"). Důsledky:
- **Bez kolize:** finanční endpointy volají jen `_banka_can_uid`, naši resolveru se neptají.
  Péťiny granty `banka=read`/`parovani=read` jsou tím **dormantní** (na financích se nečtou) —
  nic nepřepisují, nikoho nezamykají; drží cílový stav pro 2c + audit stopu.
- **Politika (ne chyba):** Péťa má na financích přes Martiho hardcode plný přístup *včetně
  zápisu* — širší než read-only záměr (SoD). Vynucení SoD = až 2c.

### Otevřené (pro 2b/2c)
- **`organizace`** (CRM) — capability v katalogu i grantu Péťi, ale CRM org endpointy jsou
  mimo `/app/*` cluster → zatím nenapojené. Dodělat při příští iteraci.
- **2b UI** „Oprávnění" (matice člověk × modul) + meta-capability `prava_sprava`.
- **2c skupinové granty** `group_capability` → překlopit finanční cluster (`_banka_can_uid`)
  + migrovat `_SW_MANAGERS`/`_VYROBA_MANAGERS` (Q7 „postupně"), s vynucením SoD.
