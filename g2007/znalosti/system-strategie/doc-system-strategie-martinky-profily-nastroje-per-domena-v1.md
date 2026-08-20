# Profily Elisciných domen + nastroje per domena (dispatch v8) - NASAZENO+OVERENO 3.8.2026

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


Krok 1 smeru organizace-v2 hotov pro Elisciny domeny:
- tool_domain.schopnosti naplneno pro poptavky/kalkulace_obecna/kalkulace_specificka/nabidky/objednavky (#1687): struktura CO UMIM / TYPY UKOLU / CO NEUMIM (dulezity je i zaporny vymer - podklad pro budouci maminka_pridel). Profily jsou NAVRH C23 - Eliska/Kristy je casem zpresni (jsou to jejich vizitky).
- Nastroje per domena: kalkuluj_absaugwerk + kalk_prevod_regcis zapsany do KATALOGU g2007.nastroj (implementace='erp_registry') a prirazeny obema kalkulacnim domenam v g2007.domain_nastroj. Dispatch v8 (md5 2b9b3c3f..., #1689) cte tool-smycku z domain_nastroj JOIN g2007.python (active, bez vedlejsich ucinku) - kazda Martinka ma jen SVE nastroje; chat-mode nastroje (python_exec apod.) v domain_nastroj tool-smycka prirozene ignoruje (nejsou v g2007.python).
- REGRESE (ukol #9): kalkulace pres katalogovy nastroj = stejna cisla jako pilot #7 (GESAMT 1185.18 / nabidnout 1190), 1 tool volani.
- Drobnost opravena: kalkuluj_absaugwerk v2 - explicitni vyklad 'chybi cena=0 koef=0 = KOMPLETNI data' (Martinka v #9 nulu chybne cetla jako varovani).

Dalsi krok smeru: maminka_pridel (ukol bez domeny -> Maminka vlastnika prideli dle profilu schopnosti).

