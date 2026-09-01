# Nález "prázdný den doplněný fondem" se vracel každou půlnoc — váže se nově na DEN, ne na id doplňovacího řádku (oprava 1. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Peťa + Claude‑26, 1. 9. 2026.** Peťa: *„už jsem to potvrzovala, ale něco to vrací
na červenou."* A k tomu, jak to má fungovat: *„dá se tam dopíchnutí do fondu, pak se mě to
zeptá, jestli je to ok, a když řeknu, že ano, je to tam a má to tam zůstat."*

## Co se dělo

Nález `prazdny_den_doplnen` („pracovní den bez docházky i bez absence — automat doplnil
do fondu X h") se **vracel každou půlnoc znovu**, i když ho člověk odbavil.

Doloženo na Petřině 7. 8. 2026 — **šest odbavených nálezů** (12. 8., 28. 8. 2×, 30. 8.,
31. 8., 1. 9.) a sedmý otevřený. Pokaždé nový, protože doplňovací řádek dostal nové id:

`10008256 → 10012627 → 10013100 → 10013729 → 10014086 → 10014445 → 10015128`

## Příčina

`att_automat_level_day` je **idempotentní**: při přepočtu okna své doplňovací řádky
**smaže a založí znovu** — s novým `id`. `att_prazdny_den_fond` pak zakládal nález
navázaný jen na to `id`, takže nový řádek = nový nález a včerejší odbavení se ho netýkalo.

Stejnou vadou trpěli lidé „bez docházky" (Marti 17×, Šík 13× od 13. 8.); u nich se to
28. 8. 2026 vyřešilo tím, že se jim nález **nezakládá vůbec** (příznak `pod_bez_dochazky`).
Tohle je řešení pro všechny ostatní.

## Oprava (nasazeno 1. 9. 2026)

V `att_prazdny_den_fond`:

1. Nález nově nese **den** (`tenant.att_anomaly.den`), ne jen odkaz na řádek.
2. Před založením se testuje, jestli pro toho člověka a ten den **už nějaký nález byl** —
   odbavený i otevřený. Když ano, přeskočí se **i zpráva na mobil**.
3. Test snese i staré nálezy bez vyplněného dne (`LEFT JOIN` na řádek, pokud ještě
   existuje), takže se odbavení nemuselo nikam zpětně doplňovat.

Ověřeno: `compile()` prošel, zdroj v DB bajtově shodný, a kontrolní dotaz na Petřině
7. 8. vrací 1 — tedy dnešní noc už nový nález nevznikne.

## Co to znamená v praxi

Doplnění do fondu **je** odpověď na prázdný den, ne chyba. Systém se zeptá jednou,
člověk odsouhlasí a tím to končí. Když se den později doplní doopravdy (docházka nebo
absence), automat si svůj řádek odebere sám při přepočtu.

## Souvislosti

- `doc-dochazka-priznak-bez-dochazky-v-podminkach` — výjimka pro lidi bez docházky (28. 8.)
- `doc-dochazka-att-day-summary-z-att-entry` — odkud se berou hodiny dne

