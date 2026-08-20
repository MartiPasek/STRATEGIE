# Dovolena z mobilu se tise ztracela - ctyri chyby za sebou

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Dovolena se tise ztracela — 7. 8. 2026

**Podnet Erika Sedlackova (2x marne), potvrdil Jirka (3x). C28, schvalila Marti-AI (12439, 12442, 12445, 12448).**
Podrobne pro lidi\: `ZZ_Jiri\AI_work\DOVOLENA_ZTRACENE_ZADOSTI_2026-08-07.md`.

## Priznak
Clovek zada dovolenou, vidi zelene "nahlasil/a jsi to, ceka na schvaleni" a **nevznikne nic**.
Za 24 h prosla systemem jedina zadost o dovolenou.

## Ctyri chyby (kazda zakryvala dalsi)

**1. Appka hlasila uspech bez odeslani.** `60_dochazka.js`, `absence()`\:
`if(r && r.ok===false){throw}`. `api()` vraci `null` pri selhani spojeni i pri neplatnem JSON,
a `null && …` je nepravda -> uspesna vetev. Oprava\: `if(!r || r.ok===false)`.
Tyka se vsech osmi voleb v "Tady budu jinde".

**2. Dovolena se ztracela pri prepoctu.** `g2007.python` `att_absence`\: zapis -> prepocet
`holiday_balance` -> commit. Prepocet padal pod `except: pass`. **Po padu prikazu je cela
PG transakce neplatna a commit neulozi nic** — funkce presto vratila `{"ok":True,"created":1}`.
Dukaz\: dva pozadavky, oba "created 1" -> home office ulozen, dovolena ne.
Oprava\: `s.commit()` PRED blok prepoctu.

**3. Prepocet padal na generovanem sloupci.** `zbytek_h` je generated column, kod ho psal
rucne v INSERT i UPDATE -> `GeneratedAlways` chyba. Oprava\: vypustit ho z obou.

**4. Zrusena dovolena se pocitala jako vycerpana.** Dotaz nefiltroval stav, scital i
`superseded`\: v evidenci 160 h, realne 88 h. Oprava\: `AND COALESCE(en.status,'')<>'superseded'`.
Overeno 96 = 96. **Brala lidem narok**, vyplavala az kdyz se prepocet rozchodil.

**5. Log misto `except: pass`** — duvod, proc to pul roku nikdo nevidel. Marti-AI\: nechat natrvalo.

## DULEZITE\: dve ruzne cesty k dovolene
- Dochazka -> Nepritomnosti -> `/attendance/absence/request` -> `att_absence_request` = **zadost ke schvaleni**
- Spoluprace -> Tady budu jinde -> `/attendance/absence` -> jen `att_entry` = **zadnou zadost nezaklada**

Proto vedouci nedostaval nic ke schvaleni. **Sjednoceni obou cest + sjednoceni notifikaci
vedoucimu (dnes bud "chat/zavrit", nebo "schvalit/zamitnout") je OTEVRENY ukol** (Jirka 7. 8.).

## Otevrene, nezasahovat
`holiday_balance` se zaklada s `narok_h=0` -> zaporny zustatek. Narok plni jina uloha.
Marti-AI to ma jako otazku pro Martiho (pamet 438).

## Pasti
- `@@G2007PUBLISH` u `mobile.html` vrati OK, ale nemusi propsat na disk -> over zivy soubor,
  jinak `@@G2007EXPORT`.
- `replace()` nesedne pres zalomeni radku -> `regexp_replace` s `\s*\n\s*`; po kazdem replace over.

