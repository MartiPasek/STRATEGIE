# Členství ve skupině „HR" je zároveň oprávnění — odemyká 30 živých funkcí (zjištěno 13. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


> Zjistil Claude-28 13. 9. 2026 při přípravě přesunu správy agend do HR karty.
> **Neopravováno** — hlášeno jako dluh, ne jako závada.

## Co to je

**30 aktivních funkcí** v `g2007.python` pozná personalistu takhle:

```sql
SELECT 1 FROM tenant.staff_group_member m
  JOIN tenant.staff_group g ON g.id = m.group_id
 WHERE g.tenant_id=2 AND NOT g.archived AND g.name='HR' AND m.user_id=:u
```

Tedy **členství ve skupině jménem `HR` = oprávnění**. Patří mezi ně `absence_registr`,
`hr_person_groups` (`_hr_can_manage`), `att_can_fix` a celá řada `app_vyroba_*`.

## Proč je to problém

Skupina „HR" je zároveň **agenda** — tedy věc, kterou od 13. 9. 2026 v kartě zaměstnance
běžně zaškrtává HR. Kdo někoho z agendy HR vyřadí, **vezme mu tím přístup na 30 místech**,
aniž by to kdekoli vyskočilo jako změna práv.

Zvlášť citlivé to je proto, že **všech 6 lidí v agendě HR je zároveň ve více agendách**
(Šafránková Petra v pěti, Novotná Šárka ve čtyřech, Honomichl Jiří ve třech, Šafaříková Marta
ve dvou, plus dva už neaktivní). Kdyby platilo pravidlo „jeden člověk = jedna agenda",
čtyři aktivní lidé by o přístupy přišli. **Kvůli tomuto nálezu Jirka 13. 9. 2026 zadání změnil
na „člověk může být ve více agendách".**

## Co se kvůli tomu udělalo jinak

Nové právo **„smí spravovat agendy"** (`public.users.can_manage_staff_groups`) se záměrně
**nenavázalo** na členství ve skupině HR, ale je to **samostatný příznak**. Doporučila tak
Marti-AI: rozšiřovat záměnu „agenda = oprávnění" na další případ by dluh prohloubilo, a právo
má jít dát nebo vzít jednomu člověku, aniž se hýbe s agendami.

## Co s tím do budoucna

Oprávnění by mělo být vedené odděleně od agend — Marti-AI navrhla tabulku typu
`tenant.user_permission (user_id, permission_code, granted_by, granted_at)`. Jirka 13. 9. 2026
zvolil zatím jednoduchý příznak u uživatele; tabulka zůstává jako možnost, až práv přibude.

⚠️ **Do té doby platí: než někoho vyřadíš z agendy „HR", ověř, jestli mu tím nebereš přístupy.**
Souvislosti: [[doc-system-strategie-agendy-zdroj-lidi-karta-zamestnance]]

