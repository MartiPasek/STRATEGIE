# Most: @@PYRUN (spousteni ctecich g2007.python) + zapis velkeho kodu pres base64

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# @@PYRUN a bezpecny zapis kodu do g2007.python pres most

Claude-24 (Kristy), 19. 8. 2026. Vzniklo pri Fazi 1 podkladu fakturace OSVC.

## 1) @@PYRUN <kod> [| <args JSON pole>]

Spusti DB-driven skript z `g2007.python` primo z mostu (`/diag-sql`), bez HTTP session.
Priklad: `@@PYRUN podklad_vyplaceni_pdf | [47]`.

BEZPECNOSTNI HRANICE (schvalila Kristy 19.8.2026): most pusti JEN skripty
`stav_zivota='active'` A ZAROVEN `vedlejsi_ucinek=false` (ctou, nezapisuji).
Skripty s vedlejsim ucinkem (syncy, mzdy, migrace) most odmitne - od toho je
schvalovaci banner a mirror joby. Kazde volani se audituje do `g2007.python_run_audit`.
Vystup: dvousloupcova tabulka klic/hodnota; klice obsahujici "b64" se nevypisuji
(jen delka), ostatni hodnoty do 1500 znaku.

K cemu to je: `g2007.python` ma na `kod` UNIKATNI index, takze stara a nova verze
teze funkce vedle sebe nezijou. Bez @@PYRUN by jedinou cestou k overeni nove verze
bylo prepsat produkci a verit. S nim se novy kandidat ulozi pod docasny kod
(napr. `<kod>_faze1`), spusti se obe verze na stejnych vstupech a porovnaji vysledky.

## 2) Zapis velkeho Python kodu do g2007.python pres most = BASE64

Dva realne problemy, oba narazene 19.8.2026:

- **`:neco` v kodu = bind parametr.** Bannerova fronta pousti SQL pres SQLAlchemy
  `text()`, ktere v dollar-quoted retezci NAJDE `:300` (z `str(e)[:300]`) i `:ec_id`
  a spadne na `A value is required for bind parameter '300'`. Skripty pro DB handlery
  maji `:param` skoro vzdy -> primy INSERT se zdrojem v `$py$...$py$` neprojde.
- **Bannerova fronta obcas tise ztrati mezery** v dlouhych odsazovacich behach
  (zname od 1.8.2026, poskodilo att_checkout/att_absence).

RESENI: poslat zdroj jako base64 a slozit ho az v SQL:

```sql
INSERT INTO g2007.python (kod, popis, kategorie, zdroj, stav_zivota, verze, vedlejsi_ucinek)
SELECT 'muj_kod', '...', 'erp_funkce',
       convert_from(decode('QUJD...' || 'REVG...' , 'base64'), 'UTF8'),
       'navrzeno', 1, false
WHERE NOT EXISTS (SELECT 1 FROM g2007.python WHERE kod='muj_kod');
```

Base64 nema dvojtecky ani mezery -> zadny bind parametr, zadna ztrata mezer.
Navic to bezi BEZ banneru (konstruktivni zapis jen do g2007.python).
Radek base64 rozsekej po ~96 znacich a spoj `||`, ať je soubor citelny.
PO ZAPISU VZDY OVER: `SELECT length(zdroj), md5(zdroj) FROM g2007.python WHERE kod=...`
proti lokalne spoctenemu md5 zdroje. 19.8.2026 sedelo na bajt.

## 3) Cteni velkeho kodu z g2007 pres most = TAKY BASE64

Most prevadi konce radku v bunkach na mezery -> Python precteny "napravo" je
nepouzitelny. Cti takhle a dekoduj lokalne:

```sql
SELECT md5(zdroj), length(zdroj),
       replace(encode(convert_to(zdroj,'UTF8'),'base64'), chr(10), '') AS b64
FROM g2007.python WHERE kod='...' AND stav_zivota='active';
```

Cela hodnota je v `CLAUDE<N>_OUT_FULL.txt` (bez orezu) -> base64 dekoduj do souboru
a porovnej md5. Uspora: 19 600 znaku kodu se precte na jedno volani a bez poskozeni.

