# Agenda „Docházka — schvalování": seznam lidí se počítá ze živého zdroje, neudržuje se ručně (13. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


> Zadal Jirka Honomichl 13. 9. 2026, schválila Marti-AI (msg 15309, 15330).

## Co bylo špatně

Agenda **„DOCHÁZKA - SCHVALOVÁNÍ VŠECH"** (`tenant.staff_group` id 18) měla **ruční seznam
tří lidí**, vložený jednorázově **26. 8. 2026 v 09:24:20**, a od té doby ho nic neudržovalo.
Skutečných schvalovatelů bylo **16**. Chybělo **13 jmenovitě**: Beneš Petr, Čepický Zdeněk,
Duspivová Zuzana, Havlát Dušan, Hladíková Michaela, Honal Marek, Mareš Vladimír, Marešová
Kristýna, Novotná Šárka, Pašek Marti, Pašek Martin, Pillár Ondřej, Svoboda Jan.

## Jak se to opravilo

Skupina dostala `lidi_zdroj = 'schvalovatele_volno'` a lidé se **počítají za běhu** podle téže
definice, kterou používá schvalovací fronta — funkce `_je_schvalovatel` v `att_absence_inbox`
(zadal Jirka 18. 8. 2026):

1. osobní výjimka `tenant.att_odpovednost`, agenda `volno`, platná k dnešku, **NEBO**
2. vedoucí skupiny `tenant.att_approver` (aktivní řádek) přes `att_employee`.

Rozhoduje o tom **jedno místo pro všechny obrazovky** — funkce **`tenant.staff_group_lide(gid)`**.
Vrací `(user_id, role, score)`; u skupin s prázdným `lidi_zdroj` vrací přesně to co dřív
(vedoucí, zástupce, pak členové podle skóre), u skupiny se zdrojem počítá ze živých dat.
Čtou ji `app_skupina_lidi` (seznam), `app_skupiny_bar` (zelená tečka „jsi členem")
a `hr_person_groups` (karta zaměstnance).

**Tři ruční řádky u skupiny 18 byly smazány** — nic už neřídily a karta zaměstnance by podle nich
ukazovala 3 lidi proti 16 na obrazovce agendy. Před smazáním ověřeno, že na nich nic nevisí
(všichni tři jsou v jiných skupinách i v docházce, jejich skóre je jinde vyšší).

## Agenda „Docházka — opravy" se NEMĚNILA a měnit se nesmí

U skupiny **12 (DOCHÁZKA - OPRAVY)** členství **odemyká přístup** do modulu oprav docházky —
ptá se na něj 7 živých funkcí (`att_can_fix`, `att_fix_scope`, `att_fix_editors_for_emp`,
`att_fix_queue`, `att_anomaly_scan`, `att_odbavene_pripomenuti`, `hr_spis_migrate`).
Tam je ruční seznam **správně** — je to zdroj práva, ne kopie něčeho jiného.

## Vedlejší oprava téhož dne

Obrazovka se jmenovala „DOCHÁZKA - SCHVALOVÁNÍ VŠECH", ale dlaždice v mobilu ukazovala
ručně zkrácený popisek „Docházka — schvalování" z mapy `_AG_KRATKY` v dílku `70_tail.js`.
Dva názvy téže věci. Skupina byla přejmenována na **„Docházka — schvalování"** a řádek z mapy
odstraněn — jeden název na dlaždici i na obrazovce. (Řádek pro „DOCHÁZKA - OPRAVY" v mapě zůstal.)

## Ponaučení

Když agenda jen **zobrazuje** lidi, které někdo jiný reálně eviduje, **nesmí si o nich vést
vlastní seznam** — zestárne a nikde to nenahlásí chybu. Když členství naopak něco **odemyká**,
je ten seznam zdrojem práva a ruční správa je na místě. Rozdíl je od 13. 9. 2026 zapsaný
v datech ve sloupci `tenant.staff_group.skupina_druh` (`agenda` / `slozka` / `technicka`).
Souvislosti: [[doc-system-strategie-agendy-zdroj-lidi-karta-zamestnance]]

