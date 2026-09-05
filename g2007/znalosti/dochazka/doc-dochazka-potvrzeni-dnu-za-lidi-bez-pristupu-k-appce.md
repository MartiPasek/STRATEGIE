# Potvrzení docházky za lidi, kteří se k němu nedostanou (Peťa 4. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Rozhodla Peťa 4. 9. 2026** při ruční kontrole srpna: *„prosím o potvrzení docházky Marešové a Kilbergra a všech, co nemají potvrzeno, protože oni se k tomu nijak nedostanou."*

## Pravidlo

Když člověk **nemá jak** si docházku potvrdit, potvrdí ji za něj HR. Nenechává se viset nepotvrzená — do mezd jde tak jako tak a nepotvrzený den jen kazí kontrolu.

Potvrzení se zapisuje do `tenant.att_day_confirm` s `confirmed_by_user_id` = ten, kdo potvrzoval (ne zaměstnanec), a **do `note` patří důvod** — ať je z dat vidět, že to nepotvrdil člověk sám.

## Dvě různé situace, obě řešené stejně

| Kdo | Proč nepotvrdil | Srpen 2026 |
|---|---|---|
| **Lidé, kteří jinak potvrzují** | Ojedinělý den jim propadl. Marešová má 49 potvrzení a chybělo jí jedno (20. 8.), Kilberger 38 a chybělo jedno (14. 8.). | 2 dny |
| **Karty z importu bez aplikace** | Vojtěch Purkar, Brigádník Saxana, Světlana Herejtová — karta vznikla importem, člověk **nemá mobilní aplikaci a potvrdit fyzicky nemůže**. Za celou dobu nepotvrdili ani jednou. Peťa 4. 9. 2026: *„vznikly importem a nemají appku, nemůžou potvrdit."* | 46 dnů |

Srpen 2026 srovnán 4. 9. 2026 — po zásahu **0 nepotvrzených dnů** s odpracovanou prací u lidí, kteří docházku vedou.

## Jak si to najít

```sql
SELECT DISTINCT e.employee_id, e.entry_date
FROM tenant.att_entry e
JOIN tenant.att_entry_type ty ON ty.id = e.entry_type_id
WHERE e.tenant_id = 2 AND ty.code = 'work' AND COALESCE(e.hours,0) > 0
  AND COALESCE(e.status,'') NOT IN ('superseded','announced')
  AND NOT EXISTS (SELECT 1 FROM tenant.att_day_confirm c
                   WHERE c.tenant_id = 2 AND c.employee_id = e.employee_id
                     AND c.day = e.entry_date AND c.confirmed_at IS NOT NULL);
```

Lidi s příznakem **„Bez docházky"** z podmínek vyřaď — ti se nekontrolují (viz `doc-dochazka-priznak-bez-dochazky-v-podminkach`).

## ⚠️ Příznak „Bez docházky" sedí na KARTĚ, ne na člověku

Zjištěno 4. 9. 2026. Jeden člověk může mít víc docházkových karet (doktrína #24) a příznak je vlastnost karty, ne osoby. **Marti Pašek** má tři karty — 2 a 41 příznak mají, **15 ne** (je neaktivní a nemá žádné aktuální podmínky, takže tam příznak ani není kam zapsat). Kdo napíše kontrolu s napojením přes `user_id`, vytáhne si i kartu bez příznaku a člověk mu z kontroly vypadne jako nekrytý.

Peťa 4. 9. 2026 k tomu: *„u Týnky se nám to dělo."* Čistá cesta je, aby kontroly braly příznak **za člověka** (má-li ho na kterékoli kartě, platí pro všechny) — dneska to tak není. Čte se na třech místech: `att_anomaly_scan`, `att_prazdny_den_fond`, `dochazka_kontrola_data`.

