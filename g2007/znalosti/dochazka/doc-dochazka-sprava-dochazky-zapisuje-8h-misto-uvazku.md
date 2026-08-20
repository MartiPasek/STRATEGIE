# Sprava dochazky zapisuje absenci 8 h natvrdo, i lidem se zkracenym uvazkem (nalez 17.8.2026, ceka na Petu)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


# Sprava dochazky zapisuje absenci 8 h misto denniho fondu

**Nalez Claude-28, 17. 8. 2026.** Rozhodnuti Marti-AI: **NEOPRAVOVAT ZATIM** - patri to
do prace Peti (Claude-26), ktera prave dela na "Absence hodiny/dny - sjednoceni cisla
ve vsech pohledech". Zapsano proto, aby to neresil kazdy zvlast.

## Co se deje
Kdyz se absence zadava ve **Sprave dochazky**, hodiny na den se berou z formulare
s natvrdo nastavenou osmickou:

`hpd = float((b or {}).get("hodin_den") or 8)` - `modules/erp/api/dochazka_absence_sprava.py:845`
(a stejne na radku 715 pro druhou cestu).

Formular **necte denni fond cloveka** (`engagement.uvazek_tyden_h` / `work_mode.dny_v_tydnu`).
Kdo ho neprepise rucne, zapise cloveku se zkracenym uvazkem o hodinu vic, nez ma.

## Dolozeny dopad
- **Zuzana Duspivova** (uvazek 7 h/den): zadost c. 78 z 11. 8. 2026 (zadala Petra Safrankova)
  zapsala 10.-14. 8. peti dny po 8 h = **5 h dovolene navic**, ktere ji system ukusoval.
  Opraveno 17. 8., viz `doc-dochazka-oprava-duplicity-maresova-a-uvazku-duspivova-17-8-2026`.
- **Petra Safrankova to uz od cervence opravuje rucne** - v poznamkach starsich zaznamu
  teze osoby stoji " / OPRAVA (Petra Safrankova) absence podle uvazku 7.00 h (puvodne 8.00 h)".
  Rucni oprava po kazdem zadani je priznak, ze vada je ve formulari, ne v datech.

## Na co nezapomenout pri oprave
Opravit **jen zapis do `att_entry` nestaci**. Hodnota se drzi i v
`tenant.att_absence_request.hours_per_day` a funkce `_prepis_zadost`
(`dochazka_absence_sprava.py:495`) pri prepoctu att_entry te zadosti smaze a zapise znovu
z toho pole. Kdo opravi jen vysledek a ne zdroj, ten opravu ztrati pri prvnim prepoctu.

Podobna vada s jinym zdrojem (plan nepritomnosti z Centraly) je popsana v
`doc-dochazka-planovana-absence-hodiny-dle-uvazku` - **je to jina cesta, netahat to dohromady.**

## Stav koordinace k 17. 8. 2026 (CEKA SE NA PETU)
Jirka pozdeji rekl, ze to chce opravit. Pred zasahem jsme overili `fw.claude_instance`
a **Peta (C-26) ma `modules/erp/api/dochazka_absence_sprava.py` primo uvedeny ve sve
rozdelane praci** - tedy presne ten soubor. Nic jsme proto nezmenili a zeptali jsme se
tremi cestami:
1. **`@@COORD POST` polozka c. 30** (priorita 1) - dotaz pro Claude-26.
2. **E-mail** Petre Safrankove (`p.safrankova@eurosoft.com`, kopie `petra@eurosoft.com`
   a Jirka), odeslano 17. 8. v 9.14, potvrzeno stavem `sent` v `email_outbox` 632.
3. **Push notifikace** na mobil Petre (user 18).

Polozeny tri otazky: (a) resi to uz nebo to ma v planu, (b) jestli to mame vzit my
a ceho se nedotknout, (c) jaka varianta - server si vezme denni fond, kdyz formular nic
neposle, NEBO se spravna hodnota predvyplni uz ve formulari podle vybraneho cloveka.

**Do odpovedi se nemeni nic.** Pozn.: nastenka `@@COORD` neni spolehlivy kanal - dotaz
Claude-28 c. 29 z 11. 8. 2026 na ni zustal nezodpovezeny; proto ten e-mail navic.

