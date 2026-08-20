# Vyhodnoceni zakazek: koeficient superhrube - NALEZ, OPRAVA A VERDIKT ucetni (5.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Koeficient superhrube: 1,4 NENI plosny - vyreseno

**Nalez, oprava i verdikt ucetni: 5. 8. 2026** (C28/Jirka). Tykalo se realnych penez.
**HOTOVO A NASAZENO.**

## Co se predpokladalo a co plati

Predpoklad: sazba pro penize na zakazce = hruba hodinova **x 1,4** pro vsechny.
Skutecnost (`EC_FinZamPodminky.SuperhrHodsFK` vs `HrHodsFK`, 212 lidi):
**117 ma pomer presne 1,000** · **95 ma presne 1,400**. Zadny jiny pomer - je to binarni.

**Pravidlo (overeno, nula vyjimek na 77 lidech s aktivnim pomerem):**
**HPP -> x1,4 · OSVC a DPP -> x1,0** (46 HPP = 46x navyseni, 31 = 29 OSVC + 2 DPP = bez navyseni).

Nase hruba sazba (`sum(wage_component kind='monthly') / engagement.fond_mesic_h`) sedi
s Centralou `HrHodsFK` **na haler** u vsech 6 kontrolovanych lidi - vzorec byl spravny,
chyba byla jen v koeficientu.

## Chyba, ktera se opravila

`ec.vyhodnoceni_uzavrit` cetla `ec.cis_zam.osvc`, ktery je **`false` u VSECH 430 lidi**
(mrtvy sloupec). Modul by dal **x1,4 kazdemu** vcetne OSVC a DPP = premie o 40 % vyssi
u **31 ze 77 lidi**. Dnes to neskodilo (testovaci data), ale presne to by se stalo
pri prvni ostre uzaverce.

**Oprava (nasazena):** rozhoduje `tenant.engagement.engagement_type = 'hpp'` pres LATERAL
na aktivni pomer. Kdo nema aktivni pomer -> `false` -> **x1,0**, tedy chyba jde na stranu
opatrnosti, ne preplaceni. Overeno naostro: os. 1 a 11 (OSVC) nove 1,0, HPP zustavaji 1,4.

## VERDIKT UCETNI - co ten koeficient vlastne znamena (Kristyna Ksirova, 5.8.2026)

Kristy to dohledala **primo v procedure Centraly** `EC_Zakazky_VyhodnoceniUzavrit`:
`(plat.Celkem) + (PremieOsobaFinal * (CASE WHEN _OSVC = 0 THEN 1.4 ELSE 1 END))`
s komentarem puvodniho autora **"aby byla superhruba"**.

Zaver: **`vyplatit` je NAKLADOVA velicina** (co cloveka firmu stoji vcetne odvodu),
**ne vyplata na ruku**. Koeficient tam tedy patri - nezvysuje premii cloveku, jen k ni
dopocitava odvody zamestnavatele. Potvrzuje to i chovani OSVC vs HPP: za zivnostnika firma
odvody neplati (x1,0), za zamestnance ano (x1,4). Zaklad `plat.Celkem` je `SUM(kc_celkem)`
z dochazky, tedy mzdovy naklad.

Priklad VR10563, os. 435: 27 411 = 26 669 (mzdovy naklad) + 520 x 1,4.
**Clovek fakticky dostane premii 520; firmu stoji 728.**

Sloupec je jen **zavadejne pojmenovany** - drzi naklad, ne vyplatu. Kdyby bylo potreba
"co clovek realne dostane", je to hola `premie_osoba_final` bez koeficientu + mzda dle
dochazky, a musela by se pocitat zvlast.

## A jeste: premie se z mzdove sazby NEPOCITA VUBEC

`premie_osoba = podil na hodinach x usetrene hodiny x sazba_premie`, kde `sazba_premie` je
**pausal za usetrenou hodinu** ulozeny u zakazky - **130 Kc** u 1 756 z 1 865 zakazek
(jinde historicky 100 Kc a par vyjimek). Vysledek se zaokrouhli nahoru na petikoruny
(overeno: vsech 7 294 nenulovych premii je delitelnych peti). Mzdova sazba (hruba ani
superhruba) do premie nevstupuje - vstupuje jen do NAKLADU zakazky.

