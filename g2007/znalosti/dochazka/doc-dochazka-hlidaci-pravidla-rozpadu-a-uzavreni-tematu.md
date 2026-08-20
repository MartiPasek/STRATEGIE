# Hlídací pravidla rozpadu (chybi_zakazka, chybi_rozpad) a uzavření tématu docházka × rozpad (19. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Třetí a poslední díl.** Předchozí: `doc-dochazka-rozkol-hodiny-vs-casy-a-spousteni-kaskady`
(proč to nesedělo) a `doc-dochazka-backfill-rozpadu-kaskadou-a-prikaz-dochkaskada` (nástroj
a srovnání srpna). Tady je, co drží kvalitu do budoucna.

## Dvě nová pravidla ve frontě Oprav (`att_anomaly_scan`)

| Pravidlo | Co hlídá | Kdy zmizí |
|---|---|---|
| `chybi_zakazka` | položka rozpadu **existuje**, ale má prázdnou zakázku (nad 0,1 h) | jakmile kontrolor zakázku doplní |
| `chybi_rozpad` | k uzavřenému pracovnímu úseku **není žádná** položka — ani navázaná, ani překrývající se časem (nad 0,25 h) | jakmile k úseku rozpad vznikne |

Obě mají **vlastní úklid** (obecný úklid ve scanu zavírá jen nálezy, jejichž záznam přestal
platit, samotnou podmínku pravidla nepřepočítává). Obě berou posledních 14 dnů, nejdřív od
1. 8. 2026. **`chybi_rozpad` má výjimku na lidi, kteří se nekontrolují** — stejný seznam
`cislo_zam` jako kontrolní přehledy (Peťa 4. 8.), jinak by hlásilo obden Martiho.

**Rozdíl mezi nimi je podstatný.** Kaskáda si zakázku nikdy nevymyslí, takže dělá jen dvě věci:
buď založí řádek se zakázkou převzatou z píchnutí (a ta může být prázdná → R7), nebo nezaloží
nic (→ R8). Ani jedno neumí opravit stroj; obojí musí doplnit člověk v Opravách.

**Objem ověřený předem** (dopadová mapa před nasazením): R7 = 5 případů za 14 dnů u 3 lidí,
R8 = 2 případy za srpen. První běh R7 ve 14.48 našel přesně těch 5.

## Změna C — parazitní úsek se přebírá jen při návaznosti

`att_wa_open`: úsek kratší než 60 s se smaže a nový převezme jeho začátek **jen tehdy, když na
něj navazuje** (mezi jeho koncem a teď není mezera nad 60 s). Dřív stačila samotná délka, a po
pauze tak nový úsek převzal začátek PŘED pauzou a snědl ji (Jirkovský 11., 13. i 14. 8.,
Honomichl 12. 8. o 137 minut). **Podmínka délky MUSÍ zůstat** — bez ní by se při každém přepnutí
zakázky smazal i několikahodinový úsek. Hranice je `<= 60 s` kvůli ořezu na celé minuty.

Ověřeno v provozu: Kristý si vybrala zakázku a o minutu později činnost — vznikla **jedna**
položka od okamžiku výběru zakázky, ne dvě jako dopoledne.

## Sjednocení kopií (dokončeno)

`_wa_open` i `_wa_close_running` existují nově **jen jednou** — jako `att_wa_open` a
`att_wa_close_running` v `g2007.python`. `att_checkin`, `att_checkout` i `router.py` na ně mají
tenké delegáty. Do 19. 8. byly tři kopie a právě ta v `router.py` neměla ořez na celé minuty.
Důkaz, že to zabralo: od nasazení v 9.00 nevznikla **ani jedna** položka se sekundami
(78 nových položek), zatímco ráno jich sekundy mělo 408 z 1277.

## Dorovnání hodin za srpen (A3)

Hodiny přepočteny z uložených časů pro typy work/homeoffice/overhead, 1.–19. 8.:
**881 záznamů u 56 lidí, 2767,13 → 2756,76 h, tedy −10,37 h** za firmu. Na jeden záznam jde
o setinu až dvě setiny hodiny (cca půl minuty), nejvíc jeden člověk −0,69 h. Časy ani rozpad
se neměnily; `att_day_summary` se přepočítal triggerem. Ověřeno čtením: 0 zbývajících rozdílů.
Guard v zápisu hlídal, že se nesáhne do zamčeného období.

## Tři dořešené případy z kontrolního přehledu

- **Saad Jarrar 17. 8.** — ohlášená služební cesta 09.24–14.31 (5,12 h) neměla rozpad.
  Kristý rozhodla, že **služební cesta má mít rozpad na zakázku Rezie**; doplněno podle časů
  z píchnutí.
- **Dušan Havlát 17. 8.** — opravený úsek 06.05–11.28 (5,38 h) neměl rozpad; doplněna režie.
  Obecný jev: **oprava docházky posune nebo prodlouží úsek, ale rozpad se k němu nedoplní.**
  Nově to chytí pravidlo `chybi_rozpad`.
- **Jana Lišková 3. 8.** — jediný případ v celém období 1. 7. – 19. 8.: na úseku 05.55–07.48
  leží naše položka (`21495`, VR10674) i importovaná z Centrály (`21649`, Rezie, 0,94 h).
  Kaskáda `centrala1` řádky **záměrně needituje ani nevypíná**, takže duplicita přežije každý
  přepočet. Čeká na rozhodnutí Péti.

**Výsledek dne:** kontrolní přehled Docházka × rozpad hlásil ráno 7 dnů u 5 lidí, večer
**jeden řádek** (právě Lišková).

## Co zůstává otevřené

- Duplicita Lišková 3. 8. (Peťa) · naplánovaná týdenní kontrola má zastaralý dotaz (Peťa) ·
  doptání na zakázku při potvrzení příchodu z notifikace (Peťa, řeší příčinu u zdroje).
- 372 běžících položek ze staré Centrály — **rozhodnuto nechat být** (Kristý 19. 8.), jsou
  věrným zrcadlem rozdělaných řádků v Centrále a nesou nula hodin.
- Honomichl si sedmkrát v srpnu nepíchl odchod — téma na člověka, ne na kód.
- Známé meze: `@@DOCHKASKADA` nikdy nezakládá chybějící řádky (schválně) · 296 historických
  položek z 1.–18. 8. má v časech sekundy (kosmetika, součty nezkresluje) · `att_entry.hours`
  je `numeric(5,2)` proti 3 desetinným místům u položek, takže ±0,005 h na záznam zůstává
  strukturálně — nově ale náhodně na obě strany, ne systematicky nahoru.

