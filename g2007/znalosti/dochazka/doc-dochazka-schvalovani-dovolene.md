# Schvalování dovolené / absencí — model a stav (21. 7. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Schvalování dovolené / absencí — model a stav (21. 7. 2026)

**Zadal:** Marti Pašek (majitel/jednatel) · **Rozhodl:** Jirka · **Návrh implementace:** Marti-AI (msg 11036)
**Oblast:** docházka · **Stav k 21. 7. 2026: ✅ NASAZENO A ŽIVÉ** (postavil Claude-28/Jirka
na výslovné pověření Marti-AI „Jeďte, nečekejte na mě" msg 11042). Realizovaný stav = §6.

---

## 1. ⚠️ PŮVODNÍ stav (rozbitý, PŘED opravou 21.7. — už neplatí, viz §6)

Žádost o absenci (`att_absence_request`) dnes routuje notifikaci vedoucímu přes
**PG funkci `tenant.resolve_role(2, emp, 'attendance_supervisor')`** (endpoint v `router.py`,
`att_absence_request`). Ta jde nahoru org stromem a hledá post s odznakem `attendance_supervisor`
v `tenant.org_role_flag`.

**Problém:** odznak je jen na postech DIVIZE 1–8 a ty jsou **skoro všechny neobsazené**
(jediný obsazený = DIVIZE 1 = Marti). Takže `resolve_role` vrátí většinou NULL a kód spadne
na fallback:

```python
_abs_notify(s, mgr if mgr and int(mgr) != uid else 1, ...)   # else 1 = Marti Pašek
```

→ **Prakticky VŠECHNY žádosti o dovolenou dnes chodí Martimu (uid 1).** To je špatně, řešíme to.

**🚫 NEsahat na `resolve_role` kvůli tomuhle** — mění se to novou funkcí, ne úpravou staré
(viz níže). `resolve_role` slouží dál pro `presence_recipient` apod.

## 2. Cílový model (Marti Pašek, upřesněno 21. 7.)

Dovolenou schvaluje **určený schvalovatel podle skupiny žadatele**; v jeho nepřítomnosti
i jeho zástup. **PĚT skupin:**

| Skupina | Definice (kdo do ní patří) | Schvalovatel | Zástup |
|---|---|---|---|
| výroba | podstrom pod post 24 (VEDOUCÍ VÝROBY), `je_kvalifikace=false` | **Dušan Havlát** | Marek Honal (existuje v datech) |
| nákupčí | lidé na postu 20 (NÁKUPČÍ div4) | **Peťa Šafránková** | *určí personální* |
| nákup automatizace | lidé na postu 70 (NÁKUPČÍ div5) | **Miroslav Mareš** | *určí personální* |
| projekty | lidé na postu 53 (VEDOUCÍ PROJEKTŮ) | **Jiří Veverka** | *určí personální* |
| ostatní | fallback — kdo nespadl do žádné skupiny výše | **Šárka Novotná** | — |

**Pozn.:** model je **hybridní záměrně** — Peťa schvaluje nákupčím ne proto, že je jejich org
nadřízená (je jedním ze 4 nákupčích), ale protože to tak Marti rozhodl. Proto **dedikovaná
tabulka, ne org strom** (viz §3).

### Pravidlo zástupu (klíčové)
- Vedoucí **přítomen** → žádost jen jemu.
- Vedoucí **nepřítomen** ten den → žádost přijde **oběma** (vedoucímu I zástupci) současně;
  schválit může **kdokoli z nich, kdo je dřív**. Není to „přepnutí na zástup", ale paralelní eskalace.
- **„Nepřítomen ten den"** = schválená absence (`att_absence_request.stav='approved'` pokrývající
  datum) NEBO záznam dovolená/nemoc/OČR v `att_entry` na **první den dovolené žadatele**
  (ne den podání — zajímá nás, kdo schvaluje v době, kdy člověk chybí).
- Dokud zástup není určen, `resolve_approvers` vrátí **jen vedoucího** i v nepřítomnosti
  (bezpečné — radši schválí vedoucí po návratu, než aby to spadlo nečekaně).

## 3. Implementace (Marti-AI, její schéma)

- **Nová funkce `tenant.resolve_approvers(p_tenant, p_emp, p_datum) RETURNS SETOF bigint`** —
  vrací SEZNAM uid k notifikaci (vedoucí + zástup v nepřítomnosti). `resolve_role` BEZE ZMĚNY
  (jinak breaking change 10+ callsitů).
- **Nové tabulky** `tenant.att_approver_group` (skupina + je_fallback + sort_order) +
  `tenant.att_approver_group_member` (post_id + subtree) + `tenant.att_approver` (group_id +
  employee_id + je_zastupce + zastupuje_employee_id). Oddělené od org dat (schvalování ≠ org linie).
- **Napojení:** endpoint `att_absence_request` přepnout z `resolve_role` na `resolve_approvers`
  a notifikovat CELÝ vrácený seznam (dnes notifikuje jen jedno uid).
- Číselník typů absence pro „nepřítomnost" brát ze **skutečných kódů** `att_entry_type`
  (Peťa/Claude-26 přidala 21.7. Dovolená/Lékař/Sickday/Neplacené), ne natvrdo.

## 4. Otevřené / čeká

- **Zástupci pro Peťu, Veverku, Mareše** — v datech nejsou; určí **personální (Šárka Novotná)
  s Marti Paškem a Veverkou/Šafránkovou** (email odeslán 21.7.). Doplní se INSERTem do
  `att_approver`, bez změny kódu.
- **Dušan → Marek Honal** je jediný jistý zástup (naplní se rovnou).
- Po nasazení ověřit, že žádost o absenci fakticky chodí správnému schvalovateli, ne Martimu.

## 5. Pro ostatní programátory (shrnutí)

- Absence approval = **`resolve_approvers`**, NE `resolve_role`. `resolve_role` nechte být.
- Přiřazení schvalovatelů žije v `tenant.att_approver*`, ne v org stromu.
- Skupiny se počítají přes posty 24/20/70/53 (+ kvalifikační filtr u výroby, viz
  [[doc-dochazka-opravy-navrh]] §17.1) + fallback Šárka.

---
**Souvisí:** `docs/org_struktura_v2.md` · znalost `doc-dochazka-opravy-navrh` (§17 je_kvalifikace)



## 6. ✅ REALIZOVANÝ STAV (nasazeno 21. 7. 2026, Claude-28/Jirka)

Postaveno přesně dle plánu §3, ověřeno naostro. Marti-AI to pověřila nám (běh se jí
kouskoval na turn-limitech, msg 11042 „Jeďte").

### 6.1 Tabulky (tenant, vlastní Marti-AI) — DDL write #1260
- `tenant.att_approver_group` (id, tenant_id, nazev, je_fallback, sort_order, created_at)
- `tenant.att_approver_group_member` (id, tenant_id, group_id, post_id, subtree)
- `tenant.att_approver` (id, tenant_id, group_id, employee_id, je_zastupce, zastupuje_employee_id, aktivni, created_at)

### 6.2 Naplněné skupiny (write #1262, po úklidu #1264 — 4 skupiny)

| Skupina | sort | post (member) | Vedoucí (emp/uid) | Zástup (emp/uid) |
|---|---|---|---|---|
| výroba | 1 | 24 (podstrom) | Dušan Havlát (emp 39 / uid 41) | Marek Honal (emp 52 / uid 85) |
| nákupčí | 2 | 20 | Petra Šafránková (emp 1 / uid 18) | — (doplní personální) |
| projekty | 4 | 53 | Jiří Veverka (emp 3 / uid 106) | — (doplní personální) |
| ostatní | 9 | (fallback) | Šárka Novotná (emp 26 / uid 13) | — |

**Post 70 (nákup automatizace / Mareš) ZRUŠEN (varianta A, Jirka 21.7.):** ověřeno, že
všech 6 lidí na postu 70 je zároveň nákupčí na postu 20 → skupina by nikoho nezachytila
(nákupčí má vyšší prioritu). Ti lidé = nákupčí → schvaluje Peťa. Mareš schvalovatel není.

### 6.3 Funkce `tenant.resolve_approvers(p_tenant, p_emp, p_datum) SETOF bigint` — write #1263
1. Najde skupinu žadatele podle `sort_order` (první shoda; subtree = rekurze pod post_id
   BEZ `je_kvalifikace`; jinak přesný post). Když nic → fallback skupina.
2. Vrátí uid: **vedoucí VŽDY** + **zástup** když (a) jeho vedoucí je nepřítomen p_datum
   [approved absence typu vacation/medical/family_care kryjící den], NEBO (b) vedoucí je sám
   žadatel (žádá si o vlastní absenci → jde na zástup). Vyloučí žadatele (neschvaluje sám sobě).

### 6.4 Napojení endpointů (commity 4e231ec5 + dd7ed6e9)
Helper **`_abs_resolve(s, emp, requester_uid)`** (router.py) volá `resolve_approvers(2, emp,
CURRENT_DATE)` → list uid; prázdné → **Šárka (13)**, když žádá sama Šárka → Marti (1) poslední
záchrana. `_abs_notify` nově přijímá i **seznam** (notifikuje všechny schvalovatele).
Přepojeno **všech 7 absenčních míst**: dovolená, OČR (nové+ukončení), nemocenská
(nové+ukončení), lékař, ohlášení absence přes chat. **`resolve_role` se pro absence UŽ
NEPOUŽÍVÁ** (zůstává jen pro presence_recipient / day-confirm).

> ⚠️ **Pozn. k datu:** endpoint volá `resolve_approvers` s **CURRENT_DATE** (kdo je k dispozici
> schválit teď), ne s prvním dnem dovolené jak původně navrhla Marti-AI. Důvod: schválení
> probíhá při podání žádosti, takže rozhoduje, kdo je přítomen dnes. Kdyby se to chtělo
> vázat na první den absence, je to jednořádková změna (předat datum_od místo CURRENT_DATE).

### 6.5 Ověřeno naostro
- resolve_approvers: montér→Dušan, nákupčí→Peťa, projekty→Veverka, Dušan(vlastní)→Marek. ✅
- Reálný POST žádosti o dovolenou jako Jirka (ostatní) → **approvers=[13] Šárka, NE Marti**. ✅
- Test hned zrušen + testovací notifikace smazána (#1265). Žádná zbytková data.

### 6.6 Zbývá (data, bez změny kódu)
- **Zástupci pro Peťu a Veverku** — určí personální (Šárka + Marti + Veverka/Šafránková,
  email 21.7.). Doplní se INSERTem do `att_approver` (je_zastupce=true, zastupuje_employee_id).
  Do té doby jde jejich absence i jejich vlastní žádost na Šárku (fallback) — bezpečné.


