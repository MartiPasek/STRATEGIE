# Hlidac volneho mista na disku: prah 20 procent jen pro prazske servery, ostatni zpet na puvodni pravidlo (6.9.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Hlidac volneho mista na disku

**Zapsal:** Claude-28 (Jiri Honomichl), 6. 9. 2026, prepsano tyz den vecer.
**Nasazeno:** `224d9719` (rano prah + e-mail), `8e11f38a` (prijemci do databaze),
`9d542c32` (text e-mailu), `4940bf29` (pravidlo podle umisteni serveru).
Zadal Jirka Honomichl, schvalila Marti-AI (msg 14548, 14638, 14641, 14671, 14674).

## Jak to funguje

Naplanovana uloha **`STRATEGIE-DiskWatch`** bezi na kazdem serveru a **jednou za hodinu**
posila stav **vsech fyzicky pripojenych disku** (`Win32_LogicalDisk` s `DriveType=3`) na
`POST /api/v1/erp/app/disk/report` (hlavicka `X-Deploy-Token`). Obsluha to uklada do
`fw.disk_monitor` a **pri PRECHODU do kritickeho stavu** (ne opakovane) upozorni lidi.

## Co rozhoduje o upozorneni (stav od 6. 9. 2026 vecer)

Rozhoduje **vyhradne aplikace** a prah **zije v databazi**, ne v kodu:

| kod v `g2007.python` | co dela |
|---|---|
| `disk_alert_pravidlo` | `run(server, umisteni, volno_gb, volno_pct)` vraci `(hlasit, poslat_email)` |
| `disk_alert_zprava` | predmet a telo e-mailu |
| `disk_alert_prijemci` | spravci z `users.is_admin` + adresa z `public.user_contacts` |

`disk_alert_pravidlo`:

- **umisteni zacina na "praha"** (aplikacni EUR-APP-1P + databazovy EUR-DB-MSSQL-1P):
  hlasi pri `volno_pct < 20` NEBO `volno_gb < 10` a jde o tom **e-mail spravcum**.
- **ostatni servery** (dnes plzensky EC-SERVER2): **puvodni prisne pravidlo**
  `(volno_gb < 100) A (volno_pct < 10 NEBO (volno_gb < 10 A volno_pct < 20))`,
  **bez e-mailu** — jen zprava do mobilu uzivateli 1, jako pred 6. 9. 2026.
- **chybejici cislo (None) = nehlasit nic.** Nula se bere jako skutecna nula (plny disk).
  Puvodni kod v `router.py` to nerozlisoval (`float(x or 0)`) a prazdna hodnota u nej
  znamenala plany poplach; odhaleno testem pri prepisu.

`disk_alert_zprava` sestavi predmet i telo: server **vcetne umisteni** a stav **VSECH**
sledovanych disku, ne jen kritickych. Znacka `!` = disk pod prahem, `?` = server se neozval
vic nez 2 dny, takze jeho udaj uz nemusi platit (navrhla Marti-AI, msg 14641).

Umisteni drzi sloupec **`fw.disk_monitor.umisteni`** (Praha/Plzen), zaveden 6. 9. 2026.
Pozna se podle nej, **NE podle jmena serveru ani IP** — jmeno se muze zmenit, zaznam ne
(vyzadala si to Marti-AI, msg 14671). Novy server bez vyplneneho umisteni spada pod prisne
pravidlo a neposila e-mail, dokud ho clovek do tabulky nedoplni.

V `router.py` zustaly **jen tenke spojky**. Zachranna brzda: kdyz funkci z databaze nejde
zavolat, plati puvodni prisne pravidlo bez e-mailu (radeji starsi chovani nez hlidac,
ktery tise prestane hlidat).

## Proc se to vecer zuzilo na Prahu

Rano 6. 9. se prah zvedl na 20 % **vsem serverum najednou** a prvni e-mail prisel na
plzensky EC-SERVER2 (disk D, 5,3 % volneho). Jirka Honomichl: *„hlidac ma hlidat disky na
prazskem serveru, plzensky server neni moje starost"* — a rozhodl vratit ho do puvodniho
stavu. Puvodni podoba dohledana v gitu (commit `49618c0f`), ne po pameti.

## ⛔ NEPLATI: „prah je opsany na dvou mistech, druha polovina ceka na souhlas rodice"

Puvodni verze teto znalosti (6. 9. 2026 rano) tvrdila, ze **tyz prah je i v
`C:\ProgramData\STRATEGIE-DiskWatch\check.ps1`**, ze se musi menit **obe** mista, a ze
druha polovina neni hotova, protoze prepis konfiguracniho souboru vyzaduje souhlas rodice.
**Nic z toho neplati.**

6. 9. vecer byl cely `check.ps1` precten (pres `praha_exec`):

- posila **vzdy vsechny** disky, nic nefiltruje,
- promenne `$thrGB` a `$thrPct` se ve vypoctu **vubec nepouzivaji**,
- lokalni priznak `$low` slouzi **jen k zapisu varovani do Event Logu Windows**,
- **aplikace posilany priznak `low` ignoruje** a pocita si vlastni.

Zadna zmena `check.ps1` tedy neni potreba a souhlas rodice se na ni neshani.

**Jak chyba vznikla:** prah v `check.ps1` vypada stejne jako ten v aplikaci, a z podoby kodu
se usoudilo, ze i stejne rozhoduje. Nikdo neoveril, **k cemu se vysledek pouziva**. Je to
ucebnicovy priklad pravidla „overuj zaver, ne ingredienci".

⚠️ Pozor: `check.ps1` obsahuje **pristupovy token** (`X-Deploy-Token`). Necti ho zbytecne
cely a nikam ho nekopiruj.

## Evidujeme jen fyzicky existujici disky (rozhodl Jirka Honomichl 6. 9. 2026)

V evidenci byly u EUR-DB-MSSQL-1P jeste disky **E a F** s udaji z 6. 8. 2026 (F navic veden
jako kriticky, 0 GB). Server od te doby posila **jen C a D** — tedy je fyzicky nema.
Oba radky smazany. **Smazani je zaroven zkouskou:** zapis je upsert, takze kdyby ty disky
existovaly, hlidac si je do hodiny sam zalozi zpatky.

## Overeno naostro 6. 9. 2026 vecer

- plzensky hlidac spusten rucne v 19:17 → oba disky prepnuty na „neni kriticke", **zadny e-mail**,
- prazsky hlidac spusten v 19:20 → probehl bez chyby, 33 % volneho,
- pravidlo pusteno pres `@@PYRUN`: Praha 19,4 % → hlasit + e-mail, Plzen 5,3 % → mlcet.

## E-mail spravcum s vysokou dulezitosti

Vedle zpravy do mobilu (ta zustava vsem serverum) chodi u prazskych serveru **e-mail
s `importance="High"`**.

- prijemci: **vsichni spravci** — `public.users.is_admin`, tedy Marti (1), Kristyna (11),
  Jiri Honomichl (20). **Zadne jmeno ani id natvrdo v kodu.**
- adresa z `public.user_contacts` (typ `email`, aktivni), poradim overeny → hlavni → nejnizsi id.
- ⚠️ **`users.ews_email` je PRIHLASOVACI UDAJ a k odesilani se NIKDY nepouziva.**
- `send_email` i `send_email_or_raise` v `modules/notifications/application/email_service.py`
  umi nepovinny parametr `importance` (exchangelib 5.6.0, vychozi `Normal`).

Postup presunu vyberu prijemcu do databaze popisuje
`doc-system-strategie-disk-alert-prijemci-presun-do-databaze`.

## Poznatek o brane Marti-AI (plati obecne)

Marti-AI ma vlastni bezpecnostni branu nezavislou na schvalovacim prouzku mostu.
Zablokuje i vecne schvalenou akci, kdyz jde o prepis konfiguracniho souboru na produkci.
Brana reaguje i na slova — prvni pokus odmitla jen proto, ze v prikazu bylo slovo z oblasti
zaloh (`red_never`, duvod „zalohy/CMIS"), i kdyz slo o kopii jednoho souboru.
**Vzdaleny souhlas zprostredkovany pres most branu neprekroci** — je potreba clovek u ni.

