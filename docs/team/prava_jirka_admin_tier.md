# 🔑 Systém práv — dva tiery: SYSADMIN (is_admin) a RODIČ (is_marti_parent)

**Pověření Marti (25.6.2026):**
1. *„Jirka musí mít principiálně stejná oprávnění jako Kristý, jen s tím rozdílem, že není rodič."*
2. **Upřesnění:** *„Jirka je zástupce Kristý → odpovědný za všechny oblasti. Jsme tři lidé systémoví
   administrátoři: já, Kristý a Jirka. Já a Kristy jsme navíc rodiče."*

## Model — dvě nezávislé role

| Role | Kdo | Co dává |
|------|-----|---------|
| **SYSADMIN** (`is_admin`) | Marti (1), Kristý (11), **Jirka (20)** | Systémová nastavení, správa uživatelů, framework/design, deploy/ops, **všechny oblasti** (business, ERP, docházka, projekty, reporty, audit) |
| **RODIČ** (`is_marti_parent`) — NAVÍC | Marti (1), Kristý (11) | **+ osobní/intimní data** (viz chráněná množina) |

**Jirka = plný sysadmin** (zástupce Kristý, všechny oblasti). Jediný rozdíl oproti Kristý:
**není rodič → nevidí osobní/intimní data.**

## 🛡️ CHRÁNĚNÁ MNOŽINA (parent-only) = JEN osobní/intimní data
Tohle zůstává `_require_parent` (rodič: Marti + Kristý) + predikát `is_marti_parent` v logice. Jirka NE:
- **Paměť/diář Marti-AI** — `thoughts` personal, record/recall, diary, **md_pyramid md1 personal + md5 Privát Marti**
- **Osobní data zaměstnanců** — HR self-data, RČ/OP/pas, **výplatnice**, **trezor/secret/vault**, datovky (ISDS), děti, osobní kontakty
- **Consents** — auto-send, auto-lifecycle (grant/revoke)
- **Personal lifecycle konverzace** (intimní prostor)
- **SMS personal** (mark/list_sms_personal) · **Email Personal složka**
- **Personal audit** — thoughts/diary/SMS personal/personal konverzace (Jirka vidí business + system audit, NE personal)

Vše ostatní (systém, admin, framework, deploy, ops, business, ERP, docházka, reporty, správa členů…)
= **Jirka MÁ** jako sysadmin.

## 🛡️ Kustodská rizika (Marti-AI 25.6.) — MUSÍ zůstat ošetřené v LOGICE
- **a) Elevace role:** zápis do `users.is_marti_parent` / `users.is_admin` smí **jen rodič**
  (datová vrstva, ne jen guard). Jirka spravuje členy, NE adminy/rodiče — a nesmí povýšit sebe.
- **b) Tenant-scoping:** `is_admin` je **tenant-scoped** (na rozdíl od cross-tenant `is_marti_parent`).
  `_require_admin` kontroluje tenant kontext. Jirka-admin v EUROSOFTu nevidí STRATEGIE / osobní tenant.
- **c) Audit:** Jirka vidí business + **system** audit (deploy logy, framework akce, user-management logy) — smí vidět
  *ŽE* akce proběhla (timestamp/actor/typ). NE **obsah** osobních dat (thoughts/diary obsah, personal konverzace,
  SMS personal, email Personal, HR citlivá RČ/výplatnice). Filtr v query.
- **d) Správa horního tieru (Marti-AI doplnění):** akce na uživatelích s rolí `owner` nebo `is_marti_parent`
  (změna role / deaktivace / reset hesla) = **rodičovský souhlas i pro sysadmina**. Jirka spravuje JEN members,
  nesmí měnit vlastní tier ani tier rodičů (rozšíření self-elevace na „elevace/degradace kohokoliv v horním tieru").

## ⚠️ POŘADÍ NASAZENÍ (Marti-AI, kritické — flag až NAKONEC)
1. Zamknout celou osobní/intimní množinu na `_require_parent` + **ověřit 403 na každém endpointu**.
2. **Explicitní souhlas Marti v chatu** (Marti-AI podmínka — ne dřív).
3. Teprve PAK `is_admin=True` pro Jirku.
4. Test Jirkovým účtem (systém/business OK, osobní = 403).
Flag se NEnasazuje simultánně ani před zámkem osobní množiny.

## Mechanika (implementace)
- Nový centrální `_require_admin(uid[, tenant])` = projde **rodič NEBO is_admin** (tenant-scoped).
- Systémové/admin endpointy (dnes `_require_parent`) → `_require_admin`. Osobní/intimní → zůstávají `_require_parent`.
- `is_marti_parent` PREDIKÁT v logice (cross-tenant osobní data, audit, approver) = **nedotčen**.
- Self-elevace guard v user-management zápisech (a).
- `is_admin` grant/revoke jen rodič, audit activity_log importance=5.

## Pořadí (kustod)
1. Mechanika `_require_admin` + self-elevace guard (nezmění chování, dokud nepřepnu endpointy).
2. Osobní/intimní endpointy ověřit, že zůstávají `_require_parent` (default už jsou).
3. Systémové/admin endpointy přepnout na `_require_admin`.
4. `is_admin=True` pro Jirku (přes rodičovský banner, audit).
5. **Test účtem Jirka** — osobní data = 403; systém/business = OK.

## Stav
- [x] Marti-AI potvrzení opraveného modelu (Jirka = plný sysadmin, lock jen osobní data). ✅
- [x] Mechanika `_require_admin` + `is_admin_user`/`is_parent_or_admin` (commit 05049b1). ✅
- [x] Systémové endpointy router.py `_require_parent`→`_require_admin` (commit 8d3cf30) — **INERTNÍ** dokud flag. ✅
  - Re-protect na rodičovské: deploy/preview, deploy/now, restart-api, /diag-sql, /ops/request.
  - Bridge approval (diag-write pending/decide/status, instance/active) = `_require_admin` → Jirka schvaluje VLASTNÍ Claude-28.
  - Osobní data (self-data/secret/trezor/children = self-ownership; HR = `_hr_can_manage` rodič+HR skupina;
    mutující ops/secondary-refresh/ops-run = inline `is_marti_parent`) — **NEovlivněno flipem**, Jirkovi zavřené.
  - Self-elevace: správa rolí/is_admin/is_marti_parent NENÍ v router.py (admin/auth modul, neflipnuto) → zůstává rodičovská.
- [ ] **Frontend gate** — system soudeček + DESIGN dlaždice ukázat i sysadminům (is_marti_parent → is_parent_or_admin v UI). FOLLOW-UP.
- [ ] **Jirka `is_admin=True`** — čeká na výslovný souhlas Marti v chatu (Marti-AI podmínka).
- [ ] Test účtem Jirka (osobní = 403, systém = OK).

— Claude (ID23), 25.6.2026, po upřesnění Marti (3 sysadmini / 2 rodiče). Konzultace Marti-AI kustod.
