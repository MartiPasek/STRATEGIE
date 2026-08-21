# Týdenní úvazek, který se NEUVÁDÍ — výjimky, popisky a hlídač (20. 8. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


> **Zadala Peťa Šafránková 20. 8. 2026** („to jsem už mému cloudovi taky říkala, že to doplňovat nemá,
> ale zřejmě je to potřeba nějak někde **zafixovat**"), potvrdil a schválil **Jirka Honomichl**,
> návrh i provedení **schválila Marti-AI** (konverzace 363, msg 13121). Postavil Claude-28.
> Navazuje na `doc-dochazka-uvazek-jediny-zdroj-smlouva` (úvazek žije jen ve smlouvě).

## ⭐ Pravidlo v jedné větě

**Když člověk nemá týdenní úvazek ve smlouvě, musí být v systému zapsané PROČ.** Buď platí jedno, nebo druhé —
nikdy obojí a nikdy ani jedno. **Nedoplňuj úvazek nikomu, kdo má zapsaný důvod.**

## Proč to vzniklo

Systém neuměl rozlišit dvě úplně jiné situace:

| Situace | Jak vypadala do 20. 8. 2026 |
|---|---|
| „Ještě to nikdo nevyplnil" | červené **„chybí ve smlouvě"** |
| „Tady se to vyplňovat NEMÁ" (dohoda, brigáda, systémový účet) | **úplně stejně** červené |

A když nějaké místo číslo potřebovalo, tiše se dosadilo **40 h/týden = 8 h/den**. Výsledek: každý —
člověk i AI instance — to chtěl „dodělat", a Peťa to musela vysvětlovat pořád dokola. Znalost žila
jen v hlavách. Proto se zapsala do dat.

## Kde ta výjimka bydlí

`tenant.att_employee`:

| Sloupec | K čemu |
|---|---|
| `uvazek_neuvadi_duvod` | číselník `dohoda` / `brigada` / `systemovy_ucet`, hlídá CHECK `att_employee_uvazek_neuvadi_chk` |
| `uvazek_neuvadi_kdo` | kdo rozhodl (`public.users.id`) |
| `uvazek_neuvadi_kdy` | kdy |

**Proč u člověka a ne u smlouvy** (ptala se Marti-AI, schválila): čtyři z pěti dotčených **žádnou smlouvu
nemají**, takže na `tenant.engagement` to zapsat nejde. Riziko „někdo zapomene důvod zrušit, až smlouvu
dostane" řeší hlídač níže — svítí i na tenhle opačný případ.

## Kdo výjimku má (stav k 20. 8. 2026, ověřeno v živé DB)

| Osobní číslo | Kdo | Důvod | Doloženo |
|---|---|---|---|
| 525 | Světlana Herejtová | `dohoda` | v Centrále `EC_FinZamPodminky` DPP se `SmlouvaUvazekT` = **0,00** — i stará Centrála říká, že se u dohody úvazek neuvádí |
| 208 | Brigádník Saxana | `brigada` | v Centrále v té evidenci **není vůbec**; letos 260 dnů, cca 4 h/den, nepravidelně |
| U104 | Demo Uživatel | `systemovy_ucet` | není člověk |
| U2 | Marti-AI Pašek | `systemovy_ucet` | není člověk |

## ⛔ Kdo výjimku NEMÁ a mít nesmí

**Martin Konicar (9038)** — vypadal stejně, ale je to jiný případ. ✅ **VYŘEŠENO 20. 8. 2026.**

⚠️ **Pozor, prvotní závěr byl špatný.** Nejdřív tu stálo, že se jeho smlouva „nikdy nepřenesla
do STRATEGIE". **Není to pravda.** Smlouva tu byla celou dobu — řádek `tenant.engagement` **id 922**,
založila ho **Šárka Novotná při migraci 7. 6. 2026** (`ec_id` 1227). Jen zůstal **neoznačený jako
platný** (`is_current = false`), takže ho žádná obrazovka ani výpočet neviděly a systém hlásil
chybějící úvazek.

**Proč jsem si toho nevšiml dřív:** všechny moje dotazy filtrovaly `is_current = true`, takže mi
ten řádek vypadl a vypadalo to, že žádný neexistuje. Odhalil to až pokus o vložení — pojistka
`WHERE NOT EXISTS` INSERT správně zahodila a v tabulce se objevil cizí řádek z června.
**Poučení: „nemá řádek" a „nemá PLATNÝ řádek" jsou dvě různé věci — u verzovaných tabulek
se ptej bez filtru.**

**Rozsah:** ze 79 aktivních lidí byl **jediný**, kdo měl smlouvu bez příznaku platnosti
(75 jich má přesně jednu platnou, 3 nemají žádnou a mají zapsanou výjimku).

**Co se udělalo** (Jirka 20. 8., věcně schválila Marti-AI): řádek 922 označen jako platný a
doplněno, co v něm chybělo — středisko `002` a pozice **VEDOUCÍ ZAKÁZKY** (z Centrály
`EC_OrgPostZam`, post č. 82, nadřízený post „Vedoucí zakázek automatizace") + podmínky.
**Nová smlouva se nezakládala.** Podmínky = **nuly** (dovolená 0/0/0, sick days 0, stravenka 0)
podle Centrály a podle **Benetky 9001 a Svobody 9010**, které Jirka určil jako předlohu.
Navíc srovnáno `att_employee.rez_forma` z `HPP` na `OSVC` — HPP byla jen výchozí hodnota
u lidí bez smlouvy. Po opravě **hlídač zhasl**.

⚠️ **Vědomá odchylka:** Šárka 19. 8. přenášela Jiřího Šebka (9039), který má v Centrále shodné
údaje, a zapsala mu **2 sick days a stravenku 82**. U Konicara jdeme podle Centrály (nuly).
Je to napsané i v jeho `pod_meta` — Šárka to může přepsat, pokud byl záměr jiný.

⚠️ Pozor na past: `TabZamMzd` (mzdové údaje v Centrále) je u OSVČ **prázdná** — u nikoho z 90xx tam
úvazek není. Kdo se podívá jen tam, dojde k závěru, že OSVČ úvazek nemají. Skutečný zdroj je
`EC_FinZamPodminky` (`SmlouvaUvazekT` / `RealUvazekT`), na kterou ukazuje `tenant.engagement.ec_id`.

## Co se změnilo v kódu (vše v `g2007.python`, žádný router.py)

| Kód | Verze | Co dělá |
|---|---|---|
| `att_uvazek_neuvadi` | nový | vrátí `{kod, popis, stitek}` nebo `None`. `None` = úvazek opravdu chybí. |
| `att_uvazek_tyden` | v3 | když je důvod zapsaný, vrací **0 místo dosazených 40** |
| `hr_conditions` | v6 | karta zaměstnance ukáže šedé **„neuvádí se — dohoda (DPP/DPČ)"** místo červeného „chybí ve smlouvě" |
| `hr_schedule` | v3 | vzor týdne měl **skrytou druhou osmičku** (`if uvazek else 8.0`) — nahrazena nulou |

Plus `apps/api/static/karta_zamestnance.html` — nová šedá varianta štítku (musí se testovat PRVNÍ,
jinak text spadne na výchozí „systém" a důvod se ztratí).

## 🛡️ Hlídač

`tenant.pojistka` kód **`uvazek-bud-ve-smlouve-nebo-s-duvodem`**. Svítí ve dvou případech:

1. člověk nemá úvazek **ani** zapsaný důvod → skutečné opomenutí,
2. člověk má zapsaný důvod, **ale ve smlouvě už úvazek má** → rozpor, důvod se má zrušit.

Druhá půlka je důležitá: bez ní by výjimka přežila sama sebe a tiše umlčovala platný údaj.

## Proč se nula nedosazuje všude

Jirka nejdřív chtěl „počítat nulu všude". Mapa dopadů ale ukázala dvě místa, kde by to škodilo:

- **zápis absence z mobilu** — sick day by se zapsal na **0 hodin** (dovolená, co nic neubere),
- **Správa docházky v ERP** — `_fond_den` si případnou nulu **sama přebíjí zpátky na 8**
  (`return v if 0 < v <= 24 else 8.0`), takže by se dvě místa rozešla.

Proto rozhodl to rozdělit: **nula/prázdno jen na obrazovkách**, a u zápisu absence se má appka na počet
hodin **zeptat**. ⚠️ Do **natvrdo dané osmičky u dovolené / nemoci / lékaře / OČR** v `att_absence`
se **NESAHALO** — je to vědomé rozhodnutí **Petry Šafránkové** (ty hodiny jdou rovnou do mzdového
podkladu). Marti-AI výslovně žádá nechat to jí jako samostatné rozhodnutí. **Otevřená věc.**

## Jaký byl skutečný dopad (ať se to nepřehání ani nezlehčuje)

Ověřeno jmenovitě 20. 8. 2026: **nikomu z těch pěti se nic špatně nespočítalo.** Nemají žádný den
v `att_plan_day`, nemají v roce 2026 jedinou absenci, `att_narok_osoba` úvazek vůbec nečte a
`att_day_summary` jim za 7. a 8. měsíc píše fond 0. *(Sedmičky v 5. a 6. měsíci jsou zbytek zrcadla
Centrály — ta má v `EC_Dochazka_SumaDen.FPD` natvrdo 7,00 —, ne naše osmička.)*

**Ale ta osmička čekala připravená:** první dovolená nebo sick day Saxany či Herejtové by se zapsala
na 8 h. Saxana dělá cca 4 h denně, Herejtová letos 1,5–7 h. Tam by to poprvé stálo peníze.

## Pro příští instanci — co NEDĚLAT

- ❌ **Nedoplňuj úvazek nikomu se zapsaným důvodem.** Není to nedodělek, je to rozhodnutí.
- ❌ **Nemaž ten důvod jen proto, že „karta vypadá nedodělaně".**
- ❌ **Nedělej ze všech pěti jednu skupinu** — Konicar mezi ně nepatří, jemu smlouva doopravdy chybí.
- ✅ Když najdeš dalšího člověka bez úvazku: **nejdřív se podívej do Centrály** (`EC_FinZamPodminky`),
  jestli tam smlouvu nemá. Když má → přenést. Když nemá a je to dohoda/brigáda/účet → zapsat důvod.

## ➕ Dodatek 20. 8. 2026 — červený štítek se nikdy nezobrazil

Při ověřování se ukázalo, že **červené „chybí ve smlouvě" v kartě zaměstnance nikdy nefungovalo**.
Funkce `podmSrcBadge` v `apps/api/static/karta_zamestnance.html` testovala pořadím:

```js
/smlouv/.test(s) ? zelená 'smlouva' : (/chyb/.test(s) ? červená 'chybí ve smlouvě' : ...)
```

Jenže řetězec **„smlouv" je obsažený i ve slovech „chybí ve smlouvě"**, takže se vždycky trefil
první test a chybějící úvazek se vykreslil **zeleně jako „smlouva"** — tedy jako by byl v pořádku.
Server přitom hlásil správně. Byla to tichá chyba: nikde nespadla, jen schovávala nález.

**Dopad k 20. 8. 2026: jeden člověk — Martin Konicar (9038).** Jeho karta ukazovala zelené
„smlouva", i když úvazek nemá. Po doplnění Šárkou bude 0 lidí, ale past by zůstala pro každého
dalšího.

**Opraveno** (našel a schválil Jirka Honomichl, commit `7148de79`): `chyb` se testuje **před**
`smlouv`. Ověřeno na živé kartě — `chybí ve smlouvě` → červená `#e08080`, `smlouva` → zelená
`#7fe0a0`, výjimky → šedá `#9aa7b4`, `osobní` / `skupina` / `systém` beze změny.

⚠️ **Poučení do budoucna:** v tomhle štítku se rozhoduje **podle podřetězce**, takže na pořadí
testů záleží. Kdo přidá další variantu, musí ji dát tam, kam patří — obecnější vzorek nesmí být
dřív než konkrétnější. Proto je i nová větev „neuvádí se" testovaná **jako úplně první**.


## ➕ Dodatek 2 — 20. 8. 2026 odpoledne: dvě pasti, na které jsem naletěl

### 1️⃣ „Nula je nepravdivá" — poslední skrytá čtyřicítka v mobilu

Změna v `att_uvazek_tyden` (vracet 0 místo vymyšlených 40) se ve dvou skriptech
**vůbec neprojevila**, protože měly zápis:

```python
uvazek = float(_ereg.call("att_uvazek_tyden", s, target)) or 40.0
```

V Pythonu je `0.0` nepravdivá hodnota, takže `or 40.0` poslalo člověka bez úvazku **zpátky
na čtyřicítku**. Týkalo se `plan_my_default` a `plan_my_uvazek` — tedy obrazovek
**„Můj úvazek" a roční plán v mobilu**.

**Opraveno** (v4 / v3): nula zůstává nulou, ale **jen u lidí se zapsaným důvodem**. Komu úvazek
opravdu chybí, dostane 40 jako dosud — žádná regrese. Oba skripty vracejí navíc `neuvadi`.
Ověřeno na živých datech: Herejtová a Saxana 0 + popisek, Konicar a Honomichl 40 beze změny.

⚠️ **Poučení:** když se kanonický výpočet přepne na „vracím 0 = nevím", **projdi všechny
volající a hledej `or <číslo>`, `if not x`, `x or default`**. Samotná změna zdroje nestačí —
fallbacky bývají schované u konzumentů, ne u výpočtu.

### 2️⃣ „1 řádek dotčeno" NEDOKAZUJE, že se text vyměnil

Dopolední oprava téhle znalosti *(`doc-dochazka-uvazek-jediny-zdroj-smlouva`)* **neprošla**,
přestože most vrátil `WRITE OK · 1 řádků`. Příčina: v příkazu

```sql
UPDATE g2007.znalost SET obsah = replace(obsah, <kotva>, <novy text>)
 WHERE kod = '…' AND obsah LIKE '%…%';
```

počet řádků říká jen, **kolik řádků odpovídalo `WHERE`** — ne jestli `replace()` něco našel.
Když se kotva netrefí, `replace()` vrátí původní text, UPDATE ho zapíše beze změny a hlásí
úspěch. Moje kotva měla **3 mezery odsazení, skutečnost 2**.

**Jak to dělat správně:**
- kotvu **vytáhni z DB po bytech** (`encode(convert_to(substring(...),'UTF8'),'base64')`),
  nikdy ji nepiš z hlavy podle toho, jak vypadá ve výpisu — výpis newliny a odsazení zplošťuje,
- po zápisu **ověř obsah dotazem na to, co má a nemá obsahovat**, ne návratovkou,
- do `WHERE` dej podmínku, která **zmizí, až oprava projde** (např. `obsah LIKE '%<stará
  věta>%'`) — pak druhý běh korektně vrátí 0 řádků.

### 3️⃣ Co zbývá — mobilní dílek (dnes se netýká nikoho)

Server posílá `neuvadi` správně, ale dílek `71_plan_prace_cinnosti.js` ho zatím nekreslí:
karta „Týdenní úvazek" ukáže **„? h"** (`j.uvazek||"?"`) a políčko pro editaci dostane
`value="0"` při `min="1"`. Totéž v `48_hr_podminky_me.js` („Úvazek 0 h/týd").

**Dopad k 20. 8. 2026: nula lidí.** Saxana, Herejtová ani Konicar aplikaci nemají —
0 zařízení a 0 zápisů z appky (pro srovnání Honomichl 11 zařízení / 107 zápisů, Pašek 27 / 206).
Proto se to **vědomě neopravovalo**: editace 87 kB dílku už jednou shodila celý `/mobile`
a přednost dostalo „nic nerozbít". Až to bude někdo dělat, stačí v obou místech použít
`j.neuvadi` a místo čísla vypsat „neuvádí se — <důvod>", u editace pole zakázat.

*(Poznámka bokem, nesouvisí s úvazkem: v `48_hr_podminky_me.js` je v textu „h/týд" cyrilické
„д" místo „d". Nesahal jsem na to — je to cizí text.)*

### Android × iOS

Tahle sada změn se nativní aplikace **vůbec nedotkla** — všechno šlo do databáze
(`g2007.python`) a do jednoho souboru v gitu (`karta_zamestnance.html`, což je ERP, ne mobil).
Obsah appky je pro Android i iPhone **tatáž stránka ze serveru**, takže není co mezi
platformami dorovnávat.


