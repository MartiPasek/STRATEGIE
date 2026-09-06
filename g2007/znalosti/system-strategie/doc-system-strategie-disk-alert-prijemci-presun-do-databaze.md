# Vyber spravcu pro upozorneni na disk presunut z router.py do g2007.python (6.9.2026) — vzor presunu

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Vyber spravcu pro upozorneni na disk: presun z router.py do g2007.python

**Zapsal:** Claude-28 (Jiri Honomichl), 6. 9. 2026
**Nasazeno:** `8e11f38a` · **Kod v databazi:** `disk_alert_prijemci`, verze 1, `active`
Zadal Jirka Honomichl, schvalila Marti-AI (msg 14591 a 14593), aktivaci odsouhlasil Jirka.
Navazuje na `doc-system-strategie-hlidac-volneho-mista-prah-80-procent`.

## Proc to vzniklo

Pri uprave hlidace disku 6. 9. 2026 jsem novou pomocnou funkci `_disk_alert_prijemci`
napsal primo do `modules/erp/api/router.py`. To je **proti bodu 2 pravidel prace**
("kod zije v databazi, ne v router.py"). Priznal jsem to v shrnuti session a Jirka
rekl presunout hned. **Je to zaroven pouzitelny vzor, jak takovy presun udelat ciste.**

## Co funkce dela

Vraci seznam dvojic (adresa, id uzivatele) pro vsechny spravce (`public.users.is_admin`).
Adresa z `public.user_contacts` (typ `email`, aktivni), poradim overeny → hlavni →
nejnizsi id; u vice adres jen jedna. **Zadne jmeno ani id natvrdo.**
Pri jakekoli chybe vraci prazdny seznam — volajici kvuli tomu nesmi prijit o zapis
stavu disku.

⚠️ `users.ews_email` je PRIHLASOVACI UDAJ a k odesilani se NIKDY nepouziva.

## Postup presunu (vzor pro priste)

1. **Schvaleni Marti-AI** predem (pravidlo 7).
2. **Zapis do `g2007.python` pres base64** — kod musi mit funkci `run()`, jinak
   `erp_registry.call()` skonci chybou. Base64 kvuli tomu, ze dvojtecka v kodu se
   jinak vezme jako parametr dotazu a dlouha odsazeni muze prijit o mezery.
   Zapis do `g2007.python` je **konstruktivni**, takze jde bez schvalovaciho prouzku.
3. **Overit otisk** — `SELECT length(zdroj), md5(zdroj) FROM g2007.python WHERE kod=...`
   proti lokalne spoctenemu. 6. 9. 2026 sedelo na bajt (1918 znaku).
4. **Stav `navrzeno` → `active` az na LIDSKY pokyn** (bod 3 pravidel).
   **Marti-AI aktivaci sama neodsouhlasi** a vyslovne na to upozornila — je to AI,
   ne clovek. Schvaluje Jirka nebo rodic.
5. **Hned vyzkouset `@@PYRUN <kod>`** a zkontrolovat vysledek.
6. **Teprve pak** nahradit telo v router.py tenkou spojkou.
7. Po nasazeni **spustit `@@PYRUN` znovu** a overit, ze aplikace bezi na novem ulozeni.

## Past, na kterou jsem narazil

**`@@PYRUN` pousti jen `stav_zivota='active'`** (a zaroven `vedlejsi_ucinek=false`).
Kandidata ve stavu `navrzeno` tedy pres most **vyzkouset nejde** — vznika kruh
"nechci aktivovat neovereny kod, ale overit ho pred aktivaci neumim".

Reseni, ktere jsme pouzili: samotny SQL dotaz uvnitr funkce se da spustit primo pres
most a overit jeho vysledek; novy je pak jen obal. Aktivuje se se **zachrannou siti** —
kdyz `@@PYRUN` po aktivaci nevrati spravny vysledek, vrati se stav na `navrzeno`
a router.py se necha, jak je (stary kod tam do te doby porad bezi, takze se nic nerozbije).

## Rozhodnuti: vlastni spojeni, ne predany parametr

Funkce si otevira **vlastni spojeni do databaze** misto toho, aby ho dostala jako
parametr. Duvod (schvalila Marti-AI): jen cte, takze nema co delat v transakci, ktera
zapisuje do `fw.disk_monitor`. Na jeji zadost ma **kratky limit na dotaz**
(`SET LOCAL statement_timeout = '3s'`) a explicitni `close()` v `finally`, aby pri
nedostupne databazi neviselo a nezdrzovalo cestu upozorneni.

Parametr `ds` v tenke spojce v router.py zustal kvuli volajicim, ale uz se nepouziva.

## Overeno

`@@PYRUN disk_alert_prijemci` vratil pred i po nasazeni tri spravce s firemnimi
adresami (Marti Pasek 1, Kristyna Maresova 11, Jiri Honomichl 20), za 10-14 ms.
Radeni podle overeny → hlavni funguje: u Martiho i Kristyny, kteri maji dve adresy,
vybralo firemni, ne soukromou.

