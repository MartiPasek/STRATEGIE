# Zaverecne overeni rozpadu dovolene a hlidani stropu (17. 8. 2026) + nalez zastarale pojistky g2007-soubor-vs-git

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Zaverecne overeni prace na dovolene a sick days (Jirka, 17. 8. 2026)

Kontrola po dokonceni cele davky zmen (rozpad dovolene, hlidani stropu, sjednoceni sick days,
oprava kalendare). Vse overeno v datech, v prohlizeci a spustenim systemovych pojistek.

## Co bylo overeno a PROSLO
1. **Soucet dovolene** - u vsech 74 radku (73 lidi plus systemova vrstva) plati
   dovolena_dni = dovolena_zakladni_dni + dovolena_navic_dni. Nula rozporu.
2. **Kalendar 2027** - 365 dnu, 252 pracovnich, 13 svatku vcetne pohyblivych Velikonoc.
   Zalozil se sam pri prvnim dotazu na rok 2027 (lazy mechanismus).
3. **Stara tabulka** tenant.engagement_entitlement neexistuje, zaloha
   engagement_entitlement__zaloha_20260816 ma 1926 radku.
4. **Zadna pojistka** uz nesaha na smazanou tabulku.
5. **Hlidani stropu** naostro pres nahledovy endpoint - dovolena 21 dni proti zbylym 18
   hlasi prekroceni o 3 dny, sick day 40 h proti zbylym 12 h hlasi chybejicich 28 h
   a nabizi lekare. Roky se resi zvlast.
6. **Prehled Narok a cerpani** (74 radku) a **Podminky zamestnancu** (74 pomeru) se nactou
   a cisla sedi. Mobil se nacita, konzole bez chyb.
7. **Pojistky spustene rucne** - narok-dovolene-pravidla, narok-cerpani-prehled,
   absence-stejna-hodnota-vsude, fond-z-uvazku-ne-z-centraly, mzdy-vstupy-ze-strategie,
   vicedenni-dovolena vraci vsechny true.

## PROKLIKANO V MOBILU (doplneno 17. 8. 2026, na pokyn Jirky)
Backend uz overeny byl, tohle je overeni okem v appce.
- **Moje podminky** ukazuji dovolenou ROZDELENOU - Dovolena 0, Dovolena navic 26,
  Dovolena celkem (pocita se) 26, vsechny tri jako osobni hodnota. Je to jen vypis,
  zadna pole k editaci.
- **Formular zadosti o absenci** (Firma - Spoluprace - Nepritomnosti) ma pod tlacitkem
  ZIVY NAHLED zustatku, ktery se meni pri kazde zmene datumu. Pri jednodennim rozsahu
  ukazal "Rok 2026 - zadas 1 den, zbude 17 dni". Po roztazeni rozsahu do prosince naskocilo
  cervene varovani "V roce 2026 ti zbyva 18 dni dovolene, zadas o 86 dni - prekracujes
  narok o 68 dni. Zadost presto muzes odeslat - rozhodne o ni vedouci." Nic se pritom
  neodesilalo, nahled je jen GET.
- **Dnesek** se nacita spravne (pichacky, bocni menu, filtry).
- **POZOR pro priste** - formular vlastni zadosti se VEDOUCIMU nezobrazuje, je to zamer
  z 16. 8. 2026 (fragment 50, radek 182). Kdo testuje na uctu vedouciho, formular nenajde
  a muze si myslet, ze je rozbity. Neni.

## Tri opravy textu, nalezene az pri teto kontrole
- Veta "Sick day ti letos nezbyva" se ukazovala i tehdy, kdyz cast zustatku jeste byla
  (napr. zbyva 12 h, clovek zada 40 h). Nove "Na cely rozsah ti sick day nestaci"
  plus vysvetleni, ze se strhne co jde a zbytek bude Lekar s listeckem.
- Sklonovani dnu na SERVERU - hlasilo "prekracujes narok o 3 dni". Nova pomocna funkce
  _dny sklonuje spravne (1 den, 2 dny, 5 dni, 1,5 dne).
- Sklonovani dnu v MOBILU - zivy nahled mel natvrdo dni, takze u jednodenni zadosti
  vyslo "zadas 1 dni". Doplnena tataz logika i do JS (funkce _jed ve fragmentu 50).
  Nalezeno az prokliknutim, z API to videt nebylo.

## NALEZ - pojistka g2007-soubor-vs-git je ZASTARALA (neopravoval jsem, neni moje)
Pojistka hlida, ze zadny artefakt v g2007.soubor nezustal starsi nez 24 hodin - vychazi
z toho, ze publikovany artefakt se ma zaroven commitnout do gitu, jinak dirty working tree
zablokuje deploye celemu tymu (incident 5. 8. 2026, dochazka-opravy.html).
JENZE od 5. 8. 2026 plati opak - slozka apps/api/static_db/ je v .gitignore a artefakty
se do gitu ZAMERNE necommituji (overeno, git ls-files nad tou slozkou vraci nula souboru).
Pojistka proto hlasi false trvale a nikoli kvuli skutecne chybe - k 17. 8. 2026 na ni
visi deset artefaktu z 5. az 12. 8. (foto.html, overit.html, marti.html, index.html,
dochazka-zakazky.html, martinky.html, registr-absenci.html, vyroba.html,
dochazka-po-zakazkach.html, dochazka-opravy.html).
Pojistka neni moje, tak jsem do ni nesahal - patri autorovi, at rozhodne, jestli ji
upravit na novy stav, nebo zrusit. Zapisuji to sem, aby to priste nekdo neresil znovu
jako novy nalez a hlavne aby si to nikdo nespletl se skutecnou chybou.

## Druhy trvaly nalez pojistky - absence-bez-duplicit
Hlasi false kvuli Kristyne Maresove, 30. 6. 2026, sickday 12 h na jeden den.
Je to ZNAMA VEC, popsana primo v kodu att_narok_cerpani (v datech se muze vyskytnout
dvoji zaznam na tyz den - skutecna absence plus planovana z Centraly se source plan_ec,
priklad Maresova 30.6.). Neni to nasledek prace ze 16. a 17. 8.

## Stav gitu k zaveru prace
Vsechny zmeny jadra jsou zacommitovane a odeslane - 98c5f776 (rozpad dovolene),
c529208e (oprava deep-linku karty), 2487f94f (nahledovy endpoint). Pracovni strom je
cisty a vetev srovnana s originem.
Kod, ktery zije v DB (g2007.python a g2007.soubor), v gitu zamerne neni.

