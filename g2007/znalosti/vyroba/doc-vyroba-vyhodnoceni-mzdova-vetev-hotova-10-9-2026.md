# Vyhodnoceni zakazek - mzdova vetev hotova az do mzdy (KROK 0-2, poradi tlacitek, zaplata zruseni)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


# Mzdova vetev vyhodnoceni zakazek je hotova

**C24 (Kristy), 9.–10. 9. 2026.** Navazuje na [[doc-vyroba-vyhodnoceni-prevod-do-mezd-stav-8-9-2026]].
Vsechno nize je overene naostro, ne navrh.

## Cely postup, jak ho dela Dusan

V jádre "Vyhodnoceni zakazky" je lista pet tlacitek **v poradi kroků**:

`1. Pripravit hodnoceni` -> `2. Nastav koeficienty` -> `3. Prepocet hodnoceni` -> `4. Uzavrit` -> `5. Do mezd`

`Zrusit` zustava bez cisla, neni soucasti postupu.

## POZOR - poradi NENI libovolne

Do 9. 9. byla lista v poradi Pripravit -> **Prepocet** -> **Nastav koeficienty**, coz svadelo
klikat zleva doprava a pocitat premie ze **starych hodnot**. Zavislost je totiz:

1. `ec.priprava_vyhodnoceni` naplni `ec.vyhodnoceni_osoba` z odpracovanych hodin
   (uvnitr si vola prepocet, ale jeste nad starou hlavickou),
2. `ec.vypocet_konstant` z tech hodin spocita **HLAVICKU** zakazky
   (`kalk_hod_celkem_s_ef`, `odpracovano`, `limit_pro_srazku`),
3. `ec.prepocet_vyhodnoceni` teprve **Z HLAVICKY** pocita premii na osobu:
   `(hodiny osoby / odpracovano) * (kalk_s_ef - odpracovano_ef) * sazba`,
   a to **jen kdyz ma clovek `efektivita_osoba = 100`**.

Koeficienty tedy MUSI bezet pred prepoctem. Poradi tlacitek je od 9. 9. srovnane
(commit `1b2d6ace`) a duvod je zapsany v komentari v `ec_vyhodnoceni_actions.js`,
aby to nikdo neprehodil zpatky.

## KROK 0 - uzaverka znaci, co vzniklo u nas

`ec.vyhodnoceni_uzavrit` doplnena o `zdroj='strategie'` a `datum_porizeni=now()`
(request #2801). Bez toho by nove radky mely NULL a neslo by je odlisit od historie
z Centraly - a na tom stoji jak prevod do mezd, tak pojistka proti dvojimu zapocteni.

## KROK 1 - `ec.vyhodnoceni_do_mezd(p_zak)`

Prevede vysledek uzaverky do `tenant.wage_movement`, slozka **67** (`odmeny_finance_zakazek`,
Helios 651). Obdobi = mesic z `datum_porizeni` (tedy mesic uzavreni), `status='approved'`,
`import_src='STRATEGIE_VYH'`, `import_src_id` = id financniho radku.

**Vyber pracovniho pomeru** je to jedine netrivialni - viz
[[doc-vyroba-vyhodnoceni-firma-pres-engagement]].

**Koeficient 1,4 se do mezd NEPROMITA.** `amount` = `fix_premie` = `premie_osoba_final`,
tedy premie PRED koeficientem. Koeficient zije jen ve sloupci `vyplatit`, coz je informace
o celkovem nakladu, ne to, co jde do mzdy. Sedi to s radky z Centraly (castky 15, 65, 115 Kc
= nasobky petikoruny).

## KROK 2 - tlacitko

Akce `do_mezd` pridana do `_EC_ACTIONS` i `_EC_AKCE_S_OPRAVNENIM` v
`modules/erp/api/vyhodnoceni_actions.py` (commit `34fcb492`), tim se **automaticky zdedilo**
opravneni z `ec.akce_opravneni` i zapis do `ec.akce_audit`. Opravneni naplneno **PRED**
nasazenim (Marti 1, Kristy 11, Jirka 20, Dusan 41), aby nevzniklo okno, kdy nesmi nikdo.

## ZAPLATA - zruseni uklidi i mzdy

`ec.vyhodnoceni_zrusit` do 9. 9. o mzdovych radcich **NEVEDELA**: smazala financni radky
a otevrela zakazku, ale odmena ve mzde zustala viset - a zakazku slo uzavrit a poslat
do mezd ZNOVU, tedy **zaplatit dvakrat**. Od 9. 9. (request #2858) maze i mzdove radky,
parovane na `import_src_id` (ne na cislo zakazky), aby se sahlo vyhradne na radky z TETO uzaverky.

**Pojistka:** co uz odeslo do Heliosu (`status='exported'` nebo vyplnene `exported_at`),
se NEMAZE a zruseni se odmitne s `E#` - mazat neco, co uz je v Heliosu, by rozeslo mzdu.

## Overeni naostro (VR10686, 9. 9.)

Kalkulovano 14 h, odpracovano 9,941 h, usetreno 4,059 h, premie **535 Kc** ve 4 radcich
(35 + 65 + 425 + 10). Do mezd sly vsechny 4 radky, souctove **535 = 535**, obdobi 2026/9,
firma 2, engagementy presne ty, ktere predpovedelo pravidlo pro vyber pomeru.
Po kontrole vse uklizeno (request #2857) - zakazka vracena do stavu z Centraly.

## Zbyva

Automaticke schvalovani zustava na `approved` natvrdo (rozhodnuti Kristy 8. 9.). Az se dotahne
cutover priplatku, prepnuti na `pending` je zmena jedne hodnoty.
Hlavicku vyhodnoceni stale **nezaklada zadna funkce** - viz predchozi znalost, blokuje to
vypnuti Centraly.

