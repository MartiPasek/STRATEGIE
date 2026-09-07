# Kaskáda rozpadu: zakázku a činnost nepřepisuje, ČASY A HODINY ano (ověřeno v kódu 7. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Kaskáda rozpadu: co přežije úpravu v Docházce new a co ne

**Ověřeno čtením kódu 7. 9. 2026** (Peťa + Claude-26), zdroj `g2007.python` kód
`att_sync_vyroba_work`. Vzniklo z Petiny otázky, jestli má editace v Docházce new
vůbec smysl, když totéž jde v Opravách.

## Závěr v jedné větě

**Zakázku a činnost kaskáda nepřepisuje — časy a hodiny ano.**

## Proč

Zápisová část kaskády (krok „clip") dělá na existujícím řádku rozpadu přesně tohle:

    UPDATE tenant.vyroba_work SET att_entry_id=…, od=…, konec=…, hodiny=…, updated_at=now()

`zakazka_ref` ani `cinnost_id` v tom UPDATE **nejsou**. Kaskáda je nikdy nesahá.
Proto je úprava zakázky a činnosti v Docházce new bezpečná — a rozhodnutí Peťi
z 31. 8. ji tam nechat je správné, teď i s důkazem.

Časy ale ano, a to dvakrát:
1. **Ořez do obálky hlavičky** — `od` a `konec` se zaříznou do časů píchnutí, `hodiny`
   se přepočtou z ořezaných časů.
2. **Vyplnění okrajů (krok 5b)** — první řádek se natáhne na začátek úseku a poslední
   na jeho konec.
3. Když řádek po úpravě nemá s žádným úsekem překryv, na uzavřeném dni ho kaskáda
   **deaktivuje úplně** — řádek zmizí.

## Klíčový rozdíl mezi Opravami a Docházkou new

Krok 5b se **přeskočí u hlaviček s `local_lock=true`** — to je stopa „tenhle úsek už
člověk srovnal". Ten příznak nasazuje `att_recompute_header_from_items`, kterou volají
**Opravy** (`att_fix_polozka`). Docházka new (`/app/dochazka-zak-tab/save`) ji nevolá,
takže značka nevznikne a okraje se dorovnají zpátky.

| | Opravy (`fix/polozka`) | Docházka new (`save`) |
|---|---|---|
| přepočte hlavičku + nasadí `local_lock` | ano | **ne** |
| povinný důvod, audit, notifikace, přepočet dne | ano | **ne** |
| kontrola překryvu a zamčeného období | ano | **ne** |
| záznam z Centrály | odmítne | **přepíše** |

## Co z toho plyne

Úprava **času nebo hodin** v Docházce new vypadá, že se uložila, a při dalším srovnání
dne se tiše vrátí. Kaskádu spouští spousta věcí — `att_checkout` (každý odchod z mobilu),
`att_wa_open` (každé přepnutí zakázky), `att_confirm_day`, `att_auto_checkout_midnight`
(noční automat) a všechny `att_fix_*`. Prakticky to tedy nastane během hodin.

**Je to stejná rodina jako němý hlídač** — nic nespadne, nic nenahlásí, jen se výsledek
tiše ztratí. Návrh (NEROZHODNUTO k 7. 9. 2026): pole Začátek, Konec a Čas v editačním
okně Docházky new zamknout nebo odebrat; časy se opravují v Opravách. Zakázka a činnost
tam zůstávají.

## Poctivá míra jistoty

Přečteno z kódu, **nepozorováno na reálném případu ztracené úpravy** — a doložit to
zpětně nejde, protože `/save` v Docházce new nic nezapisuje do auditu. To je samo o sobě
součást problému.

## Souvisí

- doc-dochazka-dochazka-new-zakladani-a-mazani-jen-v-opravach
- doc-dochazka-oprava-polozek-obousmerny-sync
- doc-dochazka-att-entry-vyroba-work-kaskada

