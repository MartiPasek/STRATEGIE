# Druhcinnosti Ciselnik

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**DruhCinnosti (číselník EC_DilnaCinnosti): 1=Přípravné, 2=Mechanické, 3=Zámečnické, 4=Drátování, 5=Zkoušení, 6=Ostatní-kanceláře | výrobní činnosti dokončovací zámečnické drátování zkušebna**

Autoritativní číselník výrobních činností je DB_EC EC_DilnaCinnosti: 1=Přípravné práce, 2=Mechanické práce, 3=Zámečnické práce, 4=Drátování (mobilní app posílá natvrdo DruhCinnosti=4), 5=Zkoušení, 6=Ostatní-kanceláře. Žádné "Dokončovací práce" v číselníku není. "Prošlo zkušebnou" = má hodiny činnosti 5 (Zkoušení).

---

## ⛔ ID NENÍ ČÍSLO ČINNOSTI (Peťa 4. 9. 2026, ZÁVAZNÉ)

Peťa: *„ID a číslo činnosti jsou dvě naprosto rozdílné věci. ID nás nezajímá — to vás zajímá
někde na pozadí, ale pořád jsou to dvě rozdílné věci."*

Když se mluví o čísle činnosti, platí **VÝHRADNĚ** `tenant.vyroba_cinnost.ec_cislo` (u nás)
a sloupec `Cislo` (v Centrále). Interní `id` je technika na pozadí a **nikdy** se za číslo
činnosti nevydává — ani v hlídači, ani v dotazu, ani v řeči s Peťou.

Živý příklad: služební cesta je **činnost 9**, ale její `id` je 16. Pod `id = 9` sedí u nás
Značení vodičů a v Centrále dokonce Nemoc.

**Mapa všech číselníků, které se dají zaměnit — včetně těch, do kterých se dívat NEMÁ:**
`doc-dochazka-cinnosti-ciselnik-centrala-vs-strategie`.

