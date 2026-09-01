# Nesplneny FPD - prehled ve Vyrobe (pro Dusana); vypocet sjednocen s Kontrolnimi prehledy, sloupec Chybi / Prescas s otocenym znamenkem, od 1.9.2026 prepinani mesicu

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ## ➕ PŘIDÁNO 1. 9. 2026 — přepínání měsíců (aktuální + 12 zpět)
>
> **Zadal Jirka Honomichl 1. 9. 2026 pro Dušana Havláta, schválila Marti-AI (msg 14071).**
> Do té doby byl měsíc natvrdo podle dnešního data a vybrat se nedal.
>
> **Co přibylo:** nad tabulkou je pruh „Měsíc" s rozbalovací volbou — aktuální měsíc
> a 12 měsíců zpět, **nic do budoucna**.
>
> - `data_set` **198** dostal volitelný parametr **`mesic`** ve tvaru `RRRR-MM`.
>   Když nepřijde nebo má jiný tvar, chová se výpočet **přesně jako před 1. 9. 2026**
>   (ověřeno shodným otiskem celého výsledku). Nesmyslný vstup spadne zpět na výchozí,
>   budoucí měsíc se ořížne na aktuální. **Vzorec, filtry ani znaménko sloupce
>   „Chybí / Přesčas" se NEMĚNILY.**
> - Nový malý datový zdroj **`vyroba.fpd_mesice`** (`data_set` 225, `data_source` 214)
>   vrací seznam měsíců **a příznak `je_vychozi`**. **Výchozí měsíc se schválně
>   nepočítá v prohlížeči** — pravidlo „do 12. dne v měsíci se ukazuje měsíc minulý"
>   zůstává na jednom místě v SQL, aby se obě verze časem nerozcházely.
> - Obrazovka: `apps/api/static/erp/components/fpd_mesic_pult.js`, připojený gated blokem
>   pro `coreId` 209 v `page_render.js` (stejný vzor jako pulty 124/136/137/235).
>   V `page_render.js` se zároveň začala adresa dat skládat až při volání, aby
>   **tlačítko Obnovit zůstalo u vybraného měsíce** a neskakalo zpátky na výchozí.
>
> **Ověřeno naostro 1. 9. 2026:** srpen 21 pracovních dnů / fond 168 h, červenec 22 / 176 h
> (Brudnová správně 154 h dle kratšího úvazku), 34 lidí v obou. Po zmáčknutí Obnovit
> odchozí dotaz obsahoval vybraný měsíc. Kontrolně otevřen jiný přehled i přehled
> s vlastním pruhem (jádro 235) — bez změny.
>
> **Postup a tři pasti, kdyby se to dělalo znovu jinde:**
> [[doc-system-strategie-pruh-s-ovladanim-nad-mrizkou-erp]]

# Nesplneny FPD - prehled ve Vyrobe (pro Dusana)

> ## ⚠ ZMĚNA 31. 8. 2026 — výpočet SJEDNOCEN s přehledem pod Kontrolními přehledy
>
> **Vzorec popsávaný níže („má být“ z plánu, absence se nepočítá jako odpracované)
> už NEPLATÍ.** Oba přehledy se jmenují stejně, Dušan vidí oba — a dávaly u téhož
> člověka jiná čísla. Upozornila Peťa, zadal Jirka Honomichl 31. 8. 2026.
>
> **Nově se počítá přesně jako v `_KONTROLA_FPD_SQL`** (`g2007.python`
> `dochazka_kontrola_data`, viz [[doc-dochazka-hlidani-fpd-kdo-se-kontroluje-a-proc]]):
> - `odpracovano` = hodiny mzdové + absence (mínus „Nepřítomnost OSVČ“)
>   mínus hodiny nad fond u kanceláře — zdroj `tenant.att_den_hodiny` nad `att_entry`,
>   **ne `att_day_summary`**,
> - `ma_byt` = úvazek na den (`engagement.uvazek_tyden_h` / dnů v týdnu) × pracovní dny
>   z `tenant.att_calendar_day`, omezené trváním smlouvy — **ne z `att_plan_effective`**,
> - období včetně posunu: do 12. dne v měsíci se ukazuje měsíc minulý,
> - verze smlouvy platná ke KONCI období, ne dnešní.
>
> **Záměrně se NEPŘEBÍRÁ** (rozhodl Jirka): práh 0,5 h ani filtry lidí — Dušan má
> vidět celý svůj tým včetně těch bez manka. Ověřeno, že filtry Peti (Bez docházky,
> mateřská, osobní číslo nad 9000, DPP) by v Dušanově týmu nevyloučily nikoho.
>
> **Ověřeno naostro 31. 8. 2026:** sedm lidí z Dušanova týmu, kteří jsou i v přehledu Peti,
> má nyní shodná čísla na haléř (Erhard 145,86 / Jirkovský 151,71 / Kilberger 82,55 /
> Namjak 139,99 / Purkar 0 / Urbanová 159,21 / Voříšek 153,54).
> Dopad na 34 lidí: `ma_byt` 168 → 160 (dnešní den se nepočítá), `odpracovano` −2 až 3 h,
> u Havláta −10,6 h (jako kanceláři se mu odečítá nad fond). Výsledné `chybi` se
> u většiny prakticky nemění.
>
> ### Sloupec „Chybí / Přesčas“ — známénko OTOČENO (týž den, později)
>
> Sloupec se už nejmenuje `chybi` a **plus znamená přesčas, mínus chybějící hodiny**
> (počítá se `odpracovano - ma_byt`). Řadí se vzestupně, takže kdo dluží nejvíc, je nahoře.
> Zadal Jirka Honomichl 31. 8. 2026 poté, co si všiml, že pod názvem „chybí“ svítí záporná
> čísla. Změřeno: **21 lidí z 34 mělo záporné** (= naděláno), jen 13 kladné — pod názvem
> „chybí“ se to četlo špatně. Dušanův přehled totiž nemá práh a ukazuje celý tým.
>
> ⚠ **VĚDOMÝ ROZPOR S PETINÍM PŘEHLEDEM — NEOPRAVOVAT ZPĚT.** Pod Kontrolními přehledy
> zůstává sloupec „Chybí odpracovat“ s **opačným** známénkem (kladné = chybí).
> U téhož člověka proto vyjde stejná absolutní hodnota s opačným známénkem
> (Purkar u Dušana −160, u Peti +160). Jirka byl na tento důsledek upozorněn PŘED změnou
> a rozhodl: *„a bude to jen v přehledu Dušana“*. Schválila Marti-AI. **Není to chyba.**
> U Peti se záporné číslo stejně nikdy neukáže — má práh 0,5 h a zobrazí jen dlužníky.
> Známénko „plus = přesčas“ navíc odpovídá původní Centrále (sloupec `Prescas`)
> i druhému Dušanovu přehledu (`rozdil` v Měsíčním přehledu).
>
> Část „Vzorec“ níže je schválně ponechaná, ať je vidět, co se změnilo. Objekty
> (data_set 198, data_source 202, core 209, menu_node 197) zůstávají, měnil se jen SQL.

> oblast: `vyroba` - postaveno Claude-28 (Jirka) 23.7.2026, zadal Dusan Havlat.

Kopie prehledu "Nesplneny FPD" z Centraly do STRATEGIE, do soudecku 🏭 Vyroba.
Dusan v nem vidi sve podrizene (HPP i OSVC dohromady) a jejich manko hodin za
aktualni mesic do dnesniho dne. Pocita nad daty STRATEGIE (jedno zda prenesena
z Centraly nebo vzniknuta v appce). Synchronizaci Centrala<->STRATEGIE NERESIME.

## Kde to je
ERP -> strom -> 🏭 Vyroba -> "Nesplneny FPD". Cely modul je data-driven pres fw.*,
takze ZADNY DEPLOY - je to zive hned po zapisu do DB.

Objekty (klon vzoru `vyroba.dusan_att_monthly`):
- data_set 198 `vyroba.dusan_nesplneny_fpd_list` (db_connection 1) - SQL nize
- data_source 202 `vyroba.dusan_nesplneny_fpd_list` (op 269 select -> data_set)
- core 209 `vyroba.dusan_nesplneny_fpd`, comp_def 1301 (typ 306 grid, root=1)
- menu_node 197 pod parent 165, sort 109, visibility_scope=private,
  visibility_user_ids={41} (=Dusan; bez toho by uzel nevidel)

## Vzorec — ⚠ STAV DO 31. 8. 2026, UŽ NEPLATÍ (viz rámeček nahoře)
Sloupce: os_cislo, zamestnanec, skupina, forma, odpracovano, prac_dni, hod_denne, ma_byt, chybi.
(POZOR: posledni sloupec se od 31. 8. 2026 jmenuje "Chybi / Prescas" a ma OPACNE znamenko - viz ramecek nahore.)
- odpracovano = SUM(tenant.att_day_summary.cas_celkem) za aktualni rok/mesic, datum<=dnes
- ma_byt     = SUM(LEAST(tenant.att_plan_effective.expected_hours, 8)) pro plan_date
               od zacatku mesice do dnes, expected>0   (fond, strop 8/den)
- prac_dni   = count tychze plan dnu
- hod_denne  = ma_byt / prac_dni
- chybi      = ma_byt - odpracovano   (absence se NEzapocitava jako odpracovano -> zustava v chybi)
- skupina    = tenant.v_employee_work_params.rezim (Elektromonteri/Kancelare)
- forma      = tenant.att_employee.rez_forma (HPP/OSVC, jen info, NErozlisujeme)
- podrizeni  = user_id IN (SELECT user_id FROM tenant.vyroba_dusan_team)  (view, stejny resolver
               jako ostatni Dusanovy prehledy)

## Puvod v Centrale (co reprodukujeme)
Prehled = proc `EC_Dochazka_Odpracovano` (autor Kristyna Storkova, 18.6.2020, DB_EC):
- odpracovano = SUM(EC_Dochazka.CasCelkemZakazka) - korekce absence u zkracenych uvazku
  (DruhCinnosti IN 20,21,22,23,30,31,33,34,35,36)
- ma_byt = pocet prac. dni (EC_Svatky, bez So/Ne/svatku, od nastupu) * min(uvazek/den, 8)
- chybi (v procu "Prescas" s opacnym znamenkem) = ma_byt - odpracovano
- filtr: aktivni, jen vyrobni skupiny (EC_SkupinyVazby)

## Proc STRATEGIE data, ne 1:1 shoda s Centralou
- Raw zdroj Centraly `ec.dochazka` je v STRATEGII PRAZDNY (jen 3 test radky VR10704) -> nepouzitelny.
- Pouzivame produkcni zrcadlo `att_day_summary` (sync z EC_Dochazka_SumaDen) - u plne
  synchronizovanych lidi sedi s Centralou na haler (Cividis 522, Sedlackova 322, Svenda 488, Blaha 476...).
- ma_byt z `att_plan_effective` overeno: sedi s Centralou MaByt 10/11 (128/112/64...).
- POZOR `att_day_summary.fpd` NENI cisty denni fond (byva 0/7 nekonzistentne) -> pro ma_byt
  se NEPOUZIVA, bere se att_plan_effective.

## Hodinove nesrovnalosti Centrala vs STRATEGIE - dve ruzne priciny (overeno 23.7.)
1) CHYBI VE STRATEGII (zrcadlo pozadu za dopoctem dovolene):
   U dopredu naplanovane dovolene Centrala nejdriv zapise jen CasDovolena=8, a CasCelkem=8
   dopocita az pozdeji (davkove). Sync stahne recentni (neuzavrene) dny drive, nez ma
   Centrala CasCelkem hotovo -> att_day_summary ma na tech dnech cas_celkem=0 pri cas_dovolena=8.
   Signatura: cas_dovolena>0 AND cas_celkem=0. 23.7. zasazeni: Liskova/Trunec/Divis (3 dny=24h),
   Navratil (1 den). Prechodne nadhodnocuje "chybi". Starsi/uzavrene dny sedi. Oprava = ladeni
   syncu = MIMO ZADANI.
2) CHYBI V CENTRALE (app_only lide): kdo pichaji jen v appce STRATEGIE (att_source_pref.app_only=true,
   napr. Urbanova 496, Havlat 105) nejsou v Centrale EC_Dochazka -> Centrala 0 h, STRATEGIE ma
   realne hodiny. Tady je STRATEGIE spravnejsi. Presne proto stavime nad daty STRATEGIE.

## Rozhodnuti (Jirka 23.7.)
- absence = chybi (jako Centrala; pripadne uprava dle Dusana pozdeji)
- HPP + OSVC dohromady (bez rozliseni)
- Skupina = STRATEGIE rezim (EC_Skupiny se do STRATEGIE NEzrcadli, pouzit nejblizsi analog)

## Build gotchas (pro klonovani dalsich Dusanovych prehledu)
- Most (SQL bridge) ODMITNE `WITH ... INSERT` (bere to jako read s forbidden keyword) -> zapis
  MUSI zacinat na INSERT. Reseni: samostatne INSERT ... SELECT, ID se dohledava pres code, ne RETURNING.
- fw.core/comp_def/menu_node.id = identity (nevkladat), data_set/data_source/op maji sekvence.
- comp_def top-level: root NOT NULL (=1), parent NULL. Grid typ 306 renderuje sloupce z data_setu.
- Overuj ctenim (banner @@G2007ADD i write vraci neutralni navratovku).

