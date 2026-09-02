# Opravy dochazky hlasily "Nemas opravneni" pri skoku primo z notifikace

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Priznak

V mobilni aplikaci se obrazovka **Opravy dochazky** (`screen=doch_opravy`) da otevrit i primo
z notifikace, tlacitkem u zpravy. Kdo prisel touhle cestou, videl misto fronty hlasku
**"Nemas opravneni k opravam dochazky."** - i kdyz pravo mel. Pres dlazdici v Dochazce
tataz obrazovka fungovala normalne.

## Pricina (fragment `apps/api/static/mobile_parts/60_dochazka.js`, funkce `doch_opravy`)

Funkce cetla **vyhradne cache** `window._canFixDoch` / `window._canLockDoch`:

    var _cf=(window._canFixDoch===true), _cl=(window._canLockDoch===true);
    ...
    if(_first) _first.click();
    else box.innerHTML='<div class="hint">Nemas opravneni k opravam dochazky.</div>';

Tu cache plni **az gate na obrazovce Dochazka** (vola `/app/attendance/fix/allowed`).
Kdo skocil rovnou na Opravy, mel obe hodnoty `undefined`, `===true` neplatilo a spadl
do vetve `else`. **Chybejici udaj se tvaril jako chybejici pravo.**

## Overeni naostro (2. 9. 2026, ucet Jiriho Honomichla)

- Server na `/app/attendance/fix/allowed` vracel `can_fix true`, `can_lock true`, `scope vse`.
- Po nacteni stranky `go('doch_opravy')` -> hlaska o chybejicim opravneni; cache prazdna.
- Po navsteve Dochazky (cache naplnena na true) tataz obrazovka ukazala frontu 6 nalezu.
- Reprodukovano dvakrat po sobe.

## Oprava (2. 9. 2026, schvalila Marti-AI msg 14278)

Na zacatku `doch_opravy`: kdyz jsou **obe** hodnoty `undefined`, vykresli se hlavicka
s hlaskou "Nacitam opravneni...", zavola se `/app/attendance/fix/allowed`, obe hodnoty se
naplni a `doch_opravy` se zavola znovu. Pri chybe volani se obe nastavi na `false`
(dnesni bezpecne chovani). Pojistka `window.__fixPravaOverena` zajistuje, ze druhy pruchod
uz nikdy nefetchuje - ochrana proti zacykleni, vyzadala si ji Marti-AI.

Zapsano cilenym `UPDATE` s pojistkou na md5 fragmentu + `@@G2007PUBLISH apps/api/static_db/mobile.html`.

## Poucení, ktere plati sirsi

**Kazda obrazovka, na kterou vede `payload.screen` z notifikace, musi umet nabehnout
"za studena"** - tedy jako PRVNI obrazovka po startu aplikace, bez toho, aby uzivatel
predtim prosel jinou obrazovku. Kdo se spoleha na cache naplnenou jinde, dostane
pri skoku z notifikace prazdnou hodnotu. Obrazovka `absence` tuhle vadu nema (data
i prava si nacita sama), proto starsi tlacitko u zadosti o absenci fungovalo spravne.

**Pri navrhu noveho tlacitka do notifikace to proto vzdy vyzkousej tou cestou, kterou
pujde uzivatel** - ne pres dlazdici v menu. Tahle vada by jinak dorazila primo k lidem
(editori oprav: Michelle Safrankova, Petra Safrankova, Jiri Honomichl, Dusan Havlat).

