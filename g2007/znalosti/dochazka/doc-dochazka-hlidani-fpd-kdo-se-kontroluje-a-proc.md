# Hlídání FPD - co přehled ukazuje, podle čeho vybírá lidi a proč zrovna takhle

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Hlídání FPD — co přehled ukazuje, podle čeho vybírá lidi a proč zrovna takhle

**Peťa + Claude-26, 28. 8. 2026.** Nasazeno a ověřeno nezávislým přepočtem.

## Kde to žije
- data: `g2007.python` kód **`dochazka_kontrola_data`**, `report=fpd` (konstanty
  `_KONTROLA_FPD_SQL`, `_KONTROLA_COLS`, `_KONTROLA_TITLE`)
- stránka: `apps/api/static/dochazka-kontrola.html` (obyčejný soubor v gitu, ne v `g2007.soubor`)
- v ERP: Docházka → Kontrolní přehledy → **Nesplněný FPD**
  (`fw.menu_node` 206, `fw.core` 218 `dochazka.kontrola.fpd`; přejmenováno 28. 8. 2026
  z „Hlídání FPD (HPP)" na název jako v Centrále — rozhodla Peťa)

## Zdroje dat (ověřeno, NENÍ to ze starého)
- hodiny: `tenant.att_den_hodiny(2, od, do)` nad `tenant.att_entry` — tedy docházka
  ve STRATEGII, ne zrcadlo Centrály,
- úvazek: `tenant.engagement.uvazek_tyden_h` ve **verzi platné ke konci sledovaného období**
  (Jirkovo verzování z 19. 8. 2026), ne dnešní.

## Kdo se do přehledu dostane (stav po 28. 8. 2026)
1. druh smlouvy **HPP nebo OSVČ** — **DPP se nehlídá vůbec**,
2. **nemá zaškrtnuto „Bez docházky"** v kartě zaměstnance
   ([[doc-dochazka-priznak-bez-dochazky-v-podminkach]]) — nahradilo seznam devíti
   osobních čísel natvrdo, který tu byl od 4. 8. a obsahoval i Marešovou, která se
   kontrolovat MÁ,
3. **osobní číslo pod 9000** — devítková řada jsou externí OSVČ (programátoři, vedoucí
   zakázek), docházku nevedou. Rozhodla Peťa 28. 8.; nečíselná osobní čísla zůstávají,
4. **aktivní zaměstnanec a smlouva neskončila** — dřív se filtrovalo na „má nějaké
   hodiny", což schovávalo nejhorší případy,
5. není na **mateřské**,
6. schodek **větší než 0,5 h**.

**Pracovní dny se počítají jen za dobu, kdy člověk smlouvu měl** (od `smlouva_od` do
`smlouva_do`). Bez toho by nově nastoupivší (Dalecký od 27. 8.) vyšel jako díra 152 h.

## Dvě chyby, které se tím opravily
- **Filtr `(mzdove + absence) > 0` schovával lidi bez jediného záznamu.** Vojtěch Purkar
  (501, HPP, úvazek 40) neměl za srpen ani jeden záznam, chyběl mu celý měsíc — a v přehledu
  nebyl vůbec. **V Centrále má Kristýna tentýž řádek od 6. 11. 2023 zakomentovaný**
  s poznámkou *„aby to neukazovalo lidi, kteří nemají nic v docházce"*, tedy vědomě
  vypnutý. Zrušeno i u nás.
- **Práh tolerance byl 0,1 h, ačkoli popis přehledu i rozhodnutí Peti ze 4. 8. říkají 0,5 h.**
  Kvůli tomu svítila Duspivová se schodkem 0,14 h — přesně ten šum, který se zobrazovat
  neměl. Srovnáno na 0,5.

## Vzory v Centrále a proč se nedají opsat 1:1
| přehled | název | klíčová podmínka |
|---|---|---|
| **1088** | Docházka - Hlídání FPD HPP | `DruhSmlouvy = 2` + seznam čísel `not in (21,41,15,2,47,361)` |
| **5509** | Docházka - Hlídání FPD OSVČ | `DruhSmlouvy = 3` + **`NeplacenyPrescas > 0`** + `not in (9017,9030,9031,9103)` |

Peťa 28. 8. zrušila rozdělení na dvě záložky (filtruje se sloupcem Druh smlouvy).
**Podmínku `NeplacenyPrescas > 0` z 5509 ale převzít NELZE** — změřeno v obou databázích:
Erhard, Kilberger, Namjak a Voříšek, které hlídat CHCEME, mají nulu, kdežto externisté
Kubín, Mareš a Siřiště mají 0,50. Filtrovala by přesně naopak. Proto se externisté poznají
podle osobního čísla.

## Sloupce a vzhled
Sloupce jsou **přesně jako v Centrále 1088, bez ID, navíc Druh smlouvy**, v jejím pořadí:
Příjmení Jméno · Odpracováno · Počet · Hod denně · Má být odpracováno · Chybí odpracovat ·
Měsíc · Ke dni · Číslo · Skupina · Druh smlouvy.
**„Odpracováno" je stejně jako v Centrále už výsledné číslo** (odpracované + absence,
u kanceláře minus nad fond) — rozpad na Absenci / Dopíchnuto / Nad fond byl matoucí a byl zrušen.
Tabulka srovnána podle [[doc-system-strategie-prehledy-tabulky-standard]] — hlavně
**hlavička bez velkých písmen**, kterou standard výslovně zakazuje a která tu byla od začátku.

## Nezávislé ověření (28. 8. 2026)
Postavený druhý výpočet přímo z `att_entry`, bez `att_den_hodiny`, ke dni 27. 8.
**Deset lidí proti deseti, shoda v devíti.** Dva rozdíly, oba vysvětlené:
Duspivová (jen v přehledu — ten práh 0,1) a Michelle Šafránková (jen v kontrole —
je na **mateřské**, přehled ji vyřazuje správně). Tohle je použitelný postup, jak
přehled kdykoli přeměřit: kontrola musí vyřadit mateřskou, jinak hlásí falešný nález.

## Nález mimo přehled — předáno Šárce
**Kubín (9003), Mareš (9005) a Siřiště (9037) mají neplacený přesčas v Centrále 0,50
a ve STRATEGII 0.** U ostatních prověřených hodnoty sedí. Na tenhle přehled to vliv nemá,
ale je to podmínka ve smlouvě. Mail Šárce 28. 8. 2026.

## ⚠️ Pozor: ve STRATEGII jsou DVA přehledy „Nesplněný FPD" a počítají JINAK

| | náš | Jirkův (pro Dušana) |
|---|---|---|
| kde | 📋 Kontrolní přehledy | 🏭 Výroba |
| uzel / jádro | `menu_node` 206, `core` 218 | `menu_node` 197, `core` 209 `vyroba.dusan_nesplneny_fpd` |
| kdo vidí | restricted, 11 lidí | **private, jen Dušan (user 41)** |
| koho ukazuje | celá firma dle pravidel výše | jen Dušanovy podřízené (`vyroba_dusan_team`) |
| odpracováno | `att_den_hodiny` (+ placená absence) | `att_day_summary.cas_celkem` |
| má být | fond z **úvazku** × pracovní dny | z **plánu** (`att_plan_effective`, strop 8 h/den) |
| absence | **počítá se** jako odpracováno | **nepočítá se** — zůstává v „chybí" |

Jirkův vznikl 23. 7. 2026 na zadání Dušana Havláta (viz [[doc-vyroba-nesplneny-fpd]]),
náš 30. 7. 2026. **Nejsou to duplikáty a nemá smysl jeden mazat** — mají jiné publikum
i jiný vzorec. Ale **Dušan je v obou seznamech, takže jediný uvidí dvě stejně pojmenované
položky, kterým u téhož člověka vyjdou různá čísla.** Dotaz na Jirku odeslán 28. 8. 2026,
odpověď zatím není — až přijde, doplnit sem, jak se to rozhodlo.

