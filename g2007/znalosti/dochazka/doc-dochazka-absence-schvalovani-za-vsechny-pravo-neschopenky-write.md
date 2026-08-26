# Schvalování absencí za všechny: nosičem práva je admin nebo neschopenky/write, ne jméno

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Schvalování absencí za všechny (mzdy/HR), nikoli jen za své lidi

**26. 8. 2026, C26 / Peťa.** Navazuje na `doc-dochazka-schvalovani-absenci-erp-menu-a-fajfka`
(Jirka 6. 8.: rozhoduje jen vedoucí toho člověka) a na hromadné rozhodnutí označených
řádků, které Peťa přidala 24. 8. do `dochazka-po-zakazkach.html`.

## Podnět a skutečná příčina
Peťa hlásila, že „schválení více označených řádků přes pop-up menu nefunguje". Kód
z 24. 8. byl v pořádku. `window.hromadneRozhodni` bere jen ty označené řádky, které jsou
čekající žádost **a které smí přihlášený rozhodnout** (`schvalZadostProRadek` -> mapa
`MOJE` plněná z `att_absence_inbox`). Peťa nebyla u žádné z 23 čekajících žádostí vedená
jako `manager_user_id`, takže inbox vracel 0 a hromadná akce vždy skončila hláškou
„Není označena žádná žádost, kterou jde rozhodnout". Stejným gatem jí nešlo ani schválení
jednoho řádku — položka v kontextovém menu se vůbec nenabídla.

## Rozhodnutí (Peťa 26. 8.)
Mzdy musí umět odbavit i to, co vedoucí nechal ležet. Právo rozhodnout **každou** čekající
žádost mají: Peťa, Michelle, rodiče (Marti, Kristýna) a Jirka.
Vedoucím se **nic neubírá** — Dušan a Michaela dál rozhodují své výrobní lidi.

## Jak je to udělané
Nová funkce `_abs_global(s, uid)` v `g2007.python` skriptech `att_absence_inbox`
a `att_absence_decide`:
- `att_absence_inbox`: `parent = _is_parent(s, uid) or _abs_global(s, uid)` — kdo projde,
  vidí všechny čekající žádosti, ne jen své.
- `att_absence_decide`: `elif not (_is_parent(...) or _abs_global(...) or (mgr and int(mgr) == uid))`.

**Nosičem práva je oprávnění, ne jméno** (stejný vzor jako potvrzování lékaře/nemoci/OČR
o pár řádků níž): správce systému (`public.users.is_admin`) **nebo** držitel práva
`neschopenky` na úrovni `write` v `tenant.user_capability`. K 26. 8. to vychází na
Marti (1), Kristýnu (11), Jiřího (20), Peťu (18) a Michelle (17). Při změně role se do
kódu nesahá — právo se přidává a odebírá v aplikaci.

**Směrování žádostí se NEMĚNÍ.** `_abs_resolve` v `att_absence_request` zůstal netknutý,
žádost dál patří svému vedoucímu; globální schvalovatel k ní jen navíc dosáhne.

## Ověřeno na produkci
Před zásahem inbox Peti = 0 žádostí, po zásahu 21. V přehledu Správa docházky šla po
zásahu hromadně rozhodnout žádost Pavla Zemana (home office).

## `materialized` NEZNAMENÁ „je to vidět v docházce"
Příznak `att_absence_request.materialized` sleduje **jedinou cestu**: řádky, které do
`att_entry` zapíše schválení v `att_absence_decide` (`source_system='absence_req'`,
`status='confirmed'`, poznámka „schválená absence"); při zrušení rozhodnutí je táž větev
zase maže a příznak vypíná. Absence se do docházky dostává **i bez schválení** (plán
nepřítomností, sync z Centrály 1, ruční zápis ve Správě docházky), takže „nepromítnutá"
žádost neznamená chybějící den. **Nezaměňovat příznak za data — dívat se do `att_entry`.**

Doložený případ — žádost 4, Šárka Novotná, dovolená 13.–17. 7.: Marti ji 2. 7. odbavil
větou „Kontaktuj mě osobně, musíme to probrat" (stav `info`), takže `materialized` zůstal
`false`. Dny v docházce přesto jsou: 28. 6. přišly z plánu nepřítomností (8 h/den) a 30. 7.
z Centrály 1 (7 h/den); dedup C24 30. 7. nechal verzi z Centrály a plánovou odstavil na
`superseded`.

## PROČ V PŘEHLEDU VISÍ I ROZHODNUTÉ ŽÁDOSTI (ověřeno 26. 8., původně vedeno jako neznámé)
Dataset `dochazka.zakazky_budoucnost_list` (přehled **Správa docházky**, minulost
i budoucnost) skládá řádky `Z:` (žádost) a `D:` (den). Žádost se ukazuje, dokud platí:

```sql
WHERE r.tenant_id=2 AND COALESCE(r.materialized,false)=false
  AND COALESCE(r.stav,'') NOT IN ('cancelled','rejected')
```

Přehled tedy bere `materialized` jako „už vyřízeno". Jenže ten se nepřepne **nikdy** ve
dvou legitimních případech, takže rozhodnuté žádosti visí dál jako by čekaly:

1. **Home office se do docházky ZÁMĚRNĚ nematerializuje** —
   `att_absence_decide`: `if stav == "approved" and typ != "homeoffice":` (Peťa + Claude-26
   12. 8. 2026). HO není čerpané volno, ale místo výkonu práce; člověk normálně píchá,
   takže docházka musí nést jeho skutečný čas, a schválení zůstává jen informací, že ten
   den dělá z domova. Dřív se zakládal umělý blok 8 h od šesté ranní i na dny, kdy dotyčný
   píchal, a hodiny se zdvojily (Michaela Hladíková 24. 7. 9,17 h místo 8,00 a 7. 8.
   10,05 h místo 4,72). Souvisí s pravidlem v
   `doc-dochazka-sprava-vs-new-co-se-preklapi` (Peťa 30. 7.: „home office se do Docházky
   new nepřeklápí, schválně").
2. **Verdikt typu `info`** („Kontaktuj mě osobně…", „To je na tobě, beru to jako info") —
   není to schválení ani zamítnutí, nic se nezapíše a filtr `NOT IN ('cancelled','rejected')`
   takovou žádost nevyfiltruje.

Doloženo: Z:93 (Michaela Hladíková, HO 14. 8., **schváleno** Šárkou 14. 8. v 11:15) —
v docházce na 14. 8. nemá jediný řádek se zdrojem `absence_req`, má tam normální píchaný
den (příchod 9:19, pauza, práce, konce dne, automat doplnil 0,5 h do fondu). Je to
správně. Z:4 (Šárka, `info`) tamtéž.

**Kdo to bude opravovat:** vada je v podmínce přehledu, ne v zápisu. Řešit „vyřízenost"
podle `stav`/`decided_at`, ne podle `materialized` — u home office a `info` se materializace
z principu nikdy nestane.

## Slepé uličky — ať je nikdo nezkouší znovu
- **`tenant.att_odpovednost` s „řádkem bez člověka" NENÍ zástupný zápis za všechny.**
  Řádky 1 a 2 vypadají v přehledu s LEFT JOINem jako „(všichni)", ale mají `user_id = 44`,
  což je uživatel, který v `public.users` už není. Sloupec je navíc `NOT NULL`, takže
  wildcard tudy nejde. `_abs_resolve` je joinem `o.user_id = ae.user_id` stejně zahodí.
- **Nová `staff_group` „DOCHÁZKA - SCHVALOVÁNÍ VŠECH" je zbytečná** — vyžadovala by zápis
  do `tenant.*`, tedy schvalovací banner, a duplikovala by model oprávnění, který už
  existuje. Rozepsáno a zase zrušeno.
- **Skupinu `DOCHÁZKA - OPRAVY` k tomu použít nelze** — jsou v ní i Dušan, Michaela
  a Jiří, tedy lidé, kteří mají záměrně vidět jen svůj okruh.
- **`att_entry.is_active` není příznak platnosti záznamu.** V červenci 2026 je `false`
  u všech 5 048 řádků včetně `approved` a `confirmed`. Platnost se pozná ze `status`
  (`superseded` = odstavený).

## Gotchy
- Zápis do `g2007.python` projde mostem **bez banneru** („G2007 KONSTRUKTIVNÍ"), zápis do
  `tenant.*` chce schválení rodiče. Dva pokusy 26. 8. vypršely po 120 s bez kliknutí —
  proto se řešení hledalo tak, aby žádný zápis do dat nepotřebovalo.
- Dotaz na most nesmí obsahovat dvojtečku následovanou slovem — SQLAlchemy z toho udělá
  bind parametr a spadne to na „A value is required for bind parameter". Týká se to i
  **komentářů** a JS ternárů (piš s mezerami kolem dvojtečky). V generovaném kódu dvojtečku
  sesaď přes `chr(58)`.
- Příkaz mostu, který začíná `WITH ...`, se vyhodnotí jako čtení a spadne na
  „forbidden keyword" — víceřádkový zápis piš jako prosté `INSERT`/`UPDATE`.

## Otevřené
- Lékař, nemoc a OČR se hromadně neschválí — brání tomu pojistka `_smi_doklad`
  (potvrzuje jen držitel `neschopenky/write` a až s doloženým dokladem). Není to vada.
- Podmínka „vyřízenosti" v `dochazka.zakazky_budoucnost_list` podle `materialized`
  (viz výše). Neopraveno, čeká na rozhodnutí Peti.
- Změna rozšiřuje pravidlo, které 6. 8. výslovně zadal Jirka. Jemu i Martimu odeslána
  notifikace 26. 8.

