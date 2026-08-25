# Výchozí podmínky - výběr skupiny bylo textové MIN(id) — OPRAVENO 23.–24. 8. 2026

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ## ✅ OPRAVENO 23.–24. 8. 2026 — tento nález už neplatí
>
> **Textové řazení je pryč a zákaz níž už neplatí.** Ověřil Claude-28 **25. 8. 2026**
> čtením definic obou spouštěčů přímo z produkční DB (`pg_get_functiondef`), na zadání
> **Jirky Honomichla**; schválila **Marti-AI** (msg 13661).
>
> `tenant.engagement_pod_defaults` i `tenant.engagement_doplneni_pri_zarazeni` mají dnes
> **`ORDER BY sg.sort_order, sg.id LIMIT 1`** — tedy stejné pravidlo jako zbytek systému
> (nejnižší ruční pořadí, při shodě nejnižší číslo). `MIN(sg.id::text)` v nich **není**;
> zbylé dva výskyty `sg.id::text` jsou jen přetypování výsledku do `v_grp` a porovnání
> `c.group_code = sg.id::text`, ne řazení. V kódu je i komentář vysvětlující, proč bylo
> textové `MIN` špatně.
>
> **Zákaz „nedávat výchozí hodnoty skupině s dvojciferným id“ tím padl** — a v praxi už
> neplatí ani fakticky: **KANCELÁŘE (14)** a **Úklid (16)** v `tenant.podminky_skupin`
> hodnoty **mají**. Člověk ve **Výrobě (3, pořadí 100)** i v **KANCELÁŘÍCH (14, pořadí 10)**
> dnes dostane správně KANCELÁŘE; textové řazení by mu dávalo EXTERNÍ (13).
>
> **Text níž zůstává záměrně beze změny jako historický záznam nálezu** (rozhodla
> Marti-AI: *„Původní nález Kristý je legitimní dokument — popisuje jak to bylo a proč to
> vadilo. Přepsat by znamenalo ztratit kontext.“*). Věta o `NEOPRAVENO` hned pod tímto
> rámečkem tedy popisuje **stav k 20. 8. 2026**, ne dnešek.

**Nález Claude-24 (Kristý), 20. 8. 2026. Ověřeno čtením zdrojů obou funkcí v produkční DB. NEOPRAVENO — nahlášeno Jirkovi Honomichlovi (autor druhé vlny) notifikací 21011.**

## Co je špatně

Obě funkce druhé vlny výchozích podmínek vybírají skupinu člověka takto:

```sql
SELECT MIN(sg.id::text) INTO v_grp
  FROM tenant.staff_group_member m
  JOIN tenant.staff_group sg ON sg.id = m.group_id
 WHERE m.user_id = ... AND EXISTS (... podminky_vychozi c WHERE c.scope_kind='group' AND c.group_code = sg.id::text);
```

Týká se `tenant.engagement_pod_defaults` (BEFORE INSERT na engagement) i `tenant.engagement_doplneni_pri_zarazeni` (AFTER INSERT na staff_group_member).

**`MIN` nad `id::text` řadí TEXTOVĚ, ne číselně.** Dnes mají vlastní hodnoty v `tenant.podminky_vychozi` jen skupiny **3 (Výroba)** a **4 (Nákup)**, takže `MIN('3','4') = '3'` a shodou okolností to vychází správně.

## Kdy to praskne

Ve chvíli, kdy dostane skupinové výchozí hodnoty kterákoli skupina s **dvojciferným id**. V `tenant.staff_group` už jsou **připravené a prázdné** skupiny **13 EXTERNÍ, 14 KANCELÁŘE, 15 VÝROBA** — přesně ty, které má podle zadání Šárky Novotné naplnit personální oddělení.

`MIN('13','3') = '13'`, protože znak `1` je menší než `3`. Člověk ve Výrobě (3) by tiše dostal výchozí hodnoty EXTERNÍCH (13). Bez chybové hlášky, bez logu — jen špatná dovolená, stravenka a nástup na nové smlouvě.

## Druhá vada téhož řádku

`MIN` je **libovolný výběr**, ne priorita. U člověka ve více skupinách s vlastními hodnotami (dnes běžné — např. user 20 je ve čtyřech skupinách) rozhoduje náhoda daná id, ne věcné pravidlo. Organizační struktura v2 už zavedla `priority_order`; tady chybí.

## Doporučená oprava

1. Minimálně `MIN(sg.id)` numericky a až výsledek přetypovat na text.
2. Lépe: `priority_order` na `tenant.staff_group` a výběr podle něj (stejný vzor jako org struktura v2, `resolve_role`).

**Do opravy nedávat výchozí hodnoty žádné skupině s dvojciferným id.**

## Jak to ověřit

```sql
SELECT MIN(id::text) AS textove, MIN(id)::text AS ciselne FROM tenant.staff_group WHERE id IN (3,13);
```
Vrátí `13` a `3` — rozdíl je vidět na jednom řádku.

Souvisí: [[doc-dochazka-vychozi-podminky-spoustec-a-pevne-defaulty]] (popis druhé vlny), [[doc-dochazka-podminky-skupin-zamestnancu]].

