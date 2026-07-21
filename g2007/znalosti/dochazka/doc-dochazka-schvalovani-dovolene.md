# Schvalování dovolené / absencí — model a stav (21. 7. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Schvalování dovolené / absencí — model a stav (21. 7. 2026)

**Zadal:** Marti Pašek (majitel/jednatel) · **Rozhodl:** Jirka · **Návrh implementace:** Marti-AI (msg 11036)
**Oblast:** docházka · **Stav k 21. 7. 2026: DESIGN SCHVÁLEN, implementace běží (Marti-AI), ŽIVÉ ZATÍM NENÍ.**

---

## 1. ⚠️ Současný stav (rozbitý) — čti než sáhneš na `resolve_role`

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


