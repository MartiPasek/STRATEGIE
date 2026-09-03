# Překryv časů na dni blokuje zezelenání i odbavení z fronty (Peťa 3.9.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Překryv časů na dni blokuje zezelenání i odbavení z fronty

> oblast: `dochazka` · zadala Peťa 3. 9. 2026, nasadil Claude-26

## Co se stalo
Peťa opravovala v ERP „Správa docházky — opravy" pauzu, kterou nahlásil sám člověk
(Andrea Bernardová 2. 9. 2026 — práce 6.50-15.01 a uvnitř přestávka 12.10-12.22).
Server po uložení vrátil oranžové varování *„Záznam je uložený, ALE časy se překrývají"*,
ale karta ve frontě přesto **zezelenala jako „opraveno"** a Peťa ji odklikla
**„Vyřídit bez opravy"**. Den tím zmizel z fronty, přestože byl dál rozbitý.
Všimla si toho jen proto, že jí zůstal otevřený vpravo v detailu.
Peťa: *„je potřeba, aby když je tam překryv, to nezezelenalo vlevo v tom přehledu
a nešlo to vyhodit z fronty."* Rozhodla se pro TVRDÝ zákaz, bez možnosti přebít.

## Sourozenec staršího nálezu
Je to přesně tentýž vzor jako 18. 8. 2026 se zapomenutým odchodem
(půlnoční automat uzavřel směnu na 23.59 a karta svítila zeleně) — tehdy platilo
Peťovo *„opraveno znamená SROVNÁNO, ne někdo se toho dotkl"*. Překryv je druhý
případ téhož pravidla; obojí teď žije ve stejném výrazu.

## Co je nasazeno (3. 9. 2026, bez deploye, vše přes most)
- **`att_fix_queue` v9** — nová funkce `_sql_prekryv(emp, den)` skládá EXISTS nad
  dvojicemi `tenant.att_entry` téhož dne. Používá se **dvakrát**: (1) přidána jako
  `AND NOT <překryv>` do výrazu `opraveno` (u anomálií i u rozporů), takže den
  s překryvem nezezelená a nedostane tlačítko „Hotovo — z fronty"; (2) jako **nový
  vracený příznak `prekryv`** v obou seznamech.
- **`att_fix_resolve` v3** — táž funkce jako pojistka na serveru. Odbavení anomálie
  (`anomaly_id`) i rozporu dne (`uid`+`day`) se odmítne hláškou
  *„Na tomhle dni se pořád překrývají časy — srovnej je a teprve pak jde den odbavit
  z fronty."* Nejde to obejít ani přímým voláním endpointu.
- **`apps/api/static_db/dochazka-opravy.html` v72** — `markPrekryv()` dá kartě místo
  zeleného štítku oranžový **⚠ časy se překrývají**, `blokPrekryv()` zašedí a vypne
  tlačítko („Vyřídit bez opravy" u rozporů, „V pořádku — vyřídit" u nesrovnalostí)
  s vysvětlením v title. Publikováno přes `@@G2007PUBLISH`, ověřeno na živé stránce.

## Definice překryvu — JEDNA, na třech místech stejná
Úseky téhož člověka a dne, obojí s časem od i do, `status` mimo `superseded`/`announced`,
`entry_type.code <> 'day_end'`, kategorie `presence`/`break`/`travel`, porovnání
`date_trunc('minute', …)` a **ostře** (konec jednoho = začátek druhého NENÍ překryv).
Shoduje se s `att_fix_overlap` (hláška po uložení) i s žlutou hláškou v detailu dne
v `dochazka-opravy.html`. **Když se bude měnit, musí se změnit na všech místech.**

## Gotcha, kvůli které to nehlásí plané poplachy
Půlnoční `day_end` (u Bernardové 15.01-23.59, kategorie `break`) by jinak kolidoval
s čímkoli odpoledním — proto je z porovnání vyhozený přes `code <> 'day_end'`.

## Následek, se kterým se počítá
Den s překryvem ve frontě **zůstane, dokud se fakt nesrovná**. To je záměr, ne chyba.
Bernardovou 2. 9. jsem 3. 9. vrátila do fronty (`tenant.att_day_confirm` id 2361,
`disputed=true`, důvod zapsán do poznámky dne), protože byla odbavena omylem.

## Odloženo (Peťa 3. 9. 2026)
Peťa chtěla navázat automatikou: vložená přestávka by pracovní záznam **sama rozdělila**
(6.50-12.10 + 12.22-15.01), vzorem podle `att_apply_work_selection` z 20. 8. Dohodnuté
pojistky: dělí JEN přestávka (ne cesta), JEN když leží celá uvnitř jednoho záznamu,
platí při přidání i při opravě, součet hodin dne se nemění (8.18 - 0.20 = 7.98 před
i po), rozpad `vyroba_work` křížící pauzu se rozdělí a druhá část přepojí na nový
záznam. Peťa: *„tohle raději uděláme až později, až všechno ostatní bude funkční."*
Konzultace odeslána Marti-AI přes `@@MARTIAI` 3. 9. — až se to bude stavět, vzít
její odpověď v potaz.

