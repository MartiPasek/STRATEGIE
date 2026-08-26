# Nemoc, OČR a lékař z mobilu = jen informace vedoucímu, do docházky nic

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Pravidlo (Peťa 19. 8., 24. 8., 25. 8. a závazně 26. 8. 2026)

Když člověk z mobilní aplikace nahlásí **nemoc, OČR nebo lékaře**, jde to **POUZE jako informace vedoucímu**. Do docházky ani do žádostí se nezapisuje **NIC**.

Peťa doslova (25. 8. 2026): *„když někdo z mobilu nahlásí nemoc, NIKAM se to nezapisuje, jde info jen vedoucímu, do správy se to zapíše ručně na základě dokladu."* A dál: *„apka to nemá umět zapisovat nemoc, protože to nechceme přece."*

Dřív (19. 8. 2026): *„ano vedoucímu má přijít pouze info, že ten člověk jde k lékaři nebo že je nemocen."*

- **Nemoc a OČR** zapisuje Peťa ručně ve **Správě docházky** až podle dokladu (neschopenka, potvrzení).
- **Lékař** je zatím taky jen info. Jeho logika (přednostní čerpání sick day, strop 4 hodiny) se **předělá po domluvě s Martim** — do té doby pozastaveno. Peťa 26. 8. 2026- *„lékaře musíme řešit individuálně, bude fungovat jinak po domluvě s Martim."*
- Člověk v mobilu dostane **„Nahlášeno vedoucímu"**, vedoucí prostou zprávu na vědomí (bez tlačítka schválit).

## Proč se to řešilo čtyřikrát

Rozhodnutí padlo poprvé 19. 8. a pak ještě třikrát — ale **nikde nebylo zapsané**. V plánu z 24. 8. 2026 byl bod „zapsat rozhodnutí do G2007", který se neudělal; 25. 8. se zapsal jen home office. Každá nová instance to proto objevovala znovu a Peťa to musela vysvětlovat pokaždé od začátku.

**Poučení-** dokud rozhodnutí není v G2007 a v pojistce, neexistuje.

## POZOR- jsou TŘI mobilní vstupy, ne jeden

Kdo opravuje jen jeden, nechá díru ve dvou zbylých.

| Vstup | g2007.python | Co dělal do 26. 8. 2026 |
|---|---|---|
| „Tady budu jinde" | `att_absence` | zapsal rovnou do docházky (att_entry) s hodinami = denní fond |
| Žádost o nepřítomnost | `att_absence_request` | založil žádost, schválení ji zapsalo do docházky |
| „Je mi blbě, dnes nedorazím" | `att_announce` | z volného textu poznal nemoc a **založil žádost na 8 hodin** |

Třetí je nejzákeřnější- člověk jen napíše, že mu není dobře, a systém z toho udělal nemoc. Rozpoznávání typu z textu dělá `att_announce_absence_typ`.

**Správa docházky má vlastní cestu** (`modules/erp/api/dochazka_absence_sprava.py`, funkce `_zapis_dny` se zdrojem `manual_fix`) — ta s mobilem nesouvisí a **ruční zápis podle dokladu zůstává beze změny**.

## Co se změnilo 26. 8. 2026 (Peťa + Claude-26)

Ve všech třech skriptech přibyla stejná podmínka na typy `("sick", "family_care", "medical")`-

- `att_absence` — `_upsert` pro tyto typy nezapíše nic; navíc se pro `medical` už nevolá `sickday_lekar_apply` (není z čeho čerpat) a hláška vedoucímu říká „Jen na vědomí" místo „čeká na schválení".
- `att_absence_request` — nezaloží žádost, jen pošle info vedoucímu a vrátí `info_only`.
- `att_announce` — nezaloží žádost, jen pošle info vedoucímu.

Zálohy původních verzí- `att_absence__zaloha_20260826`, `att_absence_request__zaloha_20260826`, `att_announce__zaloha_20260826`.

Hlídá **pojistka `nemoc-ocr-lekar-z-mobilu-jen-info`**.

## Dopad na existující data

Z mobilu takto vzniklo málo záznamů, ale vznikaly- nemoc 1x (Navrátil 31. 7. 2026), OČR 2x (Kristý, červen 2026), lékař 19x (Erika, Peřina, Honomichl, Zuzka, Horký). Staré záznamy se **nemažou**, pravidlo platí dopředu.

## Související pravidlo (Peťa 26. 8. 2026)

*„Když něco schováváme, tak proto, že to tam nemá být — a nemá se s tím nic dít ani na pozadí."*

Vzniklo u ohlášení home office- schovali jsme ho z obrazovek filtrem, ale řádek v `att_entry` zůstal a automat na ten den pouštěl přepočet doplnění do fondu. Reálnou škodu to nedělalo (ohlášení nemá hodiny, do výpočtu nevstupuje), ale pouštět se nemělo. Opraveno- přepočet se v `att_absence` pouští jen když se opravdu něco zapsalo a nejde o home office. Hlídá pojistka `prepocet-jen-kdyz-se-neco-zapsalo`.

