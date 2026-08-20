# Prevod priplatku a odmen z Centraly: prevodnik druhu se cte z ciselniku, ne z konstanty v kodu

> oblast: `mzdy` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Problem (nahlasila Peta 6.8.2026)
Odmeny, priplatky a srazky zadane v Centrale se neprenasely do STRATEGIE. Za 7/2026 jich bylo
v Centrale 80 radku, u nas 8. Akce `sync_priplatky` (hodinovy job `fw.mirror_job`) mela
`TYP_MAP` **natvrdo v kodu** (`_sync_priplatky_from_ec` v `router.py`, radek 42321) a pokryvala
**14 z 49 typu Centraly**. Co v mape nebylo, se **TISE zahodilo** do citace `skipped` -
nikde se to neobjevilo a nikdo se to nedozvedel.

Nejvic palilo **EC typ 50 "Odmeny z financi zakazek"** (zalozeno v Centrale az 4.8.2026,
autor Kristy) - **47 radku / 18 lidi / 11 870 Kc za 7/2026**. Drive tyhle premie chodily do mzdy
starou dochazkovou cestou (`mzdy_finance_zakazek_rows` nad `tenant.att_finance_zakazek`), ta je
ale od 7/2026 prazdna a **5.8. ji Peta vedome vypnula** v `mzdy_generuj` (radek ~232,
`pass  # prows = ... mzdy_finance_zakazek_rows`), aby se premie nezdvojily.

## Reseni (6.8.2026, C28/Jirka, schvalila Marti-AI msg 12356 body A-D)
1. **Datova oprava** - `tenant.wage_component_type` mela `ec_typ_id` vyplnene u 49 z 49 typu
   Centraly, ale u `odmeny_finance_zakazek` (id 67) zustalo NULL, doplneno `ec_typ_id = 50`.
2. **Migrace + datovy prevodnik** - telo `_sync_priplatky_from_ec` presunuto do
   **`g2007.python` kod=`sync_priplatky_from_ec`** (kategorie `mzdy`), v `router.py` zustal
   tenky delegate (commit `6022e546`, -123/+12 radku). Prevodnik se ted cte z ciselniku
   (`SELECT ec_typ_id, id FROM tenant.wage_component_type WHERE ec_typ_id IS NOT NULL`),
   takze **novy druh v Centrale uz nepotrebuje deploy - staci radek v ciselniku**.
3. **Pojistka proti dvojimu zapocteni** - EC typy **1, 2, 3** (DPP do mzdove slozky 700) a
   **17** (Odmena Jednatel do 693) se ZAMERNE neprenaseji - na tyto lidi existuji aktivni
   radky v `tenant.mzdy_rucni_slozka` (693 - cisla 2, 47, 41; 700 - 374, 525) a Marti Pasek tuhle
   cestu **10.7.2026 vedome vypnul** (`mzdy_generuj` V1.04, "Herejtova 8000 misto 4000").
   Neni to tichy zahaz - vraci se duvod `blokovano_rucni_slozkou` + log WARNING s navodem
   (pozadavek Marti-AI). **Zapnout az PO deaktivaci rucnich slozek = rozhodnuti Petry a Martiho.**
4. **Viditelnost** - navratovka nese rozpad `zahozeno` = [{typ, duvod, pocet, castka, lidi}]
   plus klic **`_msg`**, ktery `_mirror_run_job` (`router.py`, radek 26226) preferuje pred generickym
   vypisem cisel, takze rozpad je videt ve `fw.mirror_job.last_result` (ridici pult), ne jen v logu.

## Overeny vysledek
Po nasazeni - `preneseno 818, zahozeno 26 | clovek nema aktivni pracovni pomer (byvaly
zamestnanec): 26 radku / 238 337 Kc, typy 4,9,32,37,38,40,44` (844 radku 2026 celkem).
Drive se zahazovalo 58 radku. Odmeny ze zakazek za 7/2026 - **47 radku / 18 lidi / 11 870 Kc**,
sedi na Centralu na korunu. Simulace vyberu `mzdy_priplatky_rows` za 7/2026 potvrdila, ze
**vsech 47 dojde do mzdy do slozky 651** (EC 9 radku/4 lidi/2 990 Kc + ES 38/14/8 880 Kc).
Riziko zdvojeni overeno - v `mzdy_rucni_slozka` neni ZADNA slozka 651.

## GOTCHY
- `fw.mirror_job.last_result` je **orezany na 400 znaku** - rozpad po typech se do nej nevesel
  a konec chybel. Proto se `_msg` seskupuje **po duvodech**, ne po typech (vejde se do ~133 znaku).
  Rozpad po typech zustava v navratovce (klic `zahozeno`) a v log WARNING radcich.
- `_mirror_run_job` scita VSECHNY ciselne hodnoty navratovky do `last_rows`, tedy 818+26 = 844.
- Zdrojak obsahuje nazev sloupce s diakritikou `d.[Preneseno]` (s hackem nad r). Pri zapisu pres
  most se diakritika prekoduje, proto je v kodu psany jako `"d.[P" + chr(345) + "eneseno]"`
  a cely skript je ciste ASCII. Zapis pres most delej **base64** (`convert_from(decode(...))`)
  a **vzdy over md5** - fronta u velkych payloadu tise ztraci mezery.

## ROZHODNUTO 11.8.2026 - odstupne se NEPRENASI (drive zde bylo "k rozhodnuti")
Vyhledani cloveka pozaduje `engagement.is_current = true`, takze radky **byvalych zamestnancu
propadnou** - vcetne **ODSTUPNEHO (EC typ 32)**, ktere z povahy veci dostava ten, kdo odchazi.

> **Rozhodl Jirka Honomichl, 11. 8. 2026 - odstupne se do STRATEGIE prenaset NEMA.**
> Soucasne chovani je tim padem **spravne, ne vada**. Podminka `engagement.is_current`
> zustava beze zmeny, do kodu se nesaha. Doporuceni Marti-AI z 29.7. (rozsirit o "posledni
> engagement, kdyz zadny neni current") se **nebude realizovat**.

Tech **26 radku / 238 337 Kc** (odstupne, telefony, obleceni, home office; EC typy
4,9,32,37,38,40,44) se bude **kazdou hodinu ukazovat v rozpadu** jako
`clovek nema aktivni pracovni pomer (byvaly zamestnanec)`. **Cte se to jako chyba,
ale je to zamer. NEOPRAVOVAT.** Detail v [[doc-mzdy-sync-priplatky-obdobi-z-platnosti-od]].

## Nesrovnalost k doptani u Petry (stale otevrene k 11.8.2026)
Peta psala 48 zapisu / 19 lidi / 12 870 Kc; v Centrale je 47 / 18 / 11 870 Kc (ID 19998-20044
souvisle, bez dir) a u nas presne totez. Rozdil = 1 radek / 1 000 Kc, ktery v Centrale neni.
Neopravovano naslepo.

## Navaznost
**11.8.2026 se nasla druha, hlubsi dira ve stejnem skriptu** - filtr `WHERE d.Rok = 2026`
zahazoval uz v SQL vsechny radky, kde Centrala Rok nevyplnuje (fakturacni podklady OSVC,
114 radku za 2026). Opraveno, viz [[doc-mzdy-sync-priplatky-obdobi-z-platnosti-od]].

