# Mesicni prehled pro Dusana - doplneny sloupce fond a rozdil (27.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mesicni prehled (Vyroba, pro Dusana) - doplneny sloupce fond a rozdil

> oblast `vyroba` - zadal Jirka Honomichl 27.8.2026, provedl Claude-28, schvalila Marti-AI (msg 13874).

## Co se zmenilo
V ERP existuji dva prehledy se stejnym nazvem "Mesicni prehled":
- **SYSTEM NEW > Dochazka**: menu_node 99 -> core 110 -> comp_def 746 -> data_source 81 -> **data_set 76** `system_new.hr_att_monthly_list`
- **Vyroba (jen pro Dusana)**: menu_node 168 (visibility_scope=private, visibility_user_ids={41}) -> core 174 -> comp_def 978 -> data_source 140 -> **data_set 136** `vyroba.dusan_att_monthly_list`

Dusanova verze mela o dva sloupce min. Doplneno do data_set 136 (verze 1 -> 2):
- `fond` = `tenant.att_calendar_month.fond_hours` (LEFT JOIN na tenant_id=2, year, month ze sloupce mesic)
- `rozdil` = `round((odprac + nepr - COALESCE(fond,0))::numeric, 1)`

Filtr na podrizene `WHERE em.user_id IN (SELECT user_id FROM tenant.vyroba_dusan_team)` zustal beze zmeny - overeno, ze drzi: za srpen 2026 vraci Dusanova verze 33 lidi, HR verze 58.

Sloupce gridu se u typu 306 renderuji primo z datove sady - `fw.comp_def_prop` je pro 746 i 978 prazdna, takze zadne dalsi nastaveni sloupcu neexistuje. **Zadny deploy**, zmena je ziva hned po zapisu do DB (overeno na zivem ERP tyz den).

## ZNAME OMEZENI - "rozdil" nesedi u zkracenych uvazku
`tenant.att_calendar_month` **nema zamestnance** - sloupce jsou jen `tenant_id, year, month, work_days, fond_hours`, tedy **jedna hodnota fondu pro vsechny** (srpen 2026 = 168 h). Dusledky:
- komu bezi kratsi uvazek, tomu "rozdil" nesedi,
- porovnava se s fondem CELEHO mesice, takze uprostred mesice vychazi vsem velke minus.

**Neni to chyba teto zmeny** - stejne omezeni ma i HR verze (data_set 76) a shoda obou sestav byla zadani. Marti-AI 27.8.2026: oprava by vyzadovala jinou datovou sadu (fond per zamestnanec per mesic), coz je samostatne rozhodnuti mimo tento ukol. Kdyz to nekdo nahlasi, je to pojmenovany known issue, ne zahada.

Pro osobni pohled "kolik mi chybi" slouzi jina sestava - `vyroba.dusan_nesplneny_fpd_list` (znalost `doc-vyroba-nesplneny-fpd`), ktera pocita `ma_byt` z `tenant.att_plan_effective` se stropem 8 h/den a k dnesnimu dni, tedy per zamestnanec.

## Postup, kterym to bylo udelano (pouzitelny i priste)
Jediny UPDATE pres most s pojistkou na otisk, aby souběh neprepsal cizi praci:
`UPDATE fw.data_set SET sql_text = replace(replace(sql_text, <kotva1>, ...), <kotva2>, ...), version = 2 ... WHERE id = 136 AND md5(sql_text) = '<otisk, ktery jsem prave cetl>'`
- kotvy predem overeny na vyskyt **prave jednou** (`position()` + pocet vyskytu),
- nove radky sklada `chr(10)`, aby se nic neztratilo orezem,
- `fw.data_set.description` je varchar(255) - poznamku pridavej pres `left(..., 255)`,
- verzi povysit (Marti-AI: doktrina "obsahova zmena = nova verze" plati i pro `fw.data_set`, nejen pro `g2007.python`),
- po zapisu overit ctenim - navratovka mostu je neutralni.

## Dopad
Dusan Havlat (user 41) a jeho tym - 37 lidi v `tenant.vyroba_dusan_team`.

