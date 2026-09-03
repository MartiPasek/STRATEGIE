# Opravy docházky mají jen JEDEN datum — vpravo nad dnem (Peťa 3.9.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Opravy docházky mají jen jeden datum — vpravo nad dnem

> oblast: `dochazka` · zadala Peťa 3. 9. 2026, nasadil Claude-26

## Problém
Záložka „Najít člověka v den …" měla **vlastní** políčko s datem („Který den zobrazit")
a detail dne měl **další, nezávislé**. Byla to dvě samostatná pole — vybralo se jméno
a datum vlevo, pak se v detailu datum přepnulo a vlevo zůstalo staré. Peťa 3. 9.:
*„ty dva datumy se liší a je to zavádějící, aby tam byl jen jeden."*

## Řešení (`apps/api/static_db/dochazka-opravy.html` v77)
Levé políčko i s popiskem **zmizelo**. Zůstalo jediné, a to **v pravé části** —
tam, kde se den zobrazuje:
- **Když je den otevřený** — políčko se šipkami ◀ ▶ nad tabulkou dne (beze změny).
- **Když ještě není nikdo vybraný** — totéž políčko nakreslí `datumVpravo()` nad
  prázdné místo pro den, aby šlo den zvolit **předem**. Volá se z `loadPeople()`.
  Pojistky uvnitř: nekreslí nic, když je otevřený den (`CTX`), a nekreslí druhé,
  když už tam jedno je (`#right input` typu date).

Globální proměnná **`POSL_DEN`** drží zvolený den napříč překreslením:
- `_openDayDo` ji nastaví při otevření dne a při každé změně data v detailu,
- `datumVpravo()` z ní vychází a při změně ji zapisuje,
- `_lide(sDatem=true)` z ní bere den při kliku na člověka (`POSL_DEN||today()`).

Proklikávání více lidí po témže dni tím zůstalo zachované. Před prvním otevřením
dne se nabídne dnešek.

## Pozor — návazná oprava v `obnovVse()`
Tlačítko „🔄 Aktualizovat" si pamatovalo a vracelo hodnotu přes selektor
`#left input[type=date]`. Po přestěhování data doprava by hledalo prázdno, proto
je selektor přepsaný na `#right`. **Kdo bude s tím políčkem zase hýbat, musí
zkontrolovat i tohle místo.**

## Zvažované alternativy
Peťa vybírala ze tří: (1) jen datum v detailu, (2) jen datum vlevo a v detailu jen
nápis bez šipek, (3) nechat obě, ale svázat je. Nejdřív padla volba na (1), jenže
v provozu se ukázalo, že **datum musí být vidět i než se někdo vybere** — jinak se
den nedal zvolit předem. Doplněno hned týž den funkcí `datumVpravo()`.
Peťu napadlo dát datum nahoru přes celou šířku obrazovky — nápad je správný, ale
sáhlo by se tím do rozvržení stránky a datum by svítilo i na záložce „K vyřešení",
kde nic neznamená. **Kdyby i tohle nesedlo, tamto je další krok.**

## Souvisí
[[doc-dochazka-opravy-prehled-ui]] — celkový popis obrazovky.

