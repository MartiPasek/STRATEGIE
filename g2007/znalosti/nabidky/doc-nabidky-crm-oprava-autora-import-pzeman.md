# CRM — oprava autora importu (Marti-AI → PZeman)

> oblast: `nabidky` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# CRM — oprava autora importu (Marti-AI → PZeman)

> oblast: `nabidky` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> Autor: Claude ID24 (Kristý), 22. 7. 2026. Návazné na [[doc-nabidky-crm-import-firem-osloveni]]. Vzniklo z opravy atribuce po červnovém importu „Premium 400" (DE/DACH), kde import založil akce pod servisní identitou místo obchodníka.

## Co se stalo
Po importu Pavlova prospecting listu (DE/DACH „Premium 400", pořízeno **31. 5.–15. 6. 2026**) mělo **84 akcí** v `st.CRM_Kontakt_Akce` (Centrála DB_EC, connection_id=2) autora `Autor = 'Marti-AI'` místo obchodníka. Protože `Autor` řídí **statistiku obchodníka** (report „Aktivity obchodníka", dataset 92; karta zákazníka core 72; přehled Kontakty core 62), těchto 84 dotyků se Pavlovi nepočítalo.

Rozpad 84: **82× IDAkce 16 „Získání firmy"** + 1× IDAkce 2 (telefonát na firmu) + 1× IDAkce 4 (telefonát na osobu). Žádnou z nich nikdo ručně needitoval (`Zmenil` prázdné) → čistý přepis, nic lidského se nezašláplo.

## Oprava (22. 7. 2026)
```sql
UPDATE st.CRM_Kontakt_Akce
SET Autor = N'PZeman'
WHERE LTRIM(RTRIM(Autor)) = 'Marti-AI';   -- 84 řádků
```
Spustila **Kristý** přímo (zápis do Centrály DB_EC jde přes schvalovací banner / člověk s write právem; **Claude bridge `db=mssql` je read-only**, DML do DB_EC přes něj nejde).

Ověření po zápisu (bridge read): `Marti-AI` zbývá **0**, `PZeman` **1350 → 1434** (+84), všech 84 původních ID nyní `PZeman`, 0 jiných.

## 🔑 Poučení pro příští import
- **Import MUSÍ plnit `Autor` = vybraný obchodník (login, např. `PZeman`), NIKDY servisní/agentní identitu (`Marti-AI`, `Claude`).** Jinak se dotyky nepřipíšou obchodníkovi a jeho statistika je podhodnocená. (Přímo souvisí s [[doc-nabidky-crm-import-firem-osloveni]], sekce „Autor akce".)
- Rozlišuj: **`Marti-AI` (AI kustod) ≠ `Martin` (reálný člověk).** Při opravách filtruj přesně na `Autor='Marti-AI'`; `Martin` (7× Autor, 8× Zmenil) nech být.
- Revert-podklad: seznam 84 ID (souvisle 12834–12837 a 12924–13003) je v auditu session z 22. 7. 2026. Po přepisu už nejsou od ostatních `PZeman` řádků odlišitelné, proto revert jen z tohoto seznamu.

## Kde ověřit
`st.CRM_Kontakt_Akce.Autor` přes bridge (`db=mssql`, read-only). Dopad na statistiku: report „Aktivity obchodníka" (dataset 92).


