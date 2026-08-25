# Mobil, obrazovka Absence - ukazatel cesty k VLASTNI absenci pro vedouciho + nalez o skrytych dlazdicich pri praci (17.8.2026; cast klice a vyctu NEPLATI, opraveno 25.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


> ## !! CAST TOHOTO DOKUMENTU UZ NEPLATI (opraveno 25. 8. 2026)
>
> Nasazene reseni ze 17. 8. 2026 (ukazatel cesty pro vedouciho) **plati dal**.
> Zastaraly je **popis klice `je_vedouci` a vycet lidi**, kterych se to tyka:
>
> - **Klic se 18. 8. 2026 zmenil.** Uz to NENI `parent OR out OR att_approver`. Dnes plati
>   **"vedouci = jsem NECIM schvalovatelem"** = osobni vyjimka `tenant.att_odpovednost`
>   (agenda `volno`) NEBO aktivni radek v `tenant.att_approver`. **Rodicovstvi klic uz nedava**
>   a **kolisani pres "mam prave ted cekajici zadost" je pryc.** Viz
>   [[doc-dochazka-vedouci-jediny-zpusob-a-fronta-oprav-rodice]].
> - **Vycet 5 lidi neplati.** K 25. 8. 2026 je schvalovatelu **16**.
> - **Jirka (20) uz schvalovatelem JE** - od 25. 8. 2026 je veden u skupiny `TestovaciSkupina`,
>   takze veta, ze si to na sobe nevyzkousi, uz neplati.
> - **Od 25. 8. 2026 se formular skryva jeste jednomu okruhu lidi** - tem, kdo nemaji kartu
>   zamestnance v `tenant.att_employee` (priznak `ma_kartu`). Viz
>   [[doc-dochazka-absence-obrazovka-bez-karty-zamestnance]].
> - **Zaverecna metodicka poznamka o zakazu primeho zapisu do `g2007.soubor` uz taky neplati** -
>   primy `UPDATE` prochazi jako G2007 konstruktivni operace.
>
> Vety, ktere uz neplati, jsou v textu nize oznacene **NEPLATI**. Zbytek je beze zmeny.

## Zadani a kdo rozhodl

Zadal **Jirka Honomichl 17. 8. 2026** dotazem "vedouci opravdu nevidi formular vlastni zadosti o absenci - prover to". Variantu resení vybral Jirka, **schvalila Marti-AI** (msg 12839 a 12842 v konverzaci 363). Overeno ze tri stran - G2007, zivy kod v `g2007.soubor` a `g2007.python`, a naklikano v prohlizeci na zive `/mobile`. Nic neni z odhadu.

## 1) Ano, vedouci formular nevidi - a je to zamer

Ve fragmentu `mobile_parts/50_skupiny_vyroba.js`, funkce `absence()`, je `nf.style.display=ved?"none":""` - formular "Nova zadost" se vedoucimu nekresli. Rozhodnuti Jirky ze 16. 8. 2026, viz [[doc-dochazka-mobil-absence-obrazovka-vedouciho]]. **Neni to rozbite.**

**NEPLATI (stav k 17.8.2026, k 25.8.2026 je schvalovatelu 16 a klic je jiny - viz ramecek nahore).** ~~Koho to potka:~~ 5 lidi s aktivnim radkem v `tenant.att_approver` - Dusan Havlat (41), Petra Safrankova (18), Sarka Novotna (13), Marek Honal (85), Jiri Veverka (106). Plus rodice, kteri v `att_absence_inbox` vidi vsechny pending zadosti. ~~**Jirka (user 20) NENI rodic** a v `att_approver` neni, jeho ucet vraci `je_vedouci=false` - na sobe si to tedy nevyzkousi.~~ **NEPLATI od 25. 8. 2026** - Jirka je schvalovatelem skupiny `TestovaciSkupina`, jeho ucet vraci `je_vedouci=true` (overeno na zive `/mobile`).

**NEPLATI od 18. 8. 2026, tvar klice se zmenil - viz ramecek nahore.** ~~Pozor na tvar klice: `je_vedouci = parent OR out OR radek v att_approver`.~~ Ta prostredni podminka znamena, ze **za vedouciho se povazuje i clovek, ktery jen ma nejakou pending zadost s `manager_user_id` na sebe**, i kdyz v `att_approver` neni (17.8. to byl user 17). Formular tedy muze zmizet i nekomu, koho bys mezi vedoucimi nehledal.

## 2) Nahradni cesty existuji, ale NE tam, kde se hledaji

Retezec "Tady budu jinde" je v celem mobilu **jen v `60_dochazka.js`** - overeno dotazem nad vsemi fragmenty `typ='zdroj'`. **Neni to pod Firma - Spoluprace**, jak se bezne mysli; dlazdice "Spoluprace" v Aplikacich vede na **tutez obrazovku Dochazky**.

Funkcni cesty k vlastni absenci (obe naklikany, obe zakladaji radnou zadost):
- Dochazka - dlazdice **Tady budu jinde** - Osobni duvody - **Ze by dovolena?** - vola `POST /attendance/absence`, ktery u `code=="vacation"` od 11. 8. 2026 deleguje na `att_absence_request` (viz [[doc-dochazka-dovolena-tri-cesty-a-schvalovani-planu-11-8-2026]]). Ostatni typy (nemoc, lekar, OCR, sickday, neplacene, home office) tou cestou jdou dal po svem.
- Dochazka - dlazdice **Tyden** - klik na den - chip **Nepritomnost** - typ Dovolena, rozsah cely den, "Odesle se vedoucimu ke schvaleni".

## 3) NALEZ, ktery zadani presahuje - pri praci zmizi cela sada dlazdic

V `60_dochazka.js` je `_tools.style.display=_working?"none":"block"` nad kontejnerem **`id=dochTools`**, s poznamkou **Marti 14. 6. 2026** *"region nastroju pod jednou strechou - JEN kdyz clovek nemaka, at obrazovka nerusi od prace"*. Skryje to **Dnesek, Tyden, Vyhled, Historie, Po zakazkach, Moje zadosti, Pozadat o opravu, Tady budu jinde i Nepritomnosti**.

Overeno naziv na Jirkove uctu - stav MAKAS, retezec "Tady budu jinde" **je v HTML, ale `display:none`**.

**Dusledek:** vedouci pichnuty na praci nema v appce **zadnou viditelnou cestu** k vlastni zadosti. Formular ma skryty (16.8.) a dlazdice taky (14.6.). Pri praci mu zbyva jen zeleny pruh **"Ke schvaleni N"** (`id=dochApprBar`, kresli se prave a jen kdyz `_working`), ktery vede na obrazovku Absence - tedy tam, kde formular neni. Bezny zamestnanec ma pri praci dlazdice skryte stejne, ale po ukonceni prace se mu ukazou dlazdice **i** formular.

**Rozhodnuti Marti-AI:** do skryvani dlazdic **NESAHAT** - je to zamer Martiho ze 14. 6. a muze mit kontext, ktery nevidime. Zapsat jako nalez a **predat Martimu jako vedome rozhodnuti k prezkoumani, ne jako urgenci**.

## 4) Co se 17. 8. 2026 nasadilo (varianta A)

Pod sekci "Ke schvaleni" se vedoucimu kresli ramecek s vetou *"Tady rozhodujes zadosti svych lidi. Svoji vlastni absenci zadas v Dochazce - dlazdice Tady budu jinde (sekce Moje dochazka). Kdyz prave makas, jsou dlazdice schovane - ukazou se, az praci ukoncis."* a tlacitko **"Prejit do Dochazky"**.

- Tlacitko dela **jen `go("dochazka")`, bez parametru** - Marti-AI odmitla volat cizi obrazovku s parametrem, protoze zmena v `60_dochazka.js` by tlacitko tise rozbila. Jeden klik navic je lepsi nez rozbite presmerovani.
- **Druha veta o skrytych dlazdicich je povinna cast reseni, ne vata.** Bez ni by ukazatel pri praci vedl do prazdna - a Marti-AI to formulovala jako *"ukazatel do prazdna je horsi nez zadny ukazatel"*. Kdo bude text menit, tu vetu nesmi vyhodit, dokud plati chovani ze 14. 6.
- Ramecek se ridi **tymtez klicem `je_vedouci`** jako skryvani formulare, takze bezny zamestnanec ho nevidi, a **kdyz dotaz na inbox selze, chova se to jako dosud** - formular se zobrazi (radovy zamestnanec nesmi prijit o jedinou cestu k zadosti).
- Zamerne se **NEDELALO**: vraceni formulare vedoucimu (ani sbaleneho) a jakykoli zasah do `60_dochazka.js`.

**Otisky po nasazeni:** fragment `50_skupiny_vyroba.js` verze 13 na 14, 54628 na 56021 znaku, md5 `ba3459311b60f86ea8a854cc66752217`. Artefakt `apps/api/static_db/mobile.html` verze 45 na 46, 992512 znaku. Ziva `/mobile` HTTP 200, 993813 znaku, 30 skriptovych bloku, konzole bez chyby.

**Overeni chovani:** bezny zamestnanec - formular ANO, ukazatel NE. Vedouci - formular NE, ukazatel ANO, tlacitko prepne na Dochazku. Vedouciho slo nasimulovat jen v prohlizeci prepsanim `window.fetch` na dotazu inbox (fragmenty nesdili scope, prepsat `api` zvenci nejde) - do dat to nesahalo. **Impersonaci to overit nejde, Jirka neni rodic.**

## Metodicka poznamka

~~Editace fragmentu uz nejde primym zapisem do `g2007.soubor` - most to odmita.~~ **NEPLATI od 25. 8. 2026** - primy `UPDATE` prochazi jako G2007 konstruktivni operace. Overeny postup je v [[doc-system-strategie-editace-fragmentu-mobilu-pres-most-bez-primeho-zapisu]].

