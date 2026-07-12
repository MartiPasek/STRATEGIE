# Plán obnovy a kontinuity (DR/BCP) — RTO/RPO + restore drill

> oblast: `iso27001` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Plán obnovy a kontinuity (DR/BCP) — RTO/RPO + restore drill

> **Verze:** 1.0 (návrh) · **Datum:** 21. 6. 2026 · **Entita:** STRATEGIE – System s.r.o.
> **Vede:** Michal (restore drill + kontinuita) · podklad k DOC-11 · ISMS dohled: Mísa · technika: Marti + Claude · **Klasifikace:** Interní
> **Pokrývá:** A.5.29 (bezpečnost při výpadku), A.5.30 (připravenost ICT na kontinuitu),
> A.8.13 (zálohování), A.8.14 (redundance).

---

## 1. Cíl a rozsah

Definovat **cíle obnovy** (RTO/RPO) pro klíčové služby a data STRATEGIE, popsat **existující
mechanismy obnovy** (blue-green HA + zálohy) a stanovit **opakovatelný scénář ověření obnovy**
(restore drill) se záznamem. Auditor u A.5.30 chce vidět nejen plán, ale **doložený test**.

---

## 2. Definice

- **RTO** (Recovery Time Objective) = maximální přijatelná doba výpadku, než je služba obnovena.
- **RPO** (Recovery Point Objective) = maximální přijatelná ztráta dat (stáří poslední použitelné zálohy).

---

## 3. RTO/RPO per služba a datový sklad

| Aktivum | Scénář výpadku | Mechanismus obnovy | RTO (cíl) | RPO (cíl) |
|---|---|---|---|---|
| **API (aplikace)** | Vadný deploy / pád procesu | **Blue-green**: Caddy přeroutuje na API-B (frozen-good) + pin/unpin | **< 5 min** | 0 (kód v gitu) |
| **API (oba uzly)** | Pád hostitele cloud APP | Restart služeb / obnova VM u ČMIS | < 4 h | 0 (kód v gitu) |
| **PostgreSQL `data_db`** | Poškození/ztráta DB | Obnova z denní zálohy (ČMIS) | < 4 h | **< 24 h** (denní záloha 03:00) |
| **MSSQL DB_EC/DB_IS** | Výpadek EC-SERVER2 (on-prem) | EUROSOFT obnova (mimo náš kód); STRATEGIE běží degradovaně bez zrcadla | < 8 h | dle EUROSOFT |
| **Trezor tajemství** | Ztráta klíče `STRATEGIE_VAULT_KEY` | Klíč zálohovaný mimo DB (offline); bez klíče data nečitelná | < 2 h | 0 (záloha klíče) |
| **Konfigurace / kód** | Lidská chyba, regrese | git revert + blue-green fallback | < 15 min | 0 |

> Hodnoty jsou **cíle k odsouhlasení vedením** (management review). Skutečné hodnoty doložíme
> z restore drillu (§6) a z reálného failover testu (§5).

---

## 4. Zálohovací schéma (A.8.13)

| Co | Kam | Frekvence | Retence | Šifrování |
|---|---|---|---|---|
| PostgreSQL `data_db` | DC ČMIS (Praha) | Denně 03:00 | [DOPLNIT — doporučeno ≥ 30 dní] | [v zavádění — at-rest] |
| Kód / konfigurace | Git (origin) + blue-green prev | Při každém deploy | Plná historie | TLS přenos |
| Klíč trezoru | Offline úložiště mimo DB | Při změně | — | Chráněný přístup |

**Akce (T2/T4):** potvrdit retenci záloh (≥ 30 dní), zapnout šifrování záloh at-rest, doložit
offsite kopii (jiná lokace než produkční DB).

---

## 5. Redundance a failover (A.8.14, A.5.29) — STAV: OTESTOVÁNO

**Blue-green architektura:**
- **API-A** (port 8002, `C:\Projekty\STRATEGIE`) = primár (aktuální verze).
- **API-B** (port 8003, `C:\Projekty\STRATEGIE-prev`) = záloha (ověřená stabilní verze).
- **Caddy** `lb_policy first` → při výpadku A automaticky servíruje B.
- **User-controlled fallback** — pin/unpin v patičce (cookie routing), `unpin-now` pro zaseknutý prohlížeč.
- **Povýšení do zálohy** na tlačítko („Zkopírovat aktuální verzi do zálohy") + self-heal štítku verze
  (`fw.api_version` se srovnává na reálnou verzi B).

**Důkaz funkčnosti:** failover na B byl reálně proveden a ověřen (přepnutí na B funkční, 20.6.2026).
→ záznam viz §6 šablona (vyplnit datum/čas/výsledek do auditní stopy).

---

## 6. Scénář restore drillu (A.5.30) — K PROVEDENÍ (T2)

Cíl: prokázat, že zálohu `data_db` lze obnovit a změřit reálné RTO.

**Příprava:**
1. Vybrat poslední denní zálohu `data_db` z ČMIS.
2. Připravit izolovanou **test DB** (oddělená instance / jméno, NE produkce).

**Provedení (krok za krokem):**
3. Zaznamenat čas startu (T0).
4. Obnovit zálohu do test DB (`pg_restore` / nástroj ČMIS).
5. Ověřit integritu: počet řádků klíčových tabulek (`public.users`, `tenant.att_entry`,
   `tenant.ucetni_denik`, `fw.diag_log`), poslední `created_at`, namátkový SELECT.
6. Zaznamenat čas dokončení (T1) → **RTO = T1 − T0**; **RPO = stáří zálohy**.
7. Test DB po ověření zlikvidovat (smazat).

**Šablona záznamu (do auditní stopy / DOC-11):**

| Datum | Provedl | Záloha (datum/čas) | T0 | T1 | RTO | RPO | Integrita OK? | Poznámka |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

**Cadence:** minimálně **1× za čtvrtletí** + po významné změně schématu.

---

## 7. Postup při incidentu (rychlý odkaz)

| Situace | První krok | Eskalace |
|---|---|---|
| Vadný deploy | Pin na API-B (patička) / `unpin-now` | git revert + redeploy |
| Pád API procesu | RESTART-WATCHER marker / ops „Restartovat API" | Restart hostitele |
| Poškození `data_db` | Restore z poslední zálohy (§6) | ČMIS podpora |
| Podezření na únik / bezp. incident | Postup DOC-10 (řízení incidentů) | Rodičovská rada + ÚOOÚ dle závažnosti |

---

## 8. Otevřené body (akce)

1. **Provést restore drill** a vyplnit záznam (§6) — T2. *(největší mezera pro A.5.30)*
2. Potvrdit **retenci záloh** (≥ 30 dní) a **šifrování at-rest** — T2/T4.
3. Doložit **offsite** kopii (jiná lokace) — T2.
4. Odsouhlasit **RTO/RPO cíle** na management review (§3) — T6.
5. Zaznamenat provedený **failover test** na B do auditní stopy — T2.

---

*Návrh — promítne se do DOC-11 (Zálohování a kontinuita). Navazuje na `iso27001_dorazeni_2026.md`
(§5 B10/B11) a SoA A.5.29/5.30/8.13/8.14.*


