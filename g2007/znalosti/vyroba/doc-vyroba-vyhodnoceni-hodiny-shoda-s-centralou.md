# Hodiny na zakazkach: STRATEGIE vs Centrala sedi (overeno 4.8.2026) + jak spravne porovnavat

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Hodiny na zakazkach: STRATEGIE vs Centrala

**Overeno 4. 8. 2026** (C28/Jirka) na obdobi leden-kveten 2026.

## Vysledek: sedi

| | |
|---|---|
| zakazek na obou stranach | 196 (identicka mnozina) |
| sedi presne (hodiny i pocty lidi) | **193** |
| lisi se | 1 (Rezie, o 1,15 h z 17 359) |
| celkem hodin | nase 39 063,31 vs Centrala 39 062,16 |
| **shoda** | **99,997 %** |

Mesicne (nase vyroba_work vs Centrala po spravnem filtru): leden 7 628,41 = 7 628,41 ·
unor 7 552,10 = 7 552,10 · brezen 8 519,94 = 8 519,94 · kveten 7 566,53 = 7 566,53.
Sedi na setiny.

## PAST: jak NEporovnavat (chyba, ktera vypadala jako 6 000 chybejicich hodin)

Naivni porovnani sum EC_Dochazka vs tenant.vyroba_work ukaze, ze nam za leden-cerven
chybi ~6 000 hodin. **Je to falesny poplach.** Import (sync_vyroba_work_ec) zamerne
NEimportuje:
- **absence** (DruhCinnosti v _DRUH_ABSENCE: 10,20,21,22,23,26,30,31,33,34,35,36,39,47,50,51,133)
  - patri jen do dochazky/mezd (att_entry), ne do rozpadu na zakazky
- radky **bez cinnosti** (DruhCinnosti = 0)

Presne tyto absence delaly tech ~6 000 h. Pri porovnani je nutne je odecist i na strane
Centraly, jinak porovnavas jablka s hruskami.

## Cervenec a srpen porovnavat nelze

Dochazka v Centrale byla vypnuta vsem (430/430) a prenos od 31. 7. nebezi. Centrala uz
nesbira, takze mame vic my - a je to spravne.

## Dedup celeho dne (skutecne omezeni, ale jinde)

sync_vyroba_work_ec preskoci CELY den cloveka, kdyz ma ten den ve vyroba_work aspon jeden
radek ze source_system=app s vyplnenou cinnosti. K 4. 8. je takto blokovanych 775 osobodnu -
ale VSECHNY az od cervna (cerven 75, cervenec 608, srpen 92). Leden-kveten: nula.
Na shodu za prvni pololeti tedy nema vliv.

