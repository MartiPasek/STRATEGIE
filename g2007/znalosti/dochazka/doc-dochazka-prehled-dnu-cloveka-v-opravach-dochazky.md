# Prehled dnu cloveka v Opravach dochazky (obdoba 2060 Centraly) - postaveno jako datovy zdroj, 27. 8. 2026

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)



# Prehled dnu cloveka v Opravach dochazky

**Zadal Jirka Honomichl 27. 8. 2026** (nastroj pro Dusana Havlata, vedouciho vyroby).
Mapovani a postup schvalila Marti-AI (msg 13871, 13886, 13892, 13901).
**Overeno naostro v prohlizeci tehoz dne. Zadna data z Centraly se nepouzivaji.**

## Co to je

V ERP obrazovce "Sprava dochazky - opravy" (`/dochazka-opravy`) ma zalozka **"Najit cloveka"**
po vyberu cloveka vlevo vpravo **tabulku jeho dnu** - obdobu prehledu **2060 "Dochazka - cely den
small"** ze stare Centraly, ale nad daty STRATEGIE. **Dvojklik na radek rozbali POD nim editaci
dne** (tentyz obsah jako zalozka "Najit cloveka v den ..."); klik na jiny radek predchozi sbali.

Zalozka "Najit cloveka" byla zaroven **rozdelena na dve**: puvodni s vyberem dne se prejmenovala
na **"Najit cloveka v den ..."**, nova **"Najit cloveka"** je bez vyberu dne.

## Klicove rozhodnuti: datovy zdroj, ne Python funkce

Prvni pokus sel cestou nove funkce v `g2007.python` + nove spojky v `router.py`.
**Jirka spravne namitl, ze se to dela jinak nez zbytek ERP** - a mel pravdu:
**170 datovych zdroju v `fw.data_source` se cte pres obecnou adresu `/api/v1/erp/data/{code}`,
zadny Python se nepise.** Funkce i spojka byly zruseny.

Vysledek: **`fw.data_source` + `fw.data_set` kod `dochazka.prehled_dnu_clovek`** (ciste SQL v DB).
Parametry `user_id`, `od`, `do`; `uid` doplnuje jadro automaticky.

## Zmena jadra: datove zdroje ted vedi, KDO se pta

Do 27. 8. 2026 nemel zadny ze 170 zdroju jak filtrovat na prihlaseneho - prava se resila jen
clenstvim v ERP nebo pevnym filtrem v SQL (napr. `tenant.vyroba_dusan_team`).
V endpointu `GET /data/{code}` (`router.py`) se nove nastavuje `raw_params["uid"] = uid`,
**az PO nacteni query params** (jinak by slo uid podvrhnout z URL). Commit `d8e54ec0`.
Stavajici zdroje se nerozbily: `_normalize_params` doplnuje chybejici bind params na None
a k 27. 8. zadny z nich `uid` nepouzival (mereno nad vsemi `fw.data_set.sql_text`).

## Prava: jedna sdilena definice v DB

Vznikly dve funkce, aby logika prav nezila ve dvou kopiich (bod 14 / Marti-AI:
*"dve definice prav nejsou technicky dluh, jsou to bezpecnostni incident cekajici na prilezitost"*):

- **`tenant.att_fix_emp_dle_scope(p_scope)`** - strom `staff_group` (VYROBA / KANCELARE / EXTERNI)
- **`tenant.att_fix_viditelni_emp(p_uid)`** - z uid odvodi editorstvi + pusobnost + `fix_all`,
  pak vola prvni funkci

`g2007.python` **`att_fix_scope_emps` byl prepojen** na `att_fix_emp_dle_scope` - vlastni kopii
stromu uz nema. Pred prepojenim overena **identicka mnozina**: Dusan 34 = 34 (rozdil 0 v obou
smerech), Michaela 34 = 34, kancelar 194, kdo neni editor 0.

**Overeno jmenovite:** Dusan (vyroba) NEvidi Petru Safrankovou (kancelar); Peta a Michelle maji
`fix_all` a vidi vsech 237 karet; kdo neni editor, nevidi nikoho vcetne sebe.

## Odchylky od predlohy 2060 (vedome)

| co | Centrala | u nas |
|---|---|---|
| `SeznamCinnosti` | sloupec mrtvy (vypocet zakomentovan) | **vynechan uplne** (rozhodl Jirka) |
| obdobi | natvrdo posledni 3 mesice | filtr od-do + jediny den, default 1. 1. az dnes |
| obraceny rozsah | - | `LEAST`/`GREATEST` ho prohodi (drive prazdno = vypadalo jako "nema data") |
| `CasCelkem` | `sum(CasCelkemZakazka)` | `tenant.att_den_hodiny` (sdilena definice hodin dne) |
| `IDKontroly`, `JmenoBrigadnika` | natvrdo -2 a prazdne | ponechano stejne (brigadnici u nas nejsou) |

## PASTI OVERENE V DATECH (nemenit bez noveho mereni)

1. **`att_entry.is_active` NEZNAMENA "platny zaznam", ale "prave bezi".** Z 832 radku Dusana
   Havlata ma `is_active=true` JEDINY (dnesni bezici). Filtr na nej by prehled **vyprazdnil**.
   Spravne rozliseni je **`status <> 'superseded'`**.
2. **ODCHOD se nesmi brat jako `max(ended_at)` pres vsechny zaznamy.** Zaznam typu `day_end`
   ("Dnes uz se mnou nepocitej") ma konec ve **23:59**, takze odchod vychazel 23.59 u vetsiny dnu.
   Overeno na Dusanovi 26. 8.: skutecny odchod **15:05**, `day_end` 15:05-23:59.
   `day_end` se z vypoctu prichodu i odchodu **vylucuje** - obdoba toho, jak Centrala vylucuje
   `DruhCinnosti 27` (Odmeny fin.zakazek).
3. **Zdrojem dnu je `att_day_summary`, ne `att_entry`** - u Dusana pokryva 172 dnu proti 167
   v zaznamech a NEEXISTUJE den, ktery by byl jen v zaznamech (5 dnu navic = doplneni do fondu).

## Zadna data z Centraly (overeno na vsech clancich retezu)

- datovy zdroj bezi na `fw.db_connection` **id 1 = `strategie_pg`** (PostgreSQL `data_db`,
  10.200.188.12); Centrala je id 2 (`DB_EC`, 192.168.30.11) - tam se nesaha
- vsech **8 tabulek je lokalnich** (`pg_class.relkind <> 'f'`), zadna cizi tabulka pres FDW
- obe DB funkce i `att_den_hodiny` nemaji `dblink`, `mssql`, IP Centraly, `DB_EC` ani `EC_*`
- obrazovka se pta jen na **17 nasich adres**, v jejim kodu neni `DB_EC`, `EC_Dochazka`,
  `TabCisZam`, IP Centraly ani `db=mssql`

Z Centraly pochazi **jen predloha** (ktere sloupce a jak se pocita odchod), zadna data -
v souladu s rozhodnutim Jirky z 25. 8. 2026 "Z Centraly se neprenaseji zadna data".

## Razeni sloupcu a hromadny soucet hodin (doplneno 27. 8. 2026)

Pozadavek Dusana Havlata, zadal Jirka, schvalila Marti-AI (msg po 13911).

**Razeni:** klik na hlavicku kterehokoli sloupce radi vzestupne, druhy klik sestupne, sipka ukazuje
smer. Radi se **nad uz nactenymi radky v prohlizeci**, ne novym dotazem do DB (max 1000 radku).
Typy: cisla cislem, **datum podle skryteho `_datum`** (podle zobrazeneho `DD.MM.YYYY` by se radilo
jako text a poradi by bylo spatne), zbytek `localeCompare('cs')`. Prazdne hodnoty vzdy na konec.

**Vyber vic radku jako v Centrale:** klik = jen tento radek, Ctrl+klik = prepnout, Shift+klik = rozsah.
**Kolize s dvojklikem vyresena BEZ `setTimeout`:** klik bez modifikatoru vyber **NASTAVUJE**
(ne prepina), takze dvojklik (= dva kliky + dblclick) skonci v deterministickem stavu a teprve
pak otevre den. Marti-AI to schvalila jako lepsi nez zpozdeni 250 ms, ktere je pri kazdem kliknuti citit.

**Prave tlacitko -> "Soucet hodin"** otevre okno se souctem vybranych dnu:
vybrano dnu / z toho odpracovano / z toho absence / prumer na den / celkem.
V menu je i "Zrusit oznaceni"; okno zavira tlacitko, klik vedle i Escape.

Pro rozpad pribyly do zdroje dva **skryte sloupce `_odprac` a `_absence`** (z `tenant.att_den_hodiny`).
Sloupce s podtrzitkem se v tabulce nezobrazuji - stejna konvence jako `_datum`, `_user_id`, `_uzavreno`.
Overeno, ze `_odprac + _absence = CasCelkem` u vsech radku.

**Overeno naostro 27. 8. 2026** (Tomas Blaha, 174 dnu): cas vzestupne 0,00 -> sestupne 10,13/9,95/9,77;
datum chronologicky 2. 1. -> 3. 1. -> 5. 1.; vyber klik 1 / Ctrl 2 / Shift 5 / klik zase 1;
soucet 5 dnu = 40,23 h a **rucni kontrolni soucet primo z tabulky dal tez 40,23**.

### PAST pri stavbe tabulky v teto obrazovce

Pomocna funkce `el()` stavi prvek pres `innerHTML` na `<div>`, takze **samostatne `<thead>`, `<tr>`
a `<td>` prohlizec ZAHODI** - `el('<thead>')` vraci `null`, `el('<tr>')` hodi vyjimku.
Tabulka se proto musi slozit **jako jeden retezec** a hotova `<tr>` teprve dohledat pres
`querySelectorAll`; rozbaleny radek se vklada pres `document.createElement`. Overeno v prohlizeci.

## Souvisi

- `doc-dochazka-prehled-cely-den-vv-centrala-rozbor` - rozbor predlohy 2060
- `doc-dochazka-jeden-vypocet-hodin-za-den` - `tenant.att_den_hodiny`
- `doc-dochazka-strom-skupin` - strom pusobnosti
- `doc-system-strategie-fw-data-set-sql-validace-po-zapisu` - povinne overeni po zapisu SQL

