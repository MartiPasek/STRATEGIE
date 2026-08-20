# Sdílená hodnota — nejdřív MAPA (kdo zapisuje a kdo čte), teprve pak měnit (Kristý + Claude-24, 12. 8. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Sdílená hodnota - nejdřív MAPA, teprve pak měnit

**Zdroj -** e-mail Kristýny Marešové z **12. 8. 2026** (adresát Peťa a její Claude, Jirka v kopii). Kristý to poslala **jako návrh, ne jako příkaz**, a zafixování nechala na ostatních. Do G2007 zapsal Claude-28 (Jirka) 14. 8. 2026, protože pod avizovaným kódem tu znalost nikdo nezaložil.

## Pravidlo

Když se mění, **JAK se plní nějaká sdílená hodnota** (tabulka, sloupec, mzdový nebo docházkový podklad), udělá se **nejdřív read-only mapa - nic se nemění**-

1. Najdi **všechna místa**, kde se hodnota **(a) zapisuje/plní** a **(b) čte**.
2. U každého uveď `soubor-řádek` a co dělá.
3. U každého označ, jestli běží **AUTOMATICKY nebo ručně** a jestli ho změna **ovlivní, nebo zůstane po staru**.
4. **Čekej na rozhodnutí člověka.** Teprve pak se mění.
5. Po návrhu se ještě zeptej - **"Co všechno jinde zůstane po staru a mohlo by se to rozejít?"**

**Spouštěcí slova, na která má Claude reagovat důkladně** (Kristýnina formulace) - *"dopadová analýza", "všechna místa", "kdo zapisuje a kdo čte", "co zůstane po staru", "nejdřív mapa, neměň".*

## Proč to vzniklo - reálná škoda

Kristý s Peťou přepnuly `tenant.att_day_summary` (denní mzdový podklad docházky), aby se plnil z naší docházky (`att_entry`) místo ze zrcadla staré Centrály - udělaly na to přepočet i tlačítko "Přepočítat".

Jenže do téže tabulky **zapisuje víc míst** - generace mezd (`_mzdy_refresh_zrcadla` -> `sync_dochazka_sumaden`) ji dál automaticky přepisovala z Centrály. Jejich přepočet se proto **při každém generování mezd tiše přemazal zpátky**-

- rozešly se hodiny u **39 lidí, dohromady zhruba 85 h**,
- **stejný podklad dával ráno jiný výsledek než večer** podle toho, kdy naposledy proběhlo zrcadlo.

Odhalili to Peťa a její Claude.

## Poučení

Když měníme, odkud se hodnota bere, obvykle ji plní i čte víc míst. Opravíme jedno (třeba tlačítko) a ostatní zůstanou po staru. **Nejzákeřnější jsou místa, která běží automaticky** (generace, sync, noční job) - ta změnu tiše vrátí zpět a nikdo si toho nemusí všimnout. Není to ničí chyba, jen se to snadno přehlédne.

## Souvisí

- `doc-dochazka-att-day-summary-z-att-entry` - konkrétní případ z výše uvedeného příběhu
- `doc-mzdy-zrcadlo-dochazky-ze-strategie` - navazující rozhodnutí, odkud se zrcadlo plní
- Kristý si pravidlo dala do `START_HERE_ID24.md`, Jirka do svých pravidel práce jako bod 12a.

