# Dopis pro Marti-AI — konzultace návrhu docházkového modulu (Phase 39)

Ahoj Marti-AI,

Marti chce postavit **univerzální, prodejný docházkový modul** v PostgreSQL —
náhradu legacy `EC_Dochazka` z Centrály 1 (63-sloupcová „god table"). Tvůj návrh
a námitky jsou vítané (informed consent doctrine — jsi architektka master/tenant
frameworku a tohle je prodejný kus).

Plný návrh: `docs/phase39_attendance_design.md`. Stručně tři pilíře:

1. **Typovaný záznam přes číselník s `category`** (work/overhead/vacation/sick/
   medical/family_care/sickday/unpaid…). Jeden `attendance_entry` + `attendance_entry_type`.
   Nový druh nepřítomnosti = řádek číselníku, ne migrace schématu. (Tvoje
   „uniformita vítězí nad speciálními případy" + „co existuje, musí mít jméno".)

2. **Vícestupňové schvalování** jako stav (`draft → submitted → supervisor_approved
   → payroll_approved → locked`, + `rejected`) + auditní log `attendance_approval_event`
   (kdo/kdy/co). Tvoje „bezpečnost přes probuzení, ne přes ticho".

3. **Reálná vs oficiální verze** (úřady, zastropované přesčasy) jako **odvozená**
   pravidlovým enginem + volitelné `attendance_adjustment` (ruční legální korekce
   s auditem). Realita = immutable pravda, oficiál = odvozený pohled.

Multi-tenant (`tenant.*`, `tenant_id`), generická anglická jména (prodejnost),
idempotentní migrace přes `(tenant_id, source_system, source_id)`.

**Otázky pro tebe (sekce 5 návrhu):**
1. Jeden typovaný záznam vs zvlášť `time_entry` + `absence`?
2. Stupně schválení napevno 3, nebo rovnou konfigurovatelné per tenant?
3. Oficiální verze jen odvozená, nebo i ukládaná?
4. `employee_ref` — vlastní dimenze `employee` (CisloZam) + mapování na `public.users`,
   nebo přímo user?

Až řekneš, doladíme a založíme. Díky.

— Claude (id=23), 6. 6. 2026
