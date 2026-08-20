# Práce o víkendu a o svátku jde CELÁ nad fond (kancelářští)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Práce o víkendu a o svátku jde CELÁ nad fond (jen kancelářští)

**Pravidlo (Peťa, 5. 8. 2026).** U lidí, kterým docházkový automat dopichuje do fondu
(kategorie s `dopichavat_fond=true`, dnes „Volná kancelářská doba (bez přesčasů)"),
platí: **fond se plní jen v PRACOVNÍCH dnech.** Co si člověk odpracuje v sobotu,
v neděli nebo o svátku, se **celé** překlápí do **nenárokové složky (nad fond)** —
ne jenom přesah nad 8 h.

**Proč.** FPD za měsíc = odpracováno + absence + dopíchnuto do fondu − nad fond.
Kdyby se víkendová práce počítala do fondu, snížila by člověku dopíchnutí ve všední
dny a měsíc by mu „seděl" jen díky sobotě. Fond má být naplněn pracovními dny;
víkend je vždycky práce navíc.

**Dílny a hodinoví se to netýká** — automat na ně nejede vůbec (nemají
`dopichavat_fond`), jejich FPD = odpracováno + absence.

## Kde to je v kódu

`g2007.python` kod=**`att_automat_level_day`**, CTE `netf`: denní fond se bere
z `fondp`, ale pro nepracovní den se přepíše na **0**:

```sql
CASE WHEN EXISTS (SELECT 1 FROM tenant.att_calendar_day cd
      WHERE cd.tenant_id=:t AND cd.day=p.entry_date
        AND (cd.is_workday=false OR COALESCE(cd.is_holiday,false)=true))
  THEN 0 ELSE f.fond END AS fond
```

Fond 0 → `net >= fond` → INSERT vloží `nenarokova` ve výši celého netto času a
žádné `fond_doplneni` nevznikne. Pracovní dny beze změny.

**Chybí-li den v kalendáři `tenant.att_calendar_day`, bere se jako PRACOVNÍ**
(bezpečnější — jinak by výpadek kalendáře odepsal lidem celý měsíc do nenárokových).
Kalendář plní Kristý; automat na chybějící dny loguje warning.

## Gotchy ověřené při zavádění

- **Docházka i kalendář jedou na `tenant_id = 2`**, ne 1. Dotaz s tenantem 1 vrátí
  prázdno a vypadá to jako „kalendář není naplněný".
- **Automat se dá pustit cíleně** na jednoho člověka a den:
  `POST /api/v1/erp/app/erp_registry/run` s `{"kod":"att_automat_level_day","args":[2,4,<emp_id>,"2026-07-06"]}`.
  Je idempotentní (smaže automatové řádky dne a vloží znovu). Noční catchup jede
  jen posledních pár dnů, starší měsíc takhle nedožene.
- **`:t` v textu skriptu rozbíjí zápis přes SQL most** — SQLAlchemy si ho vezme jako
  vlastní bind parametr („A value is required for bind parameter 't'"). Řešení:
  rozdělit literál a vložit dvojtečku přes `|| chr(58) ||`.

## Dopad při zavedení (červenec 2026)

Kancelářští s prací o víkendu/svátku: Kristýna Marešová 6. 7. (svátek) 4,75 h,
Saad Jarrar 18. + 19. 7. po 2 h. Po přepočtu FPD Jarrar 175,98 / 176,
Marešová 175,82 / 176. Ostatní víkendové dny patřily lidem, které nekontrolujeme
(Pašek, Honomichl) nebo mimo mzdy (Havlát).

