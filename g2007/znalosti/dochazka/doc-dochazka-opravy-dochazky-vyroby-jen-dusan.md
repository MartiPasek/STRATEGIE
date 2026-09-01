# Opravy docházky výroby chodí jen na Dušana Havláta — Michaela Hladíková vyřazena (1. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Opravy docházky výroby chodí jen na Dušana Havláta (od 1. 9. 2026)

**Zadala** Michaela Hladíková (domluvila se s Dušanem Havlátem) · **rozhodl** Jiří Honomichl 1. 9. 2026 · **provedl** Claude-28, write #2664 · **ověřeno čtením i přepočtem směrování.**

## Co se změnilo

Odebrán řádek `tenant.staff_group_member` id 138 (tenant 2, group 12 „DOCHÁZKA - OPRAVY", user 16 Michaela Hladíková; založen 10. 7. 2026 uživatelem 20).

Skupina má nově **4 členy**, každý s výslovnou působností:
Michelle Šafránková (17) `kancelar` · Petra Šafránková (18) `kancelar` · Jiří Honomichl (20) `vse` · **Dušan Havlát (41) `vyroba`**.

## ⚠️ Proč se NEsmazal řádek v `att_fix_scope`

Michaele **zůstal** řádek `tenant.att_fix_scope` user 16 = `vyroba` — **záměrně, jako pojistka**.

`att_fix_scope` (verze 2, active) má pravidlo **„editor bez řádku = 'vse' (bezpečný default pilotu)"**. Kdyby se řádek smazal a někdo Michaelu v budoucnu do skupiny 12 vrátil, dostala by působnost **VŠE** (výroba i kanceláře) místo původní `vyroba` — a nikdo by si toho nemusel všimnout. Nečinný řádek tomu brání: bez členství ve skupině ho žádné směrování ani přístup do modulu nečte (`att_can_fix` vyžaduje členství, `fix_all` má `false`).

**Stejná past platí obecně:** kdo vyřazuje editora oprav, ať **odebírá členství ve skupině**, ne řádek působnosti.

## Čeho všeho se to týká (jedno nastavení, sedm míst)

Působnost z `att_fix_scope` + členství ve skupině 12 čte `att_fix_editors_for_emp` (verze 2, active), a na ní visí:
`att_fix_request` (žádost o opravu) · `att_dispute_day` a `att_entry_dispute` (rozporování dne a záznamu) · `att_anomaly_scan` (nálezy v docházce) · `att_neomluvena_absence` · `att_can_fix` · `att_fix_scope`.
Jedna změna proto pokryla opravy, rozpory, anomálie i neomluvenou absenci naráz.

**Osobní výjimka `tenant.att_odpovednost` agenda `dochazka` má přednost před stromem** — k 1. 9. 2026 jsou všechny tři řádky té agendy `aktivni=false`, takže do toho nezasahují.

## Koho se to týká — jmenovitě

**34 aktivních lidí větve VÝROBA** (strom `staff_group`): Havlát, Sedláčková, Brudnová, Kasal, Pěchouček, Peřina, Svatoš, Lišková, Švenda, Hájek, Artim, Erhard, Lev, Trunec, Jakešová, Honal, Króner, Nosek, Porner, Valenta, M. Svoboda, Jirkovský, Egermaier, Kilberger, Voříšek, Čiviš, Urbanová, Bláha, Reitmaier, Vápeník, Namjak, Navrátil, Purkar, Diviš.

Po změně jim všem 34 vychází jako editor oprav **jen Dušan Havlát** (přepočteno dotazem, který uvnitř spouští `att_fix_editors_for_emp`).

**Kanceláří se to nedotklo** — 29 lidí větve KANCELÁŘE má dál Michelle + Petru Šafránkovou.

**Michaela ztrácí přístup do modulu Opravy docházky úplně** (jinou působnost neměla, rodič není). Za celou dobu ale **nevyřešila ani jeden nález** (`att_anomaly.resolved_by = 16` → 0 řádků), takže se tím nikomu neubrala rozdělaná práce.

## ⚠️ Vědomé riziko, které Jirka přijal

**Dušan zůstává na 34 lidí u oprav sám a nemá zástup.** Marek Honal (85) je veden jako jeho zástup **jen pro schvalování absencí** (`att_approver` group 1 „výroba", `je_zastupce=true`), u oprav ne. Když bude Dušan mimo, žádosti a nálezy počkají ve frontě a nikomu jinému nepřijdou — uživatelé s působností `vse` (Jirka) se podle kódu **záměrně nenotifikují**.

K 1. 9. 2026 je otevřeno **29 nálezů** u lidí z výroby (24 z posledních 30 dnů, nejstarší z 8. 6. 2026) — všechny teď leží na Dušanovi.

Rozhodnutí zástup zatím neřešit padlo vědomě (Jirka 1. 9. 2026). Až se bude řešit zastupitelnost nebo nový opravce, začni tady.

## Schvalování absencí se NEMĚNILO

Absence dílenských už **před** touto změnou chodily jen na Dušana — ověřeno funkcí `tenant.resolve_approvers(2, emp, CURRENT_DATE)` na všech 34 lidech: 33× Dušan Havlát (41), u Dušana samotného Marek Honal (85). Michaela nebyla schvalovatelkou ani jednoho z nich (v `att_odpovednost` agenda `volno` má jediný řádek — za Šárku Novotnou).

⚠️ Pozor při ověřování: **`resolve_approvers` vrací `user_id`, ne `employee_id`.** Párování na `att_employee.id` dá tiše úplně jiná jména (1. 9. 2026 tak vyšla „Kristýna Marešová" místo Dušana).

## Co zůstalo neopravené

Docstring `att_fix_scope` (verze 2) pořád uvádí jména: *„'vyroba' (Míša, Dušan)"*. Je to **v rozporu s pravidlem z `att_fix_all`** — *„KDO to právo má, se čte VÝHRADNĚ z dat, do komentáře se jména NEPÍŠOU"*. Neopraveno záměrně: změna kódu je nad rámec zadání a vyžaduje povýšení verze.

**Souvisí** [[doc-dochazka-vedouci-jediny-zpusob-a-fronta-oprav-rodice]] · [[doc-dochazka-strom-skupin]] · [[doc-dochazka-odpovednost-schvalovani-volna]] · [[doc-dochazka-schvalovatel-skupiny-projekty-martin-pasek]]

