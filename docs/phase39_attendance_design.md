# Phase 39 — Univerzální docházkový modul (PostgreSQL, prodejný)

**Stav:** návrh k diskuzi (Marti + Marti-AI), 6. 6. 2026.
**Cíl:** Čistý, univerzální, multi-tenant docházkový modul v PostgreSQL `data_db`,
nezávislý na EUROSOFTu, prodejný třetím stranám. Migrace z Centrály 1
(`DB_EC.EC_Dochazka`) — pro start poslední ~2 měsíce na odzkoušení.

Tento dokument NEZAKLÁDÁ tabulky. Je to podklad pro konzultaci a rozhodnutí.

---

## 1. Co model musí umět (z Martiho zadání 6.6.)

Kromě odpracované doby i **nepřítomnosti v různých stavech**:
- návštěva lékaře (krátká, část dne),
- pracovní neschopnost (PN / „marod" — i víc dní, + kontrola),
- OČR (ošetřování člena rodiny),
- sickday,
- nahlášená dovolená,
- (rozšiřitelně) neplacené volno, paragraf, náhradní volno…

…a to **v různých stupních schválení**:
- **self-audit** zaměstnance (denně/týdně/měsíčně si zkontroluje a odešle/„schválí"),
- **vyšší kontrola** nadřízeného,
- **konečná kontrola** mzdové účetní.

Plus **dvě verze docházky**:
- **reálná** (skutečně odpracováno),
- **oficiální pro úřady** (např. zastropované přesčasy dle zákoníku práce).

---

## 2. Tři návrhové pilíře

### Pilíř A — Typovaný záznam přes číselník s kategorií (uniformita)

Místo zvlášť „práce" a zvlášť „nepřítomnost" → **jeden záznam** s typem, který
nese **kategorii**. Přidání nového typu (sickday, OČR, paragraf) = jen nový
řádek číselníku, **žádná změna schématu**. (Marti-AI doktrína „uniformita vítězí",
„co existuje, musí mít jméno".)

`attendance_entry_type` (číselník):
- `id`, `tenant_id`, `code`, `name`
- `category` ENUM: `work` | `overhead` (režie) | `vacation` | `sick` (PN) |
  `medical` (lékař) | `family_care` (OČR) | `sickday` | `unpaid` | `comp_off` …
- `counts_as_worked` bool — započítává se do odpracované doby?
- `is_paid` bool — placené?
- `requires_approval` bool
- `affects_balance` bool — hýbe kontem hodin / dovolené?
- `active` bool

`attendance_entry` (jádro — jeden úsek/událost):
- `id` bigserial, `tenant_id`
- `employee_ref` (odkaz na zaměstnance/usera — generický int + snapshot jména)
- `entry_type_id` → `attendance_entry_type`
- `work_date` date (den případu); pro vícedenní nepřítomnost `date_from`/`date_to`
- `started_at` / `ended_at` timestamptz (u timed záznamů), `break_minutes`
- `hours` numeric (vypočtené nebo zadané — u celodenní nepřítomnosti fond)
- `project_ref` varchar (zakázka, volitelné — jen u práce)
- `source` ENUM: `mobile_app` | `tablet` | `web` | `manual` | `import`
- `note` text
- `status` (workflow — viz Pilíř B)
- `is_active` bool (probíhající „píchnutí")
- audit: `created_by/at`, `updated_by/at`
- migrace: `source_system` ('centrala1'), `source_id` bigint, **UNIQUE
  (tenant_id, source_system, source_id)** → idempotentní import.

Výhoda: dotaz „co dělal zaměstnanec X dne Y" = jeden SELECT (práce i absence
pohromadě). Mzdy/finance se počítají z `category` + flagů, nejsou v jádře.

### Pilíř B — Vícestupňové schvalování (stav + auditní log)

Stav záznamu jako jasný workflow (ENUM `status`):

```
draft → submitted (zaměstnanec odeslal/„self-approved")
      → supervisor_approved (nadřízený)
      → payroll_approved (mzdová účetní)
      → locked (uzamčeno, jde do mezd)
      (kdykoli) → rejected (s důvodem → zpět na draft)
```

Plus **auditní log** `attendance_approval_event`:
- `id`, `entry_id` (nebo dávkový rozsah), `stage` (employee/supervisor/payroll),
  `action` (approve/reject), `actor_user_id`, `at`, `note`.

Tím máme „bezpečnost přes probuzení, ne přes ticho" (Marti-AI 9.5.) — kdo, kdy,
co schválil/zamítl, dohledatelné. Pro prodejnost: počet stupňů konfigurovatelný
per tenant (některé firmy nemají mzdovou účetní v procesu) — v1 napevno 3 stupně,
příprava na konfiguraci.

Hromadné schválení (Marti's „denně/týdně/měsíčně") = akce nad výběrem řádků →
zapíše stav + N událostí do logu (Mód 1 per-row, jako u nás v ERP).

### Pilíř C — Reálná vs oficiální verze (dual-ledger jako odvozené)

Reálná data = `attendance_entry` (zdroj pravdy). **Oficiální verze pro úřady se
NEduplikuje**, ale **počítá** pravidlovým enginem:
- denní/týdenní strop hodin, zastropování přesčasů, přesun přebytku do konta /
  náhradního volna, zaokrouhlení…
- volitelně `attendance_adjustment` (ruční legální korekce s důvodem a autorem —
  auditní stopa), aby šlo oficiální verzi ručně doladit, aniž se přepíše realita.

Výsledek: dvě sestavy ze stejných dat — **reálná** (co se stalo) a **oficiální**
(co se vykáže), rozdíl je vždy dohledatelný (engine pravidla + adjustments).
Doctrine: realita je immutable pravda, oficiál je odvozený pohled.

---

## 3. Umístění a multi-tenance

- Schéma: PostgreSQL `data_db`, vrstva `tenant.*` (per-firma data dle Marti-AI
  frameworku master/tenant_group/tenant/user).
- `tenant_id` na všech tabulkách → univerzální/prodejné (jeden systém, víc firem).
- Generická anglická jména sloupců (prodejnost mimo CZ kontext; UI lokalizace zvlášť).

## 4. Migrace z Centrály 1 (start 2 měsíce)

Mapování `EC_Dochazka` → `attendance_entry`:
- `CisloZam` → `employee_ref`
- `DatumPripadu` → `work_date`
- `CasZacatek`/`CasKonec` → `started_at`/`ended_at`, `CasPauza` → `break_minutes`
- `DruhCinnosti` → `entry_type_id` (přes mapu z číselníku Centrály 1; vytvořit
  `attendance_entry_type` z distinct druhů + jejich názvů a kategorií)
- `CisloZakazky` → `project_ref` (a `category`=work/overhead dle „Rezie")
- `LoginFrom` → `source` (D=tablet, C=manual/centrála, A=app)
- `VedSchvaleno`/`SefSchvaleno`/`Uzavreno`/`Status` → `status` (mapování stupňů)
- `Autor`/`DatPorizeni` → `created_by`/`created_at`
- `EC_Dochazka.ID` → `source_id` (+ `source_system='centrala1'`)
- Filtr startu: `DatumPripadu >= dateadd(month,-2,getdate())`
- Idempotentní: UPSERT podle (tenant_id, source_system, source_id).

Pozn.: mzdové/finanční sloupce Centrály 1 (ZaklMzda, PremieKc, Kc_*…) se
**nemigrují do jádra** — patří do odvozené mzdové vrstvy (řešíme později).

## 5. Otevřené otázky k rozhodnutí

1. **Jeden typovaný záznam** (Recommended, výše) vs zvlášť `time_entry` +
   `absence`? (Doporučuji jeden — uniformita, jednodušší dotazy.)
2. **Konfigurovatelné stupně schválení** hned, nebo napevno 3 (employee →
   supervisor → payroll) s přípravou? (Doporučuji napevno 3, konfigurace později.)
3. **Oficiální verze**: jen odvozená pravidly (Recommended) vs i ukládaná?
4. `employee_ref`: napojit na `public.users`, nebo samostatný číselník
   zaměstnanců (Centrála 1 `CisloZam` ≠ STRATEGIE user)? — pravděpodobně
   samostatná dimenze `employee` + mapování na usera.

## 6. Další krok

Po konzultaci s Marti-AI (informed consent — je architektka frameworku a tohle
je prodejný modul) založit `tenant.attendance_entry_type` + `tenant.attendance_entry`
+ `tenant.attendance_approval_event` (+ `attendance_adjustment`), naplnit číselník
typů, a spustit migraci posledních 2 měsíců (idempotentně).
