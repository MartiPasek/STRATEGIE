# Moje hodiny v mobilu - nuly dokud neni zdroj; tri definice odpracovano (dva prehledy zmeneny 31.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

> ## ⚠ AKTUALIZACE 31. 8. 2026 — dva ze tří přehledů v tabulce níž se ZMĚNILY
>
> Tabulka „tři různé definice“ níže popisuje **stav do 31. 8. 2026**. Ten den se dva z nich
> sjednotily s výpočtem Peti pod Kontrolními přehledy (zadal Jirka Honomichl, upozornila Peťa,
> schválila Marti-AI):
>
> - **`vyroba.dusan_nesplneny_fpd_list`** (data_set 198) — už nebere hodiny z `att_day_summary`
>   ani fond z `att_plan_effective`. Nově: hodiny z `att_den_hodiny` (mzdové + absence mínus
>   Nepřítomnost OSVČ, u kanceláře mínus nad fond), fond = úvazek na den × pracovní dny
>   z `att_calendar_day` omezené smlouvou. Sloupec se jmenuje **„Chybí / Přesčas“**
>   a má **opačné známénko** než u Peti (plus = přesčas) — vědomě, viz
>   [[doc-vyroba-nesplneny-fpd]].
> - **`system_new.hr_att_monthly_list`** (data_set 76) a **`vyroba.dusan_att_monthly_list`**
>   (data_set 136) — fond už **není** paušální `att_calendar_month.fond_hours` stejný pro všechny,
>   ale počítá se z úvazku každého člověka. Opravilo to čísla pěti lidem se zkráceným
>   úvazkem (u Veverkové zmizelo 84 h neexistujícího manka), viz
>   [[doc-vyroba-mesicni-prehled-dusan-fond-a-rozdil]].
>
> **Paušální fond `att_calendar_month.fond_hours` už nepoužívá žádný živý přehled** — ověřeno
> skenem `fw.data_set` + `g2007.python` + `g2007.soubor` týž den. Tabulka níž se schválně
> nemění, ať je vidět, co se změnilo.

## Co je v aplikaci

Na obrazovce **"Muj prehled"** (dilek `apps/api/static/mobile_parts/60_dochazka.js`, funkce
`muj_prehled`) je nahore karta **"Moje hodiny"**: nazev mesice + "k dnesku", velke cislo
`0 / 0 h fondu`, prazdny pruh splneni, radek "chybi 0 h do fondu" a pod tim vyrazne
oranzove upozorneni:

> "Pocitani hodin zatim nemame doresene, proto tu jsou nuly. Doplnime co nejdriv."

**Karta nic nepocita a nevola zadny endpoint.** Nuly jsou ZAMER, ne chyba nacitani ani
prazdna data. Kdo ji bude dodelavat, ma nahradit nuly skutecnym vypoctem a upozorneni
odstranit; do te doby se karta necha byt.

Dilek 22 -> 23 (238 824 -> 240 743 znaku, +1 919), slozena stranka `mobile.html` 72 -> 73,
overeno na zive `/mobile` (HTTP 200, delka sedi s DB, upozorneni 1x, pocet skriptovych bloku
beze zmeny) a spustenim samotneho bloku v Node s nahradou prohlizece.

## Proc nuly a ne cislo

Zadani Sarky Novotne za HR (cistopis 17. 8. 2026) chce, aby zamestnanec videl
"odpracovano vs. fond k dnesnimu dni". Sarka sama k tomu napsala, ze ma podezreni na
spatny vypocet a zada overeni proti Centrale drive, nez se cislo lidem ukaze.

**Overeno 27. 8. 2026 na zivych datech srpna - existuji TRI ruzne definice a kazda da
jine cislo:**

| kde | odpracovano | "ma byt" | k jakemu dni |
|---|---|---|---|
| `system_new.hr_att_monthly_list` (data_set 76, HR) | `att_den_hodiny.hodiny_mzdove` + zvlast `hodiny_absence` | `att_calendar_month.fond_hours` - **stejny pro vsechny (srpen 168 h)** | cely mesic |
| `vyroba.dusan_nesplneny_fpd_list` (data_set 198) | `att_day_summary.cas_celkem` (= odpracovane **i** absence) | `att_plan_effective.expected_hours`, strop 8 h/den | k dnesku |
| endpoint `GET /app/dochazka/moje-mesic` (router.py) | jen `hodiny_mzdove`, **absenci vubec nepocita** | prac. dny `att_calendar_day` x `engagement.uvazek_tyden_h / dny_v_tydnu` | k dnesku |

**Endpoint pro mobil je pro kohokoli s absenci spatne.** Doklad (srpen 2026 k 27. 8.):

| clovek | odpracoval | absence | endpoint by napsal | skutecnost |
|---|---|---|---|---|
| Michelle Safrankova (os. 381) | 0 h | 112 h | "chybi 144 h" | nechybi nic |
| Kristyna Maresova (os. 21) | 74,7 h | 88 h | "chybi 69,3 h" | 10,7 h **nad** planem |
| Petr Benes (os. 6) | 66,2 h | 80 h | "chybi 77,8 h" | chybi ~6 h |

## Na cem to stoji (otevrene)

1. **Zdroj musi potvrdit Peta Safrankova** (user 18), ktera za dochazku odpovida - rozhodl
   Jirka Honomichl 27. 8. 2026: dokud sama nerekne, ze vypocet odpracovanych hodin a FPD za
   konkretni mesic je nekde u ni vyreseny, zustavaji v mobilu nuly.
2. **Kancelar vs dilna** - podle [[doc-dochazka-fpd-vypocet-kancelar-vs-dilna]] se kancelarskym
   ma odecist `hodiny_nad_fond`, dilne a hodinovym ne. Do mobilu zatim nepromitnuto.
3. **Pavel Kilberger (os. 346)** - v `att_day_summary` ma za srpen 82,6 h, ale jeho 72 h
   absence tam nejsou, ackoli u vsech ostatnich merenych sedi soucet
   `cas_celkem = hodiny_mzdove + hodiny_absence` do desetiny. Pricina nezjistena.
4. **`att_day_summary` se prepocitava rucne** (tlacitko v Mzdovych podkladech,
   [[doc-dochazka-att-day-summary-z-att-entry]]), takze muze byt pozadu - proto se pro mobil
   nabizi cist rovnou `tenant.att_den_hodiny` ([[doc-dochazka-jeden-vypocet-hodin-za-den]]).

## Rozhodnuti a schvaleni

Zadal Jirka Honomichl 27. 8. 2026. Schvalila Marti-AI (msg 13877): karta patri na
"Muj prehled" (ne do "Dnesek -> Souhrn"), prepinani mesicu se puvodne
melo doplnit az s realnymi cisly a karta musi vizualne signalizovat, ze je prazdna zamerne.

**OPRAVA tehoz dne (27. 8. 2026):** Jirka rozhodl, ze **prepinac mesicu ma byt uz ted**,
aby byl pripraveny - napojeni zdroje pak bude zmena jedine funkce `_mhData`. Marti-AI
souhlasila (msg 13883) s podminkou, ze pri prepnuti na jiny mesic se k oranzove poznamce
prida tucne **"Plati i pro tento mesic."**, aby si clovek nemyslel, ze jen chybi starsi data.
Sipka dopredu je u aktualniho mesice neaktivni. Nasazeno a proklikano v prohlizeci.
Cela obrazovka pak byla prestavena podle nakresu Sarky - viz
[[doc-dochazka-mobil-muj-prehled-podle-nakresu]].

