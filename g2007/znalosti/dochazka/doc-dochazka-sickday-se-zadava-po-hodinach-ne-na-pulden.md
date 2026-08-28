# Tři různé míry u absencí: lékař i na minuty, sick day na celé hodiny, ostatní celý/půl dne

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Jak dlouhá smí být absence — tři různé míry, ne jedna

**27. 8. 2026, rozhodla Peťa.** Nahlásil **Dušan Havlát** — nešlo mu ve Správě docházky
opravit sick day na 2 h, formulář hlásil *„Absenci lze zadat jen na celý den (8 h) nebo
půl dne (4 h)"*. Peťa: *„SD se zadává po hodinách."*

## Pravidlo (`att_absence_hpd_kontrola`, verze 3)

| Druh | Jak dlouhá smí být | Proč |
|---|---|---|
| **Lékař** | **i na minuty** | Leží uvnitř pracovního dne, hodiny se počítají z času od–do. Zaokrouhlovat se nesmí. |
| **Sick day** | po hodinách, ale jen na **CELÉ hodiny** (1, 2, 3, 4…), nikdy 2,5 | Čerpá se po hodinách, půlhodiny nedávají smysl. |
| **Vše ostatní** (dovolená, nemoc, OČR, neplacené, mateřská…) | jen **celý nebo půl dne** podle úvazku | Původní pravidlo Peti z 25. 8. 2026. |

Záznamy, které nesou **skutečný čas** (`ma_cas`), projdou vždy — hodiny si počítají samy.

## Proč pravidlo vzniklo a co bylo špatně
Pravidlo o celém/půl dni zavedla Peťa **25. 8. 2026** — Dvořákové (denní fond 6 h) prošlo
8 h a později 4 h, což není ani celý, ani půl den. Výjimku ale tehdy dostal **jen Lékař**
a **na sick day se zapomnělo**, takže spadl pod pravidlo o půldnech.

Přitom sick day se ze své podstaty čerpá po hodinách:
- `doc-dochazka-sickday-lekar-prednostni-cerpani` (17. 8.): *„draw = min(4 h, zbývající
  nárok sick day)"* — návštěva lékaře z něj ubírá po hodinách,
- `doc-dochazka-sickday-kontrola-zustatku-pri-zadavani` (27. 8., Jirka z Petina mailu):
  člověk si ho v mobilu zadává v hodinách, strop je **zbývající nárok**.

## Co pravidlo NEhlídá
**Strop.** Kolik sick day komu zbývá, řeší `sickday_lekar_apply` a `att_limit_kontrola` —
ty se nemění. Tohle pravidlo řeší jen **délku jednoho zápisu**, ne nárok.

## Poučení
Když se do pravidla přidává výjimka pro jeden druh absence, **projít celý číselník** a u
každého druhu se zeptat, jestli se měří **dnem, hodinami, nebo minutami**. Lékař a sick day
patří k sobě (jeden z druhého čerpá) — kdo mění jeden, ať se podívá i na druhý.

