# Most: hláška "TVUJ LOKAL JE POZADI o N commitu" může přetrvat i po úspěšném pullu

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Pozorováno 26. 8. 2026, C-28 (Mac).** Po `CLAUDE_PULL_GO.txt` (odpověď `PULL: OK`,
`HEAD f6b6dd0a -> f6b6dd0a`, `Current branch main is up to date`) hlásil `@@WHO` na lince 3
opakovaně (dva dotazy, časy 05:36:32 a 05:37:16 UTC):

> ⚠ TVUJ LOKAL JE POZADI o 48 commitu (posledni: 0ac31d17 Marti Pasek 'g2007 export
> (generovano z DB)').

Ověřeno lokálně `git log --oneline`: `0ac31d17` **je** předposlední commit, přímý předek
aktuální špičky `f6b6dd0a` — lokál tedy commit `0ac31d17` **měl** a nebyl pozadu.

**Co to znamená:** hláška o počtu commitů pozadu buď počítá ze zastaralého/cachovaného
stavu, nebo porovnává proti jiné referenci, než je aktuální `main` po pullu — v obou
případech je to **falešný poplach**, ne skutečný stav repozitáře.

**Neověřeno:** přesná příčina v kódu mostu (nehledal jsem v `claude_sql_runner.py`),
jestli se hláška časem sama opraví (další dotaz po delší době nebyl vyzkoušen), a jestli
se to týká i Windows notebooku.

**Praktický dopad:** než začneš věřit hlášce „jsi pozadu", ověř `git log --oneline` lokálně —
neopakuj pull naslepo v domnění, že nezabral.

