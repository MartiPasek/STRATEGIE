# Vyhodnocení: u sloučené skupiny smí hodnocení žít jen u JEDNÉ zakázky

> oblast: `vyroba` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)


## Pravidlo

Ve sloučené skupině zakázek existuje **právě jeden seznam osob** — u té zakázky, na kterou
se naposledy kliklo „Připravit hodnocení". Ostatní zakázky skupiny mají seznam prázdný.

Není to konvence, je to nutnost: `ec.vypocet_konstant` sčítá odpracované hodiny **přes
všechny zakázky skupiny** (`sum(o.pocet_hodin)` per zakázka ze zrcadla). Když má vlastní
seznam víc zakázek skupiny, hodiny se **sečtou tolikrát, kolik seznamů existuje**.

## Jak to dělá Centrála (ověřeno v `sys.sql_modules`, 11. 9. 2026)

`EC_Zakazky_PripravaVyhodnoceni` (6 567 znaků) dělá dvě věci, které jsou pro tohle klíčové:

1. Projde kurzorem celou skupinu (`TabZakazka_EXT._IDSkupiny`) a u každé zakázky:
   `DELETE EC_TempVyhodnoceniZak WHERE CisloZakazky = @CisloZakazkyTemp AND CisloZakazky <> @CisloZakazky`
   — smaže hodnocení u **všech ostatních** zakázek skupiny, zvolenou nechá.
2. Lidi vkládá přes `WHERE NOT EXISTS (... CisloZakazky = @CisloZakazky AND CisloZam = hod.Cislo)`
   — **jen doplní chybějící**. Kdo v seznamu je, zůstane i s ručně zadanou efektivitou,
   hodnocením kvality práce a poznámkami.

## Co se stalo u nás (nález naostro, VR10675, 11. 9. 2026)

`ec.priprava_vyhodnoceni` dělala do 11. 9. 2026 **přesný opak**: mazala zvolenou zakázku
a ostatní ve skupině nechávala, a lidi zakládala znovu s efektivitou 100 místo doplňování.

Skupina VR10620 + VR10675 + VR10690 + VR10710:

| | hodin |
|---|---|
| skutečná docházka celé skupiny | 61,62 |
| co spočítala hlavička VR10675 | **121,12** (= 59,50 u VR10620 + 61,62 u VR10675) |
| limit pro srážku | 64,40 |

Zakázka byla vyhodnocena jako přetažená o 56,72 h a **sedmi lidem naskočily srážky
866 Kč**, ačkoli je skupina pod limitem a nemá se strhávat nic. Nic to neohlásilo.

**Opraveno 11. 9. 2026** — obě chování srovnána 1:1 s Centrálou. Vedoucí výroby díky tomu
nemusí hlídat, jestli zakázka náhodou není sloučená.

## Jak osiřelá sada vznikne, i když se u nás neklikne

Import z Centrály **nezrcadlí mazání**. Když někdo v Centrále klikne Připravit na jiné
zakázce skupiny, Centrála tím smaže seznam u té původní — u nás ale zůstane ležet.
U VR10620 tak zbyla sada z 21. 7. 2026 (autor MJirkovsky), kterou Centrála už neměla.

⚠️ **Při hledání podobných případů:** zakázka s vlastním seznamem osob, která v
`EC_TempVyhodnoceniZak` žádný nemá, je kandidát na osiřelou sadu.

## Pojistky, které funkce od 11. 9. 2026 má

1. **Uzamčená historie** (uzamceno=true) — tvrdý zákaz, 1 675 zakázek z let 2021–2025.
2. **Uzavřené vyhodnocení ve skupině** — uzávěrka už vyrobila výplaty v
   `ec.zakazky_finance_zam`; přeházet pod nimi seznam osob by rozešlo peníze s podkladem.
   Nejdřív storno, pak příprava.
3. **Prázdná docházka** — když k zakázce nemáme ani hodinu a hodnocení už tu je, nemazat
   naslepo (nález z VR10220: práce proběhla únor–duben 2025, docházka u nás začíná 10/2025).

## Pravidlo k zapamatování

**Funkce, která maže podle jednoho klíče a počítá přes skupinu, musí mazat taky přes
skupinu.** Jinak je výsledek tiše násobený a nic to neohlásí.

