# Texty pro lidi pisou Claudove s diakritikou - most, notifikace ani appka ji nerozbiji (14. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Texty pro lidi píšeme s diakritikou — most, notifikace ani appka ji nerozbijí (14. 9. 2026)

**Zadal Jiří Honomichl 14. 9. 2026** („proč jsou texty notifikací v mobilní aplikaci bez
diakritiky? oprav to"), schválila Marti-AI (msg 15510), provedl Claude-28.

## Nejdřív to hlavní: technická vina nikde není

Ověřeno měřením, ne úvahou:

- **Most** čte `CLAUDE_NOTIFY.txt` jako UTF-8 (`read_text(encoding="utf-8")`) a posílá JSON
  v UTF-8. **Nic neořezává.**
- **Zkouška naostro 14. 9. 2026:** dvě testovací notifikace se stejným českým textem —
  jedna zapsaná editačním nástrojem, druhá z příkazové řádky (`printf`). Obě dorazily do
  `fw.mobile_command` **s háčky a čárkami a bez jediného poškozeného znaku**
  (id 24719 a 24720) a Jirka je tak viděl **i v telefonu**.
- Systémové notifikace, které diakritiku v kódu mají (docházka, SMS brána, záloha),
  chodí do telefonu správně už dávno.

**Závěr: když v notifikaci chybí háčky, je to tím, že je někdo nenapsal.**

## Kde to chybělo (stav k 14. 9. 2026 před opravou)

Za 60 dní bylo v `fw.mobile_command` **45 různých titulků bez diakritiky**. Dvě skupiny:

**(a) automaty s textem natvrdo v `g2007.python`** — opraveno týž den:

| funkce | co posílá | komu | kolik za 60 dní |
|---|---|---|---|
| `att_prazdny_den_fond` | „Doplnili jsme ti DD.MM. do fondu" + tělo | **zaměstnancům** | přes 130 |
| `att_odbavene_pripomenuti` | týdenní souhrn odbavených nálezů + 9 názvů pravidel | kontrole docházky | 4 |
| `disk_alert_zprava` | předmět i tělo upozornění na disk | provozu | 62 |

**(b) zprávy, které psali Claudové ručně** — vlastní notifikace z mostu a zprávy commitů,
ze kterých se skládá notifikace „Claude-XX — nasazeno ✓". Tady není co opravovat v kódu;
je to **zvyk psát do souborů mostu bez diakritiky**, který vznikl u SQL (tam se posílá
base64 kvůli hlídači dotazů) a přelil se i tam, kam nepatří.

## Pravidlo

- **Co čte člověk, píše se česky správně** — notifikace, hlášky v appce, popisky dlaždic,
  nápověda, a **i zprávy commitů**, protože z nich vzniká notifikace do telefonu.
- **Bez diakritiky zůstává jen to, co čte stroj** — kódy, názvy sloupců a tabulek, klíče
  pravidel, interní logy a chybové hlášky pro vývojáře.
- Diakritika **není důvod něco kódovat do base64**. Base64 se používá kvůli **dvojtečkám
  a mezerám** při zápisu kódu přes most (viz `doc-system-strategie-most-pyrun-a-base64-zapis`),
  ne kvůli háčkům. Když se ale base64 stejně používá, háčky se svezou bez rizika.

## Jak se to ověřuje

Nejrychlejší kontrola nad ostrými daty:

```sql
SELECT left(title,46), count(*)
FROM fw.mobile_command
WHERE created_at > now() - interval '60 days'
GROUP BY 1
HAVING NOT bool_or(title ~ '[áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]'
                OR message ~ '[áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]')
ORDER BY 2 DESC;
```

U funkce, která text skládá, se výsledek **spustí naostro** přes `@@PYRUN <kod> | [args]`
(pustí jen skripty bez vedlejšího účinku) a text se přečte celý — právě tak se 14. 9. našla
dvě slova, která při opravě `disk_alert_zprava` propadla („mene nez", „hlídac").

## Co bylo dotaženo ještě též noci (Jiří Honomichl: „oprav, co zůstalo otevřené“)

- **Sick day v `att_absence`** — **žádná oprava nebyla potřeba.** Živé znění (verze 23) už
  má „Pozor — zapsali jsme ti sick day“ i celé tělo česky; opraveno 27. 8. 2026.
  Čtyři ASCII zprávy v datech jsou z 6.–19. 8., tedy **starší než ta oprava**.
  Poučení: věk zprávy v `fw.mobile_command` se musí porovnat s datem opravy kódu,
  jinak se ohlásí jako otevřený bod něco, co je dávno hotové.
- **„DR obnova: NENI OK“** — producenta jsem našel v jádře (`modules/erp/api/dr_ops.py`),
  ne v `g2007.python`. Opraven titulek, tělo zprávy i **všech devět důvodů**, ze kterých
  se skládá (databáze neodpovídá, data stará X h, málo tabulek, 0 konverzací, 0 vektorů,
  chybí pgvector, agent, řetěz záloh prázdný, řetěz záloh zamrzlý) i text při úspěchu.
  **Hodnota `verdict` („OK“/„NENI_OK“) zůstala beze změny** — je strojová, ukládá se do
  `fw.dr_selfcheck.verdict` a porovnává se; přepsat ji by ticho rozbilo rozhodování,
  jestli se má notifikace vůbec poslat. Nasazeno commitem `dfa2e080`.
- **„Plzen“ bez háčku** v upozornění na disk — nebyl to text v kódu, ale **hodnota v datech**
  (`fw.disk_monitor.umisteni`). Před změnou ověřeno, že se hodnota nikde neporovnává,
  jen vypisuje. Opraveno na „Plzeň“ (2 řádky) a ověřeno spuštěním `disk_alert_zprava`
  přes `@@PYRUN` — živý text teď říká „server EC-SERVER2 (Plzeň)“.

## Co zůstává otevřené

- **`fw.dr_selfcheck.source`** má také hodnotu „Plzen“, ale ta se **používá i v kódu**
  jako výchozí hodnota (`cockpit-marti.html`: `d.source||'Plzen'`), takže změna by se
  musela dělat na obou místech najednou. Nedotčeno záměrně.

