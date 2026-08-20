# Ramec FW - sest gotch pri stavbe edit jadra a vnoreneho gridu z SQL (C28, 11.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


Postaveno rucne pres SQL most (edit jadro nad tenant.org_post pro Dusanuv vyrobni grid). Kazda z techto veci stala cas, protoze se navenek projevi jinak, nez je pricina.

## 1. Nova fw.data_source bez status = active konci na HTTP 404
Runner (modules/erp/application/data_source_runner.py) hleda WHERE s.code = kod AND s.status = 'active'. Sloupec status nema pouzitelny default, pri INSERT bez nej zustane a endpoint /erp/data/{code} vrati 404 data_source_not_found. Navenek to vypada jako chybejici data_source nebo spatne prava.
Reseni - pri zakladani data_source vzdy explicitne status = 'active', nebo kopirovat z existujici radky.

## 2. fw.comp_def a fw.core maji created_by_text a updated_by_text jako NOT NULL
INSERT bez nich spadne na NotNullViolation. Zadny default. Vyplnuj jmeno instance.

## 3. fw.comp_def.root je smallint, ne boolean, a plati CHECK chk_comp_def_single_parent
Definice - ((root IS NOT NULL AND parent_comp_def_id IS NULL) OR (root IS NULL AND parent_comp_def_id IS NOT NULL)).
Tedy KORENOVA komponenta ma root vyplneny a zadneho rodice, POTOMEK musi mit root NULL. Hodnota 0 u potomka konstraint porusi.

## 4. Edit v gridu potrebuje samostatne edit JADRO, ne jen edit operaci
Polozka Oprava v kontextovem menu se rozsviti, jakmile na data_source existuje fw.data_source_op s operation_kind = 'edit'. Kdyz ale op.core_id ukazuje na core samotneho gridu, formular se otevre PRAZDNY s hlaskou panel main nema zadne fields.
Spravne - zalozit novy core (kind form) s komponentami form_root (typ 302), top_panel a client_panel (typ 13) a poli pod nimi, a teprve na nej nasmerovat op.core_id. Vzor ke zkopirovani - core 101 (act_def), comp_def 710 az 725.
Pole ma v layout.save objekt {table, column, schema, row_key {ID -> @id}, readonly, connection_id}.

## 5. Zaskrtavatko ve formulari - comp_type checkbox (id 3) se NEVYKRESLI
Formular ho zobrazi jako textove pole s popiskem (?checkbox) a zamkem. Funguje az checkbox_modern (id 107). V gridu se boolean vykresli jako zaskrtavatko sam od sebe, tam typ resit netreba.

## 6. Formular cte JEN skutecne sloupce cilove tabulky, pocitany sloupec do nej nedostanes
Pro PG cil dela loader SELECT * FROM schema.tabulka WHERE id = ..., tedy vlastni SQL edit data_setu se u PG NEPOUZIJE (u MSSQL ano - tam se data_set obali jako subquery). Pridani pocitaneho sloupce do edit data_setu se proto v poli neprojevi, pole zustane prazdne.
Reseni pro seznam navazanych zaznamu - VNORENY GRID. comp_def typu grid_modern jako potomek panelu, s vlastnim data_source a layoutem {"kind" -> "select-detail", "filter_field" -> "master_id", "data_source_code" -> kod, "height_px", "context_menu" -> ["refresh"]}. Data_source ma op s operation_kind = 'select-detail' a data_set s podminkou = master_id. Front-end vola GET /erp/data/{kod}?master_id=<id radku>&kind=select-detail. Vzor - core 203 ec.vyhodnoceni_jadro, comp_def 1332.

## 7. Bonus - resolver cilove tabulky bere PRVNI vyskyt FROM schema.tabulka
_resolve_entity_config_from_db extrahuje cil regexem z SQL. Kdyz je v SELECTu poddotaz, jehoz FROM je driv nez hlavni FROM, urci se spatna cilova tabulka a formular se nacte prazdny (bez chyby). Piste hlavni FROM jako prvni, poddotazy resit pres LEFT JOIN LATERAL az za nim.

