# Dva prehledy Nesplneny FPD - sjednoceny 31.8.2026, prejmenovany, znamenko zustava opacne (UZAVRENO)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Dva přehledy „Nesplněný FPD" — sjednoceno, přejmenováno, UZAVŘENO

**Peťa + C26, 2. 9. 2026.** Zavírá bod z předávky 31. 8. („čeká odpověď Jirky").

## Jak to bylo

Ve STRATEGII byly **dva přehledy stejného jména**:

- **Peťin** pod Kontrolními přehledy (`dochazka_kontrola_data`, `_KONTROLA_FPD_SQL`),
- **Dušanův** pod Výrobou (`fw.data_set` id 198, `vyroba.dusan_nesplneny_fpd_list`,
  zadal Jirka Honomichl, od 23. 7. 2026, soukromý jen pro Dušanův tým).

Dušan je v obou seznamech, takže viděl dvě stejně pojmenované položky s **různými čísly
u téhož člověka**. Peťa na to psala mail 28. 8. 2026 ve 13.52 (Dušanovi, kopie Jirkovi).

**Příčina rozdílu (platila do 31. 8.):** Dušanův přehled bral „má být" **z plánu**
a **absenci nepočítal** jako odpracováno. Komu se vybrala dovolená, vyšel jako dlužník.
Peťa: *„FPD je kontrola, jestli mají plný úvazek, a do toho se počítá odpracováno
i nemoc, dovolená."* To je závazná definice.

## Jak to je teď

**31. 8. 2026 Jirka výpočet sjednotil** (schválila Marti-AI), tři dny po Petině mailu —
proto o tom předávka z 31. 8. ještě nevěděla a popisovala starý stav.

Převzato od Peti (ověřeno čtením SQL 2. 9. 2026, ne podle popisu):

- odpracováno = mzdové + absence − Nepřítomnost OSVČ − nad_fond u kanceláře,
- má být = úvazek na den × pracovní dny z kalendáře, omezené trváním smlouvy,
- hodiny z `tenant.att_den_hodiny` nad `att_entry`, ne z `att_day_summary`,
- verze smlouvy platná ke KONCI období, ne dnešní.

**Nepřevzato, rozhodl Jirka:** práh 0,5 h a Peťiny filtry lidí — Dušan má vidět celý
tým včetně lidí bez manka. Ověřeno, že by ty filtry v jeho týmu nikoho nevyloučily.

**Přejmenováno** — Jirka po domluvě s Dušanem, takže dvě stejně pojmenované položky
v seznamu už nejsou.

## ⚠️ ZNAMÉNKO JE ZÁMĚRNĚ OPAČNÉ — NEOPRAVOVAT

| přehled | sloupec | kladné číslo znamená |
|---|---|---|
| Peťin (Kontrolní přehledy) | „Chybí odpracovat" | **chybí** hodiny |
| Dušanův (Výroba) | „Chybí / Přesčas" | **přesčas** |

U téhož člověka vyjde stejná ABSOLUTNÍ hodnota s opačným znaménkem. Jirka na to byl
upozorněn a rozhodl tak vědomě (řadí mu to největší dlužníky nahoru). **Peťin přehled
se měnit nemá.** Kdo uvidí obě obrazovky vedle sebe, ať ví, že to není chyba výpočtu.

## Výjimka OSVČ

U OSVČ se druh „Nepřítomnost OSVČ" do splněného fondu **nepočítá** — není to placené
volno, je to doba, kdy živnostník nepracoval. Proto Pavel Kilberger (346) vychází se
schodkem, i když má za srpen 88 h nepřítomnosti. Platí to v obou přehledech stejně.

Souvisí: [[doc-dochazka-hlidani-fpd-kdo-se-kontroluje-a-proc]] · [[doc-dochazka-fond-fpd-z-uvazku-ne-ze-zrcadla-centraly]]

