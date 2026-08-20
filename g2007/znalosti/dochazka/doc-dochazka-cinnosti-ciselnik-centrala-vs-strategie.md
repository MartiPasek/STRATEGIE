# Číselník činností: Centrála × STRATEGIE — čísla musí sedět, Režie je zakázka

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


**Autoritativní je číselník Centrály.** `tenant.vyroba_cinnost.ec_cislo` MUSÍ odpovídat
číslu činnosti v Centrále (EC). Peťa v aplikaci i v Centrále pracuje s **číslem
činnosti (ec_cislo)**, ne s interním `id` — vždy s ní mluv čísly, která vidí ona.

## Stav k 3. 8. 2026 (srovnáno)

Peťa dodala export činností z Centrály (76 položek). Ve STRATEGII jich bylo 47,
takže **30 chybělo**. Doplněny všechny, včetně těch, kvůli kterým to praskalo:

* **30 Dovolená navíc** — samostatný druh nepřítomnosti, NENÍ to totéž co 20 Dovolená
* **37 Nepřítomnost OSVČ** — také samostatný druh, NENÍ to totéž co 30

Dál chyběly: 10 Nařízené volno · 12 Nahrazení volna · 14 Čas na cestě · 22 Nemoc ·
23 OČR · 24 Prac. úraz · 25 Paragraf · 28 Čas. konto-výběr · 29 Osobní hodnocení ·
32 Interní doplnění · 33 Otcovská · 34 Ostatní s náhradou mzdy · 35/47/50/51 Volno
60–90 % · 36 Mateřská · 52 Oprava barvy z lakovny · 53 Garant · 54 Nepřítomen pro APS ·
119 Oběd · 120 Kouření · 123 Svačina · 132 Soukromé záležitosti · 133 Náhradní volno ·
136 Výpomoc · 138 Překážka v práci · 999 Domů.

**Po doplnění: nechybí ani jedno číslo a u všech stávajících čísla sedí.**

## Co si pamatovat, ať se to neřeší potřetí

* **„Režie" NIKDY NEBYLA ČINNOST.** `Rezie` (bez háčku) je **ZAKÁZKA** — tak to má
  Helios i Centrála, a proto se do `vyroba_work.zakazka_ref` píše bez diakritiky
  (Peťa + Marti 20. 7. 2026). Činnost `Režie` (id 14, bez čísla) byla omyl;
  3. 8. 2026 archivovaná (active=false) a přejmenovaná tak, aby to bylo vidět.
* **„ostatní - kanceláře"** bez čísla (id 45) byla duplicita — platí činnost
  **6 „Ostatní – kanceláře"**. Archivováno 3. 8. 2026.
* **45 „Bez rozlišení činnosti"** je NAŠE vlastní, v Centrále neexistuje. Používá
  se všude, kde člověk činnost neupřesnil. Nechat.
* **„Garant" je v Centrále dvakrát** — pod 53 i 114. Není to chyba, máme stejně.
* Deset názvů se liší jen typografií (pomlčka, velké písmeno): 6, 8, 9, 11, 31, 41,
  44, 116, 122, 135. Čísla sedí, názvy jsme NEsjednocovali.

## Jak zkontrolovat, že to pořád sedí

Porovnej `tenant.vyroba_cinnost.ec_cislo` proti číselníku Centrály (EC_DilnaCinnosti,
resp. export od Peti). Nesmí chybět žádné číslo a žádná činnost nesmí mít jiné číslo
než v Centrále. Páruj podle ČÍSLA, ne podle názvu — názvy se liší typografií.

Zapsal Claude-26 na výslovný pokyn Peti 3. 8. 2026 („tohle už jsem si říkala
alespoň 2×, určitě jsem ti říkala, ať to zapíšeš do G2007").

