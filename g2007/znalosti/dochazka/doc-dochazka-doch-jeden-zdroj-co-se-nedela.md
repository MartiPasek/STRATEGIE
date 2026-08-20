# Dochazka "jeden zdroj pravdy": co se ZAMERNE NEDELA (verdikt Marti-AI 27.7.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Dochazka - jeden zdroj pravdy: co je hotovo a co se ZAMERNE NEDELA

Zapsal C28 (Jirka) 27.7.2026 vecer. Vsechna cisla overena ctenim z produkcni DB v 18:50,
verdikty = Marti-AI msg 11360 na primy dotaz. Navazuje na
[doc-dochazka-bod1-att-entry-id-app-link], [doc-dochazka-bod2-att-entry-id-vyklad],
[doc-dochazka-doch-firma-id-backfill], [doc-dochazka-att-entry-user-id-denorm].

## Stav k 27.7.2026 18:50 (overeno, ne z pameti)
| Vec | Marti Pask 26.7. | Realita 27.7. |
|---|---|---|
| vyroba_work.att_entry_id | 1 / 13548 = 0 % | 13586 / 13646 = **99,6 %** |
| att_entry.user_id | chybi | 35503 / 35603 = **99,7 %** |
| vyroba_work.user_id | - | 13646 / 13646 = **100 %** |
| att_entry.firma_id | chybi | 35230 / 35603 = **99,0 %** |

Zbytkove NULLy uz NEJDE doplnit (clovek bez uctu, chybejici engagement). Kontrolni dotaz
"kolik jeste JDE doplnit" (stejne podminky jako self-completing fily): user_id 1
(dnesni radek, ceka na nejblizsi sync), firma_id 0, att_entry_id 0. Tj. backlog je nulovy,
ne "zaseknuty".

Doplnovani NENI jednorazovy backfill - self-completing fily bezi v
`_maybe_sync_ec_dochazka` (router.py ~28095), kazdy s VLASTNIM commitem + rollbackem
(driv byly v jednom commitu a 1 selhani shodilo vsechny).

## CO SE ZAMERNE NEDELA (verdikty Marti-AI, msg 11360)

### 1. firma_id do tenant.vyroba_work NEPRIDAVAT
Sloupec tam dnes vubec NENI (overeno v information_schema) a pridat se NEMA.
Marti-AI: "Nedavat. Odvozovat pres vazbu att_entry_id -> att_entry.firma_id."
Duvod: denormalizace = tentyz fakt na dvou mistech, princip jednoho zdroje pravdy plati
i na urovni SLOUPCE, ne jen tabulky. Kdyby byl JOIN prokazatelne pomaly, resenim je
index att_entry(id, firma_id), NE duplikace sloupce.
Marti Paskovo "doplnit firma_id (chybi)" = doplnit v att_entry, a to je hotovo (99 %).
POZOR: znalost [jeden-zdroj-pravdy] rika "firma_id chybi v OBOU" - to uz NEPLATI jako
ukol; do vyroba_work se nedoplnuje.

### 2. Q4 prestavba (vyroba_work jako projekce att_entry) NE DRIV NEZ ZARI
Marti-AI: "Pockat. Spokojit se s 99,6 % + self-completing."
Duvody: pocita se cervenec a blizi se mzdy; 1.8. je cutover priplatku a srazek do Prahy
a nesmi ho rozhodit paralelni prestavba; soucasny stav neni ideal, ale je STABILNI.
Bezpecny postup az prijde cas: vytvorit `vyroba_work_v` jako POHLED (work_alloc + att_entry)
VEDLE stavajici tabulky, nechat obe bezet paralelne, porovnavat per (user, den, hodiny);
teprve pri nulovem rozdilu 4 tydny -> prepnout prehledy na pohled -> az pak zvazit zruseni
tabulky. Zadna zkratka pres "rovnou nahradit" - mzdova data jsou prilis citliva.

### 3. Zobrazeni prehledu "Dochazka new" NEMENIT na link-based
Dedup vetve P (pritomnost z att_entry) zustava na urovni DNE. Dry-run link-based varianty
pridal 6705 radku pritomnosti = DVOJI POCET hodin do mezd. Viz [doc-dochazka-bod2-att-entry-id-vyklad].

### 4. Modul "Vyhodnoceni zakazek" byl pozastaveny do zakazka_meta
Marti-AI 27.7. potvrdila. **Vecer 27.7. zakazka_meta dostoji kompletni (banner #1480),
takze tenhle blok padl** - viz [doc-vyroba-zak-zakazka-meta].

## Odkud "Dochazka new" cte data (fw.data_set id=177, kod dochazka.zakazky_vse_list)
4 vetve UNION ALL: (1) vyroba_work source_system in ('app','centrala1') AND is_active;
(2) att_entry presence (work/overhead/homeoffice) JEN kdyz clovek ten den NEMA zadny
vyroba_work radek (nebo bezi smena bez konce); (3) att_entry absence -> zakazka "Rezie";
(4) att_day_summary leden-kveten 2026, jen kdyz neni vyroba_work.
Vychozi rozsah: aktualni + predchozi mesic, d <= CURRENT_DATE. Detail sloupcu:
[doc-dochazka-po-zakazkach-prehled].

