# Vyhodnoceni zakazek: hodiny a cinnosti prepnuty na nase tabulky (5.8.2026)

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Prepnuti hodin a cinnosti na nase tabulky

**Hotovo a overeno 5. 8. 2026** (C28/Jirka). Schvalili Marti-AI (msg 12211) a Jirka.
Krok 1+2 ze ctyr (zbyva: zakazky, penize).

## Co se zmenilo

| funkce | drive | nyni |
|---|---|---|
| `ec.priprava_vyhodnoceni` | seznam lidi z `ec.dochazka` (3 radky) | `tenant.vyroba_work` |
| `ec.prepocet_vyhodnoceni` | hodiny z `ec.dochazka` + priznak z `ec.dilna_cinnosti` (0 radku) | `tenant.vyroba_work` + `tenant.vyroba_cinnost` |

**Vzorce beze zmeny** - menilo se jen, ODKUD se ctou vstupy.
`ec.dochazka_neevidovana` vypustena: 0 radku u nas i v Centrale (overeno).

## Overeni

Ferova mnozina = **113 zakazek**, ktere se v Centrale pracovaly VYHRADNE v roce 2026
(nase `vyroba_work` zacina 1. 1. 2026, starsi hodiny nemame).

Soucet hodin: **nase 16 814,56 h = Centrala 16 814,56 h**. Presna shoda.
Po mesicich: leden 1 754,76 · unor 3 816,97 · brezen 4 520,98 · duben 4 138,24 ·
kveten 2 311,11 · cerven 272,10 · cervenec 0,40.

## PAST pri overovani (dvakrat me zmatla)

`ec.vyhodnoceni_osoba.pocet_hodin` NENI aktualni stav - je to **snimek k datu vyhodnoceni**.
Porovnavat proti nemu per osoba nema smysl: prace na zakazce pokracovala i po vyhodnoceni
a rozdeleni na lidi se od te doby zmenilo. Porovnavej **soucty hodin na zakazce**
proti `EC_Dochazka`, ne proti snimku.

Druha past: reference z Centraly zahrnuje hodiny za CELY zivot zakazky, tedy i pred rokem
2026. Zakazky pracovane uz v roce 2025 proto ve srovnani nutne vychazi nizsi - nejsou to
chybejici hodiny, jen je u nas nemame. Proto ta ferova mnozina 113 zakazek.

## Parovani cloveka

`tenant.vyroba_work.cislo_zam` je **text**, `ec.vyhodnoceni_osoba.cislo_zam` je **integer**.
Parovat pres `btrim(w.cislo_zam) = V.cislo_zam::text` (odolne vuci mezeram i pripadnym
necislenym hodnotam). Data overena: 21 727 radku, zadne prazdne, zadne mezery,
vse ciselne, zadne nuly vpredu, 68 ruznych lidi.

