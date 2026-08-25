# Aktualnich smluv je 81, ale lidi 76 - peti chybi uzivatelsky ucet (25.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


Overil Claude-28 na zadani Jirky Honomichla 25. 8. 2026. Rozhodnuti Jirky: **nechat tak,
jen zapsat**, aby to priste nikdo neresil znovu.

## Fakt

`tenant.engagement` ma k 25. 8. 2026 **81 radku s is_current = true**, ale zivych lidi je
**76**. Rozdil je petice zaznamu, ktere maji **platnou smlouvu bez data ukonceni**, ale
zaroven:

- `att_employee.user_id` je prazdne (nemaji uzivatelsky ucet ve STRATEGII),
- `att_employee.is_active = false`,
- v `tenant.att_entry` nemaji **ani jeden** dochazkovy zaznam.

Podle stare Centraly (`ec.cis_zam`) jde o: **Lehky Jakub (13), Maresova 2 Kristyna (27),
Kasl Pavel (9019), Bohm Karel (9035), Pilny Roman (9104)**.

## Proc to nikomu nevadi

Vsechny obrazovky HR i mobilu parujou cloveka pres **uzivatelsky ucet** (`em.user_id IS NOT
NULL`), takze tahle petice se nikde neukaze - ani v Podminkach, ani v karte, ani v mzdach.
Mzdy navic ctou jen lidi s dochazkou. Neprojevi se tedy na zadnem cisle, ktere nekdo vidi.

## Kdy si na to vzpomenout

Kdyz nekdo hlasi, ze **nesedi pocet smluv proti poctu lidi**. Preover to takhle:

```sql
SELECT count(*) AS aktualnich_smluv,
       count(*) FILTER (WHERE em.user_id IS NULL) AS bez_uctu_neviditelni,
       count(*) FILTER (WHERE em.user_id IS NOT NULL AND em.is_active) AS zivi_lide
FROM tenant.engagement g
JOIN tenant.att_employee em ON em.id = g.employee_id AND em.tenant_id = g.tenant_id
WHERE g.tenant_id = 2 AND g.is_current;
```

## Souvislost

Vyplynulo pri stavbe historie zmen - tehle petici Sarka 24. 8. 2026 vyplnila prazdne
podminky nulami a v historii po tom zbylo 50 zaznamu, ktere nesly navazat na zadneho
cloveka. Ty zaznamy byly 25. 8. 2026 na rozhodnuti Jirky smazany jako nepotrebne
(nemely vliv na zadny vypocet a v zadne obrazovce nebyly videt).
Viz [[doc-dochazka-historie-podminek-uvazku-smluv-financi]].

