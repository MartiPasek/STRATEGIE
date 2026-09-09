# Hláška od člověka v Opravách začínala datem, které vypadalo jako den docházky (Peťa 9. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

**Peťa + Claude‑26, 9. 9. 2026.** Peťa: *„ty hlášky od lidí jsou hrozně zmatečné — první mi napadne, že hlásí, že to mělo být na 4. 9., a ne že to hlásí čtvrtého devátého."*

## Co se dělo

V detailu dne 3. 9. 2026 stálo v panelu „Co člověk hlásí" u Zuzany Duspivové doslova:

> Den — „04.09. 08.23 — 8.30-16.05, chybí příchod"

To datum na začátku NENÍ den, kterého se hlášení týká — je to okamžik, kdy člověk hlášku poslal (v `att_day_confirm.confirmed_at` sedí na sekundu). Den, o který jde, je ten otevřený v hlavičce.

Přitěžující okolnosti:

- **Prefix mají jen některé hlášky.** Namjak „Odchod 15.30", Diviš „Příchod v 5.40", Šárka „Start v 8.00" ho nemají vůbec. V našem kódu prefix nevzniká — prošel jsem serverovou i webovou část. Zbývá nativní aplikace v telefonu; NEOVĚŘENO, jen jediná zbylá možnost.
- **Víc hlášení k jednomu dni se slepí do jedné věty.** Od 19. 8. 2026 se druhá žádost nepřepisuje, ale bez odřádkování to splyne — Marek Honal 4. 9. „04.09. 08.26 — Konec pauzy 8.08 04.09. 08.27 — Začátek 8.08".

## Oprava zobrazení (nasazeno 9. 9. 2026)

`apps/api/static_db/dochazka-opravy.html`, funkce `_hlasHtml(note, denIso, kdyIso)`:

1. Prefix `DD.MM. HH.MM —` se z textu vytáhne a vypíše NAD hlášení šedě jako „nahlášeno 4. 9. v 8.23".
2. Když se datum nahlášení liší ode dne docházky, píše se **„nahlášeno druhý den, 4. 9. …"** — tohle Peťě chybělo nejvíc.
3. Slepená hlášení se rozdělí na samostatné řádky.
4. Hlášky bez prefixu dostanou čas z `att_day_confirm.confirmed_at`, takže vypadají stejně. Kvůli tomu `att_fix_day` nově vrací v poli `dispute` také `nahlaseno`.
5. Dodatek „ | vyřízeno (kdo) …" se vypíše šedě pod textem.

Do dat se nesahá — je to oprava zobrazení, takže spraví i všechny staré hlášky.

## Co zbývá

- Stejnou úpravu dát do mobilu (`mobile.html` a `mobile_parts/60_dochazka.js`), ať to lidi vidí stejně.
- U zdroje — aby aplikace v telefonu datum do textu nepsala vůbec, čas nahlášení máme uložený zvlášť. To je zásah do nativní aplikace, patří Jirkovi.

