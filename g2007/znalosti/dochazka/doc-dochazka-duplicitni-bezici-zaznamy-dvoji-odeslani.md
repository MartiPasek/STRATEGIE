# Dva bezici zaznamy naraz - appka posilala pichnuti dvakrat (26.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Co se delo

Cloveku mohly v `tenant.att_entry` vzniknout **dva bezici zaznamy naraz** (`is_active=true`).
Den pak pokracoval po jednom z nich, druhy **osirel** a bezel az do pulnocniho
`att_auto_checkout_midnight`. Clovek mel v dochazce hodiny navic.

**Nalezeno 26.8.2026** (zadal Jirka Honomichl po nalezu u Martina Noska), oprava schvalena
Marti-AI (msg 13796, 13800).

## Pricina - dve vrstvy

**1. VZNIK: appka poslala pozadavek dvakrat.**
Zmereny odstup mezi obema zaznamy: **Blaha 33 ms, Nosek 36 ms** - to clovek prstem netukne
(lidsky dvojklik ~100-150 ms). Dalsi pripady 41-63 ms (taky strojove), vetsina zbylych
200-1000 ms (tam uz dvojklik byt muze). **Jsou to dva jevy, ne jeden.**

Zdroj v `g2007.soubor`:
- `60_dochazka.js` -> `function act(ep, payload, b, after){ b.disabled=true; api("POST",...) }`
  - tlacitko sice zakazovala, ale **nikdy nekontrolovala, jestli uz zakazane bylo**. Kdyz se
    `act()` spustila dvakrat z tehoz kliknuti (dva navesene listenery / touchend+click
    "ghost click"), obe volani probehla synchronne a odesla dva POST.
- `71_plan_prace_cinnosti.js` -> `window._praceStart` (tlacitko "Makat") - ochranu **nemela zadnou**.

**2. OSIRENI: kazda funkce si brala JINY bezici zaznam.**
- `att_checkin` v8: `... WHERE is_active=true` + `.first()` **BEZ ORDER BY** (nedeterministicke)
- `att_checkout` v9 a `att_do_att_action` v7: `ORDER BY id DESC LIMIT 1`
- `att_apply_work_selection` v4: `ORDER BY a.id DESC LIMIT 1`

Proto u Blahy 25.8. checkout ve 12:05 zavrel **novejsi** 10011310 a sirotka 10011309 nechal
bezet; ve 12:28:46 checkin se `switch=true` pres `.first()` trefil **sirotka** misto probihajici
pauzy, zavrel ho a zalozil navazujici 10011519, ktery dojel do pulnoci (11,52 h).

## Dopad - jmenovite

Duplicitni zalozeni od 29.6.2026 **29x u 21 lidi**. Skoda v hodinach u **ctyr**:
- **Martin Nosek** 25.8. - 11,58 h (Jirka stornoval 26.8.)
- **Tomas Blaha** 25.8. - 3,87 h + 11,52 h (**neopraveno**, viz nize)
- **Lucie Jakesova** 22.7. - 12,90 h (**neopraveno**)
- **Marti Pasek** 30.6. - 1,08 h (**neopraveno**)

Pred cervnem 2026 se to nestalo ani jednou. Miry: cerven 5,6 / cervenec 3,8 /
**srpen 10,5 duplicit na 1000 pichnuti** - srpnovy narust tedy NENI jen tim, ze se vic picha.
Proc miry v srpnu vyskocily, **neovereno**.

**POZOR u Blahy:** rozpad prace (`tenant.vyroba_work`) se navazal **vyhradne na osirelou vetev**,
takze dochazka a rozpad jedou po dvou ruznych vetvich (dochazka 08:13-12:05, rozpad 08:13-12:28).
Prosty storno zaznamu by cloveka pripravil o rozpad. Marti-AI: retrospektivni oprava
historickych pripadu **rucne per pripad, nikdy skriptem**.

## Co uz je nasazeno (bod D, 26.8.2026)

Do obou dilku pridan strazce + casova pojistka (schvalila Marti-AI msg 13800):
```js
// 60_dochazka.js, act():
function act(ep, payload, b, after){ if(b && b.disabled) return; setTimeout(function(){ if(b) b.disabled=false; }, 10000);
// 71_plan_prace_cinnosti.js:
window._praceStart=function(){ if(window.__praceBusy) return; window.__praceBusy=true; setTimeout(function(){ window.__praceBusy=false; }, 10000);
```
Pojistka 10 s je proto, aby clovek nezustal zablokovany, kdyby odpoved nedorazila.
Dilky 60_dochazka.js v17->18, 71_plan_prace_cinnosti.js v8->9, artefakt mobile.html v64->65
(+202 znaku). Overeno na zive `/mobile`: HTTP 200, oba strazci prave jednou, 30 skriptovych
bloku beze zmeny.

## Co uz je nasazeno (bod A1, 26.8.2026 v 09:48)

`att_checkin` v8 -> **v9** (otisk `4a2c349ca58514b88abea195dfdd5423`, 15428 bajtu).
Dve zmeny, obe schvalila Marti-AI (msg 13802 a 13805), pustil Jirka Honomichl:

1. **Deterministicke poradi** - puvodni `.first()` BEZ `ORDER BY` doplneno na
   `... AND a.is_active=true ORDER BY a.id DESC"), ... .first()`, takze se bere posledni
   akce cloveka, ne libovolny zaznam.
2. **Uklid soubeznych zaznamu** - novy blok hned za tim, pred `switching = False`:
   uzavre k `now()` vsechny ostatni bezici zaznamy s poznamkou `[uzavren jako soubezny zaznam]`.
   **Dve pojistky (obe od Marti-AI):** `AND entry_date = current_date` (na vcerejsek saha
   `_att_close_stale`, at se nedokonceny vcerejsek neoznaci mylne jako soubezny) a
   `AND started_at < (SELECT started_at ... WHERE id=:hid)` (kdyby byl sirotek novejsi
   nez hlavni, nesahat na nej).

**Sirotek tedy uz nedojede do pulnoci** - zmizi pri nejblizsim pichnuti toho cloveka.

**Overeni pred zapisem** (postup, ktery se vyplati zopakovat): vysledek spocitan NANECISTO
`SELECT`em, stazen pres base64 po 6000 bajtech, **otisk lokalni kopie porovnan s otiskem
na serveru** (sedely), `python -m py_compile` prosel, a kontrolou overeno, ze v souboru
zustaly vsechny puvodni casti (`_att_close_stale`, `_att_unconfirmed_days`, `need_confirm`,
`ec_close_open_shift`, `ec_vypni_dochazku`, `_wa_open`, `att_apply_work_selection`,
`already_open`). Teprve pak zapis.

**Overeni po nasazeni:** v `fw.diag_log` zadna nova chyba. **Ostry test 09:55:03** - Zdenek
Divis prepnul na Rezii; usek 09:17-09:55 se uzavrel, novy navazal na vterinu, bezi mu JEDEN
zaznam. Je to presne to misto, kde to Blahovi 25.8. selhalo. Pri nasazeni se nikomu nic
neuzavrelo (dva bezici zaznamy nemel v tu chvili nikdo).

> **PAST, na kterou jsem narazil:** `g2007.python` ma **unikatni klic na `kod`**
> (`python_kod_key`), takze u EXISTUJICI funkce **nelze mit `navrzeno` vedle `active`** -
> `INSERT` nove verze skonci `UniqueViolation`. Doktrina "vloz jako navrzeno, po lidskem
> schvaleni aktivuj" plati jen pro NOVY kod; u existujici funkce se nova verze zapisuje
> rovnou na misto stare. Nahrada je postup s otiskem popsany vyse.
>
> **ROZHODNUTI: historii verzi u `g2007.python` NEZAVADIME.** Rozhodl Jirka Honomichl
> 26. 8. 2026. Zustava tedy jeden radek na jeden kod a nova verze prepisuje starou;
> pojistkou je postup s otiskem (spocitat nanecisto, stahnout, porovnat md5, prelozit,
> teprve pak zapsat) a `git log` nad projekci `g2007/`. Nepredelavat bez jeho souhlasu.

## Co uz je nasazeno (body B2 a C, 26.8.2026)

**B2 - pojistka primo v databazi.** Spoustec `att_entry_jeden_bezici` na `tenant.att_entry`,
BEFORE ZALOZENI, plus funkce `tenant.att_entry_jeden_bezici()`. Uzavre ostatni bezici zaznamy
tehoz cloveka s poznamkou `[uzavren spoustecem - novy bezici zaznam]`; stejne dve pojistky
jako A1 (`entry_date = NEW.entry_date`, `started_at < NEW.started_at`) a `GREATEST(...,0)`
proti zapornym hodinam. Chyti i cesty, kam `att_checkin` nedosahne (opravy, import).
Nasazeno pres most (request 2492, schvalil Jirka), protoze most bezi pod enginem Marti-AI,
ktera tabulku vlastni. **Nezpomaluje**: dotaz spoustece 1000x = 54 ms, tedy pod 0,05 ms na
jedno pichnuti - v tabulce je index `IDX_att_entry_tenant_id_employee_id_entry_date`, ktery
presne odpovida jeho WHERE.

**C - hlidac.** Novy druh `dva_bezici_naraz` v `att_anomaly_scan` v7 -> **v8** (otisk
`e8c7d9cfb499c0c45bff1b2ac8b0d126`), vcetne vlastniho uklidu (nalez zmizi, jakmile clovek
uz dva bezici zaznamy TEHOZ DNE nema - filtr na den si vyzadala Marti-AI msg 13826).
`entry_id` je `min(e.id)`, aby nalez nevisel na radku, ktery A1 nebo B2 mezitim uzavre.
Slo do `att_anomaly_scan`, NE do `tenant.pojistka` - pojistky nikdo nespousti, kdezto
notifikace z anomalii prokazatelne dojdou (26.8. 07:22 upozorneni -> 08:42 Petra zasahla).
Overeno: kontrola po nasazeni probehla v 11:16:29 a uklidila 12 nalezu, takze v8 bezi.
Zatizeni 200 behu = 72 ms.

## Co jeste zbyva

- **A2** (A1 je hotova, viz vyse) - jedna SDILENA funkce "vrat bezici zaznam", volana ze vsech
  osmi mist, ktera dnes resi `is_active=true` (`att_checkin`, `att_checkout`,
  `att_apply_work_selection`, `att_do_att_action`, `att_dovolena_kaskada`, `att_fix_entry`,
  `att_prazdny_den_fond`, `sync_ec_dochazka_recent`). Jirka 26.8. rozhodl NEdelat ji zaroven
  s A1: A2 saha na pichani vsech lidi naraz, takze jde jako samostatny uklid na klidnejsi dobu.
## Rucni oprava historickych pripadu - stav k 26.8.2026

- **Martin Nosek 25.8. - HOTOVO.** Osirely zaznam (12:24-23:59, 11,58 h) stornoval Jirka Honomichl.
- **Lucie Jakesova 22.7. - HOTOVO.** Zaznam 9858417 (11:05-23:59, 12,90 h) stornoval **Dusan Havlat
  uz 23.7.2026** s poznamkou "chybny typ zaznamu", status `superseded`. Do hodin se nepocita.
  Kdo by opravoval podle seznamu naslepo, opravoval by uz opravene.
- **Marti Pasek 30.6. - NENI TO PRAVA DUPLICITA.** Zaznam 6992178 (22:54-23:59, 1,08 h) je
  **zapomenute odhlaseni** uzavrene pulnocnim automatem, ne dva soubezne bezici zaznamy.
  Ten den ma navic vedle 12 h prace i schvalenou dovolenou 8 h - samostatna vec, neresena.
- **Tomas Blaha 25.8. - CASTECNE, DORESUJE DUSAN HAVLAT.** Jeho pripad byl nejtezsi, protoze
  rozpad prace visel VYHRADNE na osirele vetvi (dochazka 08:13-12:05 vs rozpad 08:13-12:28).
  **Co rekl clovek** (zjistil Jirka primo u Blahy 26.8.): ve 12:05 sel na pauzu, **ve 12:28 se
  vratil a PRACOVAL**, ve 12:47 prepichaval na jinou praci. Cas 12:28 z rozpadu tedy byl SPRAVNY,
  chybny byl jen konec useku.
  **Co se stalo:** Dusan Havlat 26.8. v 11:19 zaznam 10011519 (12:28-23:59) **stornoval celý**
  s poznamkou "omylem zalozeny zaznam" - tim ale zmizela i skutecna prace 12:28-12:47 a jeji rozpad.
  **Co na tom dni zustalo neopravene** (stav 26.8. 11:25): duplicitni 10011309 (08:13-12:28,
  4,25 h) je porad `pending` vedle spravneho 10011310 (08:13-12:05, 3,87 h); pauza 10011498 je
  12:05-**12:47** misto do 12:28; rozpad 26861 (4,250 h) visi na duplicite. Den vykazuje **12,61 h**
  misto ~7,89 h. Navic Blaha rozporuje odchod: u 10011530 je "✋ ROZPOR: Odchod 13:00" (ne 13:12).
  **Rozhodl Jirka Honomichl 26.8.2026:** kdyz to Dusan zacal opravovat sam, dokonci to on -
  Claude do toho uz nesaha. Pripraveny (a Marti-AI schvaleny msg 13829) navrh opravy byl:
  stornovat 10011309, rozpad 26861 prepojit na 10011310 a zkratit na 12:05 (3,867 h), pauzu
  zkratit na 12:05-12:28 (0,38 h), usek 12:28 zkratit na konec 12:47 (0,32 h) vcetne rozpadu 26932
  (0,317 h) - vse v JEDNE transakci. Soucet by sedel na 7,88 h proti 7,89 h z rozpetí dne.

**Poucen pro pristi opravy** (Marti-AI 26.8.): pred zapisem overit nejen `status='pending'` a
prazdnou `fakturace_at`, ale i **uzamceni mesice** a **potvrzeni dne** (`att_day_confirm`) -
Blahuv den 25.8. uz potvrzeny JE. A hlavne: **overit stav tesne pred zasahem**, ne podle analyzy
z rana - mezi mou analyzou (09:14) a pripravou opravy (11:23) do dne zasahl Dusan.

## Mapa zapisovatelu do att_entry (stav 26.8.2026)

34 zivych funkci v `g2007.python`, z toho **19 zaklada** zaznam a **8 pracuje s bezicim**.
Import z Centraly (`source_system='centrala1'`) **od 11.8.2026 uz nezapisuje** - sync byl
ukoncen a v Centrale uz nikdo nepicha (Jirka 26.8.: "import z centraly by uz nikdy nemel bezet").
Dnes zapisuji: `mobile_app`, `automat`, `manual_fix` (opravy Petry), `absence`, `notif_confirm`.

## Gotcha na pristi vysetrovani

**Zadny log HTTP pozadavku pro tuhle cestu neexistuje.** `fw.diag_log` loguje jen chyby
(0 zaznamu s 2xx), `g2007.python_run_audit` skripty `att_*` neaudituje, `tenant.att_audit`
je pro tyhle dny prazdna. Cestu slo dohledat jen z otisku v datech (shodne `updated_at`
puvodniho a `created_at` noveho zaznamu na mikrosekundu = jedna transakce). Kdyby to melo jit
dohledat primo, muselo by se zapnout `python_run_audit` pro `att_*` (umi ulozit i `args`),
nebo rozsirit `fw.diag_log` o 2xx u zapisujicich `/app/attendance/*`.

