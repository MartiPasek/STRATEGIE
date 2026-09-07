# Kdy se doplnění do fondu „spočítalo" NENÍ důkaz — noční automat razítko každou noc přepíše (7. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Past

U řádku `fond_doplneni` (`tenant.att_entry`, `source='automat'`) vypadá `created_at` jako „kdy se to spočítalo". **Není to pravda.** Docházkový automat (`g2007.python` kód `att_automat_level_day`) při každém běhu nejdřív **fyzicky SMAŽE** všechny automatické řádky (`fond_doplneni`, `nenarokova`) ve svém okně a pak je vloží znovu:

```
DELETE FROM tenant.att_entry e USING tenant.att_entry_type et
WHERE et.id=e.entry_type_id AND e.tenant_id=:t AND e.source='automat'
  AND et.code IN ('fond_doplneni','nenarokova') ...
```

Není to `superseded`, není to UPDATE — je to smazání a nový INSERT. Takže `created_at` říká jen **„kdy tudy naposled prošel noční automat"**, a stará hodnota je nenávratně pryč (žádná historie, řádek fyzicky neexistuje).

## Důkaz z dat (7. 9. 2026)

Doplnění do fondu, seskupeno podle dne:

| entry_date | naposledy spočteno |
|---|---|
| 24.–28. 8. | 4. 9. 00:00 |
| 1.–4. 9. | 7. 9. 00:00 |

Celé okno má shodné razítko z poslední noci. Dny 24.–28. 8. mají 4. 9., protože už z okna vypadly a od té doby na ně automat nesáhl.

## Co z toho plyne

1. **Nestavěj kontrolu na časovém odstupu** „doplnění vzniklo N minut po zadání absence". U čerstvých dnů razítko přežije nanejvýš do půlnoci.
2. **Chyba v přepočtu se u čerstvých dnů sama zahladí.** Noční automat den v okně přepočítá znovu a správně. Trvalá škoda vzniká jen u dnů, které z okna vypadly (`days_back`, default 4) — přesně proto byl Saad Jarrar 19. 8. 2026 rozbitý až do ručního zásahu, zatímco stejná chyba na včerejšku by zmizela sama.
3. **Kontrola musí koukat na výsledek, ne na časy.** Viz níže.

## Jak to kontrolovat správně

Hledej dny, kde vedle sebe stojí absence i automatické doplnění a **součet přeteče fond**. Doplnění má den dorovnat *do* fondu, takže jakmile s absencí přeteče, je spočtené bez ní:

```sql
WITH slozky AS (
  SELECT e.employee_id, e.entry_date,
         sum(CASE WHEN t.category = 'presence' AND t.code <> 'fond_doplneni'
                       AND COALESCE(e.source,'') <> 'automat'
                  THEN COALESCE(e.hours, 0) ELSE 0 END) AS prace,
         sum(CASE WHEN t.category = 'absence' THEN COALESCE(e.hours, 0) ELSE 0 END) AS absence,
         sum(CASE WHEN t.code = 'fond_doplneni' THEN COALESCE(e.hours, 0) ELSE 0 END) AS doplneni
  FROM tenant.att_entry e
  JOIN tenant.att_entry_type t ON t.id = e.entry_type_id
  WHERE e.tenant_id = 2 AND e.entry_date >= DATE '2026-07-01'
    AND COALESCE(e.status,'') <> 'superseded'
  GROUP BY e.employee_id, e.entry_date)
SELECT em.full_name, s.entry_date, COALESCE(d.fpd, 8) AS fond,
       s.prace, s.absence, s.doplneni,
       round(s.prace + s.absence + s.doplneni - COALESCE(d.fpd, 8), 2) AS navic
FROM slozky s
JOIN tenant.att_employee em ON em.id = s.employee_id
LEFT JOIN tenant.att_day_summary d
       ON d.tenant_id = 2 AND d.user_id = em.user_id AND d.datum = s.entry_date
WHERE s.absence > 0 AND s.doplneni > 0
  AND s.prace + s.absence + s.doplneni > COALESCE(d.fpd, 8) + 0.10;
```

**Ověřeno na Saadovi Jarrarovi 19. 8. 2026**: práce 3,98 + dovolená 4,00 + doplnění 4,02 = 12,00 proti fondu 8,00 → nález sedí na setinu. Na živých datech od 1. 7. 2026 nula falešných poplachů (dnů s absencí i doplněním zároveň jsou vůbec jen 3 a všechny sedí).

Fond ber z `tenant.att_day_summary.fpd` (per člověk a den, respektuje zkrácené úvazky). Tolerance 0,10 h kvůli zaokrouhlování.

## Kde se to projevilo

Naplánované úlohy Peťy `kontrola-prepocet-fondu-po-absenci` (denně 16:30) a `tydenni-souhrn-prepoctu-fondu` (pondělí 5:00) původně hlídaly právě ten časový odstup. Peťa se 7. 9. 2026 zeptala „to je otázka, jestli to je to, co hlídáš" — a byla to trefa. Obě úlohy přepsány na kontrolu výsledku. Dělba: denní kouká 14 dní zpět a chytá případ dřív, než ho noc zahladí; pondělní jde od 1. 7. a chytá dny, které z okna vypadly a zůstaly rozbité natrvalo.

## Souvisí

- `doc-dochazka-absence-zpetne-prepocet-fondu` — původní nález a oprava (20. 8. 2026, commit `d2d9ff6f`)
- `doc-dochazka-prepocet-fondu-po-absenci-tri-vrstvy` — tři cesty, kudy se přepočet spouští
- `doc-dochazka-automat-fond-doplneni` — jak automat počítá doplnění a nenárokovou
- `doc-dochazka-automat-prepocet-guard-vlastni-radek` — jiná past téhož automatu (5. 8. 2026)

