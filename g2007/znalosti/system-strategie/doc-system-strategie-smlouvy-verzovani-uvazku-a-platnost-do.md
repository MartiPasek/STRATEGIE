# Smlouvy — verzování úvazku, dotaz před změnou a otevřená otázka „platnost do"

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


Zapsáno 23. 8. 2026 (Claude-28 / Jirka Honomichl). Vše níže je ověřeno čtením živého kódu
a dat, ne odhadem.

## 1) Přetypování podmínek rozbilo dva spouštěče (opraveno 22.–23. 8.)

Po přetypování sloupců `pod_*` v `tenant.engagement` (21. 8.) vracel číselník výchozích
podmínek pořád TEXT, takže:

- `tenant.engagement_pod_defaults()` padal na `COALESCE(time, text)` — DatatypeMismatch,
- `tenant.engagement_pod_soucet_dovolene()` padal na `pod_soucet_dovolene(numeric, numeric)
  does not exist` (pomocná funkce existuje jen ve variantě text).

**Následek: nešla založit ŽÁDNÁ nová verze smlouvy ani nový zaměstnanec.** Ověřeno, že od
21. 8. nevznikla ani jedna nová smlouva a nikoho jiného než Jirku to nezastihlo.

**Oprava.** Tři typové varianty číselníku — `tenant.pod_vychozi_cas` (čas),
`pod_vychozi_cislo` (číslo, čárka na tečku), `pod_vychozi_ano` (ANO/NE na ano-ne).
`engagement_pod_defaults()` je bere podle typu sloupce; `engagement_doplneni_pri_zarazeni()`
si typ přečte z `information_schema` a zapíše s přetypováním, takže ji další změna typu
nerozbije. Součet dovolené scítá přímo číselně; textová `pod_soucet_dovolene(text,text)`
zůstává pro spouštěč nad pohledem `staff_cond`.

**Test nasucho.** Celá cesta se dá ověřit blokem `DO`, který vloží kopii existující smlouvy
(projdou všechny spouštěče) a na konci ZÁMĚRNĚ vyhodí výjimku — transakce se vrátí a v datech
nezůstane nic. Doporučený postup u jakéhokoli dalšího zásahu do `engagement`.

## 2) Výběr skupiny podle čísla, ne podle textu (opraveno 23. 8.)

Oba spouštěče vybíraly skupinu člověka přes `MIN(sg.id::text)` — textově, takže skupina 10
předběhla skupinu 9. Nově `ORDER BY sg.id LIMIT 1`. Zadala Kristý, rozhodl Jirka.
Dnes nikoho nemění (42 lidí ve skupinách s výchozími hodnotami, nikdo není ve dvou naráz).

## 3) Změna úvazku se vždy ptá (22.–23. 8.)

Změna úvazku zakládá NOVOU VERZI smlouvy, proto se na ni musí vědomě kliknout. Otázku
formuluje **`uvazek_zapis`**, tedy jedno místo — všechny tři cesty (karta zaměstnance,
mzdová smlouva, plán práce) dostanou stejné znění:

„Změnou úvazku (40 h/týd → 39 h/týd) se založí NOVÝ ZÁZNAM podmínek, úvazku a smlouvy
s platností od 01.09.2026. Dosavadní záznam zůstane v historii. Chceš pokračovat?"

Do potvrzení skript jen ČTE, takže „Ne" nezanechá nic.

GOTCHA: skript přijímá `potvrzeno` jako desátý parametr, ale HTTP delegát
`/app/hr/conditions/save` ho zprvu nepředával — otázka se ptala pořád dokola a úvazek nešel
uložit. Při přidání parametru do skriptu v `g2007.python` VŽDY zkontroluj i delegáta
v `router.py`, ten předává argumenty POZIČNĚ.

Datum se zadává jako **„platí od" nové verze** (rozhodl Jirka 23. 8.), ne jako konec té
předchozí. Kdo zadá datum dřívější než začátek současné verze, dostane odmítnutí.

## 4) Změna poměru podřízena stejnému pravidlu (23. 8.)

`/app/hr/pomer-zmena` dosud zapisoval `uvazek_tyden_h` rovnou do platného řádku — bez otázky
a bez nové verze, tedy tichá ztráta historie pro mzdy. Nově se při skutečné změně úvazku
nejdřív zeptá, po potvrzení zapíše dobu trvání do platného řádku a úvazek nechá založit přes
`uvazek_zapis`. Pořadí je záměrné — nová verze pak nese i novou dobu trvání.

## 5) OTEVŘENO — sloupec `valid_to` („platnost do"). NESAHAT bez Jirky a Peti.

Stav k 23. 8. 2026: `valid_to` je prázdné u všech 939 řádků a v Centrále takový sloupec
NIKDY neexistoval (`EC_FinZamPodminky` má jen `PlatnostOd`).

Mapování ověřené na všech 935 spárovaných řádcích (`engagement.ec_id` = `EC_FinZamPodminky.ID`):
`valid_from` = `PlatnostOd` (931 shod), `smlouva_od` = `DatumSmlouvyOd` (935 shod),
`smlouva_do` = `DatumSmlouvyDo` (931), `zkusebni_do` = `ZkusebniDobaDo` (935).
POZOR na záměnu: `valid_from` NENÍ datum nástupu — proti `DatumSmlouvyOd` sedí jen 357krát.
Úvazek nemá ani jeden skutečný rozdíl (74 řádků se liší jen zápisem 0.00 vs prázdno).

`valid_to` čte OSM míst, všechna vzorcem „prázdné, nebo >= datum": att_anomaly_scan,
att_dovolena_kaskada, att_narok_cerpani, att_sd_kontrola, att_uvazek_tyden,
mzdy_benefity_apply, mzdy_loajalita_rows a mzdové náhrady v `router.py`.
Protože je vždy prázdné, podmínka nikdy nic neodfiltruje a každá stará verze platí
donekonečna. Sedm z osmi si vezme nejnovější verzi a jsou v pořádku; `att_uvazek_tyden`
si ale bere NEJVYŠŠÍ úvazek (schválně, kvůli souběžným poměrům), takže u dotazu „k datu"
vrací u 10 lidí vyšší číslo, než tehdy platilo (Marti Pašek 40 místo 20, Veverková 40/20,
Bernardová 40/32, Šik 40/30, Dvořáková 35/30, Brudnová 40/35, Novotná 40/35,
Duspivová 40/35 a dva lidé bez účtu). Otázky „jaký má úvazek teď" se to netýká.

PAST: ukončení poměru (`router.py`, uzávěrka poměrů) zapisuje `valid_to` a NENASTAVUJE
`is_current=false`. Vyplněné `valid_to` je tedy jediné, co ukončeného člověka z těch osmi
výpočtů vyřadí — kdo ho přestane zapisovat, rozbije ukončování lidí napříč docházkou i mzdami.

Varianty (rozhoduje Jirka, u druhé a třetí musí být Peťa kvůli mzdám): nechat být ·
vyplňovat jen nové změny · doplnit i 858 historických řádků. K 23. 8. 2026 Jirka rozhodl
NIC NEMĚNIT.

