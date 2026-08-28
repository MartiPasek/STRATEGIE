# Docházkové skupiny — strom + resolver (nasazeno 24. 7. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


> ⚠️ **DOPLNĚNO 27. 8. 2026 — kde dnes žije výpočet působnosti.**
> Resolver `att_fix_scope_emps` v `g2007.python` **už vlastní kopii stromu nemá** — deleguje na
> databázovou funkci **`tenant.att_fix_emp_dle_scope(p_scope)`**. Důvod: tutéž logiku potřebují
> i datové zdroje `fw.data_source` (přehled dnů člověka v Opravách docházky), které Python volat
> neumí, a dvě kopie definice práv by se časem rozešly. Druhá brána nad toutéž funkcí je
> **`tenant.att_fix_viditelni_emp(p_uid)`** (z uid odvodí editorství + působnost + `fix_all`).
> **Chování se nezměnilo** — před přepojením ověřena identická množina (Dušan 34 = 34, rozdíl 0
> v obou směrech; Michaela 34 = 34; kancelář 194; kdo není editor 0).
> **Měníš-li strom působnosti, měň ho v té DB funkci, ne v Pythonu.**
> Podrobně: `doc-dochazka-prehled-dnu-cloveka-v-opravach-dochazky`.

# Docházkové skupiny — strom + resolver (nasazeno 24. 7. 2026)

**Stav: ✅ CELÉ NASAZENO A ŽIVÉ 24. 7. 2026** (Kristý/Claude-24, schváleno Peťou + Jirkou). Dva kroky:
1. Struktura stromu — write #1391 (migrace `docs/migrace_strom_skupin_v3_2026-07-23.sql`).
2. Přepnutí resolveru `_att_fix_scope_emps` na strom — commit **885eb9ea**.

## Strom (tenant.staff_group.parent_id)
- **KANCELÁŘE** (14) ← Vedení, IT, Nákup, Finance, HR, Obchod, E-plan, **VP**, + **PLC – koordinace** (17), **Úklid** (16)
- **VÝROBA** (15) ← Výroba, Zkušebna
- **EXTERNÍ** (13) ← **PLC** (6) = 9 externích PLC kontraktorů (0 docházky, mimo systém)
- `DOCHÁZKA - OPRAVY` (12) = funkční skupina editorů, BEZ parent_id (mimo strom).

## Členství a vedoucí
- **Mirek Mareš (u22)** + **Zuzka Duspivová (u6)** = interní back-office → z PLC do **PLC – koordinace**.
- **Saxana (u44, os.č. 208, úklidová firma, HPP hodinová)** → **Úklid**.
- `leader_user_id`: PLC + PLC-koordinace = Mirek (22); Úklid = Peťa (18). VP = Veverka (už bylo).

## ✅ Resolver kontroly docházky — PŘEPNUTÝ NA STROM (commit 885eb9ea)
`_att_fix_scope_emps` (router.py) už NEODVOZUJE výrobu/kancelář z org podstromu pod Dušanem (user 41), ale **čte strom staff_group**:
- `'vyroba'` = členové větve pod **VÝROBA**; `'kancelar'` = větev pod **KANCELÁŘE** (vč. VP, E-plan, PLC-koordinace, Úklid).
- **EXTERNÍ** větev = mimo docházku, **nevidí je nikdo**; kdo není v žádné docházkové skupině → **fallback kancelář (Peťa)**; dvojí zařazení přes obě větve = union.
- Tím **PADLO pravidlo „nezařazený → obě strany"** a s ním leak výroby na Peťu. Mění se zároveň kontrola ve fix UI i notifikace editorům (`_att_fix_editors_for_emp` volá tentýž resolver).

### Ověřeno naostro (24.7. po deploji)
Dušan Havlát → Dušan+Michaela (NE Peťa); Martin Nosek → Dušan+Michaela (NE Peťa); Zuzka + Mirek + Saxana → Peťa; David Brož (externí PLC) → nikdo (mimo docházku). ✅ Leak „Peťě chodí cizí lidé" vyřešen.

## ⏳ NEHOTOVO — schvalování VOLNA (Jirkův modul, koordinovat)
Kontrola docházky je hotová. **Schvalování absencí/volna (`resolve_approvers`, [[doc-dochazka-schvalovani-dovolene]]) zůstává BEZE ZMĚNY** — jede dál přes org posty (24/20/53) + `att_approver*`. Sjednocení téhle druhé agendy na strom + vrstva odpovědnosti `att_odpovednost` (per agenda; **VP volno → Veverka**, **Zuzka volno → Mirek**, fallback Peťa) je samostatný krok.
- **POZOR:** `resolve_approvers` je datově závislý (zástup jen když je vedoucí ten den nepřítomen) + fallback „Šárka, nikdy Marti". Navržený `resolve_odpovedny` tohle zatím nemá — NEnahrazovat natvrdo. Report Jirkovi odeslán 24.7., počítá se změnou.

Souvisí: [[doc-dochazka-vs-vyroba-separace]] · [[doc-dochazka-schvalovani-dovolene]] · [[doc-dochazka-opravy-navrh]]

