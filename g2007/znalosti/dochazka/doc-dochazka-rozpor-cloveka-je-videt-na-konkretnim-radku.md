# Rozpor člověka je vidět na konkrétním řádku dne (Peťa 3.9.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Rozpor člověka je vidět na konkrétním řádku dne

> oblast: `dochazka` · zadala Peťa 3. 9. 2026, nasadil Claude-26

## Proč to vzniklo
Lukáš Horký 2. 9. 2026 poslal rozpor ke konkrétnímu záznamu (13.15-20.27, „Ahoj,
odcházel jsem 15.15"). Peťa to vyhodnotila tak, že mu docházku ukončila v 15.15
a **večerní záznamy smazala v domnění, že jsou neplatné**. Kolega ji upozornil,
že rozpor psal právě k tomu jednomu zápisu a ve schvalování to má rozdělené
po jednotlivých záznamech. Peťa: *„co kdyby se dala tečka k tomu / těm, které
ten dotyčný rozporoval?"*

## Co je nasazeno (`apps/api/static_db/dochazka-opravy.html` v73)
Řádek dne, ke kterému člověk poslal rozpor, dostane ve sloupci **STAV** oranžový
štítek **✋ rozporoval** (`.tag.rozp`), vedle dosavadních štítků (storno, 🛠 opraveno,
⚠ neodhlášeno…). V title je vysvětlení, že text rozporu je nahoře v panelu
„Co člověk hlásí" a taky v poznámce pod řádkem.

## Odkud se to pozná
Rozpor od člověka se ukládá do **`tenant.att_entry.note`** s prefixem `✋ ROZPOR:`.
Frontend to už dřív četl do proměnné `_maRozpor` (kvůli výpisu poznámek pod řádkem,
Peťa 19. 8. 2026) — nově se z téže proměnné rozsvítí i štítek. **Žádná změna serveru,
žádné nové pole.**

## Platí i na stornovaných řádcích
Štítek se ukáže i u řádku, který je mezitím `superseded` (šedý „storno") — přesně
tam, kde chyběl nejvíc. Původní hlášení tak zůstane přišpendlené k záznamu, kterého
se týkalo, i po opravě.

## Souvisí
[[doc-dochazka-prekryv-casu-blokuje-zezelenani-a-odbaveni-z-fronty]] — druhá pojistka
z téhož dne (den s překryvem nezezelená a nejde odbavit z fronty).

