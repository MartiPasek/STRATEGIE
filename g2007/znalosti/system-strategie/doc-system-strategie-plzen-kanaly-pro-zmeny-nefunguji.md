# Zmenu na plzenskem serveru neudela zadna AI - obe automaticke cesty jsou zavrene (8. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Zmenu na plzenskem serveru NEUDELA zadna AI - obe automaticke cesty jsou zavrene (8. 9. 2026)

Zjisteno pri oprave nocniho prenosu zaloh (`doc-system-strategie-dr-prenos-praha-plzen-pricina-a-oprava-2026-09-08`).
Zadal Jiri Honomichl, overil Claude-28, potvrdila Marti-AI (msg 14929).

**Kdyz je potreba zmenit soubor na EC-SERVER2 (192.168.30.11), napriklad skript
v `C:\scripts\`, musi to udelat CLOVEK pres vzdalenou plochu.** Obe automaticke cesty,
ktere by se k tomu nabizely, jsou k tomu nepouzitelne. Nehledej treti — neni.

## 1. Fronta prikazu `fw.plzen_cmd_queue` NEBEZI

V evidenci vypada dostupne: `fw.plzen_relay_cfg` ma `enabled = true` a HTTP obsluha
(`/api/v1/ops/plzen/enqueue` a `/plzen/pending` v `dr_ops.py`) funguje — prikaz se do
tabulky opravdu zapise.

**Ale poller na plzenske strane si ho nevyzvedne.** 7. 9. 2026 ve 20:55 UTC tam byl
zarazen neskodny cteci prikaz (`hostname` + `Test-Path`); po vice nez pul hodine byl
porad ve stavu `queued`, `taken_at` prazdne. **Tabulka byla od sveho zalozeni 23. 7. 2026
uplne prazdna — kanal se nikdy nepouzil.** Nelze odsud rozlisit, jestli naplanovana uloha
s `plzen_agent.ps1` na serveru nebezi, nebo bezi a neprihlasi se.

**Je to stejny druh pasti jako neexistujici lane 4 u mostu:** tvari se to jako dostupna
cesta a pritom mlci. Kdo tam neco zaradi a ceka, ceka marne.

## 2. Brana Marti-AI zapis na Plzen ODMITA (red_never)

Marti-AI ma na EC-SERVER2 funkcni ruku a **cist umi** (bezne `Get-Content` projde).
Jakmile ale prikaz vypada jako zasah do souboru nebo zaloha, brana ho zaradi jako
**`red_never`, kategorie `zalohy/CMIS`** a nespusti ho. Spousteci je uz samotne
`Copy-Item` na soubor v `C:\scripts\`, a staci i slovo o zaloze v jinak cistem
ctecim prikazu.

Jeji vlastni formulace: *„Ja skript precist mohu, navrhnout presne zneni mohu,
ale zapsat ho tam nemohu — a spravne."*

⛔ **Branu NEOBCHAZET** prevlekanim prikazu do jinych slov. Je to vedoma pojistka.

## Co tedy delat

1. **Pripravit hotovy skript k vlozeni** — ne navod ke cteni. Osvedcil se tvar, ktery
   si sam udela zalohu puvodniho souboru, najde kotvu, nahradi jen ji, zkontroluje
   syntaxi (`[System.Management.Automation.PSParser]::Tokenize`) a **pri jakekoli chybe
   se sam vrati ze zalohy**. Na konci vypise ocislovane "OK", aby clovek videl, kam se doslo.
2. **Vyzkouset ho nanecisto** na napodobenine toho skriptu drive, nez ho clovek pusti.
3. **Clovek: vzdalena plocha na 192.168.30.11 → `powershell_ise` → vlozit nahoru → F5.**
   ⚠️ **Do modreho okna PowerShellu delsi skript nevkladat** — konzole ceka na dokonceni
   prikazu a Enter jen pridava prazdne radky. ISE to zvlada bez problemu (overeno 8. 9. 2026).
4. **Po nasazeni si vysledek precist ocima** — Marti-AI soubor precist smi.

_Souvisi:_ `doc-system-strategie-dr-prenos-praha-plzen-pricina-a-oprava-2026-09-08`,
`doc-system-g2007-plzen-relay-stav`, `doc-provoz-topologie-serveru-praha-plzen`

