# Kaskáda rozpadu – kdy se NEdorovnávají okraje úseku

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Pravidlo (C24 / Kristý, 20.–21. 8. 2026)

Kaskáda `att_sync_vyroba_work` má v bodě **5b** dorovnání okrajů – první položku
natáhne na začátek píchnutí, poslední na jeho konec, aby rozpad seděl s hlavičkou.
Nově má **jednu výjimku**: u úseku, jehož hlavička má **`att_entry.local_lock = true`**,
se okraje **nedorovnávají**.

## Proč

`local_lock` nastavuje `att_recompute_header_from_items` – tedy přepočet hlavičky
z položek, který běží při **každé opravě i stornu položky v Opravách**. Ten příznak
je proto spolehlivá stopa **„tenhle úsek už člověk srovnal"**.

Bez výjimky by kaskáda při dalším běhu natáhla ručně zkrácenou krajní položku
zpátky na obálku píchnutí a tiše přepsala práci kontrolora. Původní záměr bodu 5b
(dorovnat rozpad po **prodloužení** píchnutí v Opravách, Kristý 30. 7. 2026) platí
dál všude jinde.

## Co se NEMĚNÍ

- Zakládání chybějících položek u nepokrytých úseků běží dál – to lidskou práci
  nepřepisuje.
- Ořez do úseku a slučování sousedních duplicit běží dál.
- Načtení příznaku je **fail-open**: když selže, kaskáda se chová jako dřív
  (radši dorovnat než spadnout uprostřed dne).

## Ověřeno

- Dotaz na srovnané hlavičky ověřen zvlášť (je uvnitř `try/except`, chyba by se
  jinak tiše spolkla) – na vzorku 12 hlaviček očekáváno 9, vráceno 9.
- Náhled kaskády za 19.–21. 8. proběhl bez chyby, 173 dvojic člověk × den.
- K 21. 8. 2026 **neexistuje v srpnu ani jedna hlavička s `local_lock`, jejíž
  položky by nedosahovaly ke krajům** – změna tedy dnes nic nemění a je čistě
  preventivní.

Hlídá pojistka **`dochazka-kaskada-nedorovnavat-srovnane`**.

## Poznámka k původní diagnóze

Případ „kaskáda vrátila Péťinu ruční opravu" (Lišková 3. 8. 2026) se z dat
**nepodařilo doložit** – v `tenant.att_audit` k tomu dni není žádný `polozka_fix`
ani `polozka_void`. Obě cesty oprav navíc hlavičku přepočítávají, takže obálka
se po zkrácení sama stáhne a kaskáda nemá co natahovat. Zbylá díra jsou zásahy
**mimo Opravy** (přímo v DB) a položky **bez vazby na píchnutí** (k 21. 8. jich
je 205).

