# Skript, ktery ma clovek spustit v PowerShell ISE, nesmi koncit prikazem exit - zavre mu cele okno (14. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# V PowerShell ISE prikaz `exit` zavre CELE OKNO

Narazil na to Jirka Honomichl 14. 9. 2026 pri prvnim ostrem spusteni noveho skriptu
na plzenskem serveru. Zapsal Claude-28.

> ## Hlavni veta
> **Skript, ktery ma clovek spoustet v ISE, nesmi koncit `exit`.** V ISE `exit`
> neukonci jen skript, ale **cele okno** - clovek tim prijde o zaverecnou hlasku
> a nema jak poznat, jestli beh dopadl dobre. Jirkovi se okno zavrelo presne ve
> chvili, kdy mel precist vysledek; prenos pritom probehl spravne.

## Proc na tom zalezi zvlast u Plzne

Na plzenskem serveru (192.168.30.11) **nesmi nic menit zadna AI** - vsechno tam
spousti clovek pres vzdalenou plochu, typicky prave v ISE (do modreho okna
PowerShellu se delsi skript vkladat nema, ceka na dokonceni prikazu).
Viz `doc-system-strategie-plzen-kanaly-pro-zmeny-nefunguji`. Kazdy skript, ktery
pro nej pripravujeme, tedy tenhle problem ma - dokud se nenapise jinak.

## Jak to napsat spravne

Naplanovana uloha navratovy kod POTREBUJE (jinak nepozna selhani), takze `exit`
nejde jen vypustit. Resenim je telo ve funkci a `exit` az mimo ISE:

```
function Prevzeti {
  ...
  if (chyba) { return 1 }
  ...
  return 0
}

$vysledek = @(Prevzeti)      # @(...)[-1] je pojistka, kdyby neco proteklo do vystupu
$kod = [int]$vysledek[-1]

if ($Host.Name -like '*ISE*') {
  Write-Host ('=== HOTOVO. Navratovy kod: {0} ===' -f $kod)
} else {
  exit $kod
}
```

- Vsechny `exit N` v tele se prepsi na `return N`.
- **Pozor na vystup do proudu:** kdyz nejaky prikaz v tele neco vypise (napr. bez
  `| Out-Null`), stane se to soucasti navratove hodnoty funkce. Proto `@(...)[-1]`.
- Prakticky navod pro cloveka: vzdalena plocha -> `powershell_ise` -> vlozit nahoru -> F5.

## Kde to uz je udelane

`scripts/ops/docs_pull.ps1` (prevzeti zalohy dokumentu z Prahy do Plzne) - commit
`bf7b8407`. Tam je i komentar s duvodem, aby to nikdo nevratil zpet.

_Souvisi:_ `doc-provoz-zaloha-dokumentu-do-plzne-balik-a-prevzeti`,
`doc-system-strategie-plzen-kanaly-pro-zmeny-nefunguji`

