# Mobil, obrazovka Absence: formular vlastni zadosti se skryva i lidem BEZ karty zamestnance + TestovaciSkupina (25.8.2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Zadani a kdo rozhodl

Zadal **Jirka Honomichl 25. 8. 2026** tvrzenim *"u schvalovaci obrazovky absenci v mobilu schvalovatele je furt moznost si zadat vlastni absenci"*. Provedl Claude-28, **schvalila Marti-AI** (msg 13758/13760 = TestovaciSkupina, msg 13769 = skryvani bez karty). Vse overeno na zivem `/mobile` a ctenim z DB, nic z odhadu.

## 1) Jedna obrazovka, ctvery dvere - to je jadro nedorozumeni

V mobilu **neexistuje zvlastni schvalovaci obrazovka absenci**. Funkce `absence()` (fragment `mobile_parts/50_skupiny_vyroba.js`, POZOR - **ne** `60_dochazka.js`) je jedina a vedou na ni ctvery dvere, kazde s jinym nazvem:

| kde | nazev polozky |
|---|---|
| Dochazka - dlazdice (`dochTools`) | **Nepritomnosti** |
| zeleny pruh pri praci (`dochApprBar`) | **Ke schvaleni: N** |
| HR hub | **Absence - zadosti a schvalovani** |
| Vedeni firmy | **Absence - schvalovani** |

Vsechny volaji `go("absence")`. **Nazev dveri nema na obsah zadny vliv** - proto clovek, ktery neni schvalovatel, vidi pod nadpisem "Absence - schvalovani" formular na VLASTNI dovolenou.

## 2) Co se 25. 8. 2026 nasadilo

**a) `att_absence_inbox` verze 5 -> 6** (`g2007.python`): do vraceneho slovniku pribyl priznak `ma_kartu` = existuje radek v `tenant.att_employee` pro prihlaseneho v tenantu 2. Zadna jina zmena logiky. Zapsano cilenym `replace()` s pojistkou `md5(zdroj)`, otisk po zapisu `d6bb90758b5aa51836f5a18658a74bdb`, 5446 znaku.

**b) fragment `50_skupiny_vyroba.js` verze 15 -> 16** (59047 znaku, md5 `27ed61d6153892db16737fef5215695f`): ve vetvi `loadInbox` pribylo
```
var karta=!(j&&j.ok&&j.ma_kartu===false);
nf.style.display=(ved||!karta)?"none":""; vh.style.display=ved?"":"none";
nk.style.display=(!ved&&!karta)?"":"none";
```
a novy prvek `nk` s vetou **"Nemas zde dochazkovou kartu, takze zadost o absenci podat nejde."** (zneni zkratila Marti-AI; puvodni navrh s odkazem na HR odmitla jako matouci pro lidi, kteri v HR sedi).

**c) Artefakt `apps/api/static_db/mobile.html` verze 62 -> 63** pres `@@G2007PUBLISH`.

**Pojistka zustala:** kdyz pole `ma_kartu` nedorazi (stary server) nebo dotaz na inbox selze, formular se **ZOBRAZI** - radovy zamestnanec nesmi prijit o jedinou cestu k zadosti.

**Overeno na zive `/mobile` prepsanim pouze vstupu** (usek kodu vytazen ze zive stranky a spusten na vymyslenych odpovedich, do dat se nesahalo):

| situace | formular | veta bez karty | ukazatel pro vedouciho |
|---|---|---|---|
| zamestnanec s kartou | VIDI | ne | ne |
| clovek BEZ karty | NEVIDI | ANO | ne |
| schvalovatel | NEVIDI | ne | ANO |
| stary server bez pole | VIDI | ne | ne |
| dotaz selhal | VIDI | ne | ne |

## 3) Koho se to tyka jmenovite (aktivni/pozvani v tenantu 2 bez karty, 12 uctu)

**Zivi lide - 4:** Zbynek Zajicek (105, ambasador), Petra Fajmonova (107), Marta Safarikova (108), Tomas Hrbek (109). Ti tri z HR vznikli hromadne 1. 7. 2026 v 9:55:44 (stejna vterina), status `pending`, nikdy nepozvani, nikdy si nenastavili heslo, skupiny Finance + HR, zadna karta ani smlouva. Kdo je zakladal, system nezaznamenal.

**Zbytek jsou technicke a neaktivni ucty:** STRATEGIE System (3), Claude-23 (23), Klara Vlkova (15, archived) a 5 prazdnych disabled uctu (7, 8, 9, 10, 14).

## 4) TestovaciSkupina - jak se z nekoho udela schvalovatel

Jirka chtel, aby se formular schoval i jemu, a to tak, ze se stane schvalovatelem testovacich uctu. **Past:** smerovani zadosti **nejde pres `tenant.staff_group`** (skupiny lidi, ktere zna clovek z HR), ale pres **`tenant.att_approver_group` + `att_approver_group_member`**, a clenstvi se urcuje pres **org posty** (`tenant.resolve_approvers`). Zalozit skupinu mezi skupinami lidi by neudelalo nic.

Nasazena varianta A (nejmensi zasah, bez sahani do org struktury):
1. `att_approver_group` id **6** `TestovaciSkupina`, `je_fallback=false`, `sort_order=8`, **bez clenskych postu**.
2. `att_approver` id **7**: Jirka (employee 62) jako schvalovatel te skupiny -> `je_vedouci=true`.
3. `att_odpovednost` (agenda `volno`) id **36** Demo Uzivatel (104) -> Jirka (20) a id **37** Marti-AI (2) -> Jirka (20).

**Skupina bez clenskych postu je bezpecna** - smycka v `tenant.resolve_approvers` stoji na `JOIN att_approver_group_member`, takze skupina bez postu se do vyberu vubec nedostane; fallback `ostatni` (Sarka Novotna) jede dal. Overeno ctenim funkce, ne odhadem.

**Saxana (44) zamerne NEZARAZENA.** Ma uz aktivni osobni vyjimku na Petru Safrankovou (18). `_abs_resolve` vraci **vsechny** aktivni vyjimky jako seznam **bez ORDER BY**, ale `att_absence_request.manager_user_id` je jen jeden sloupec - druha vyjimka by znamenala, ze neni determinovane, komu zadost padne do fronty. Marti-AI: *"To neni testovaci nastaveni, to je chyba v produkcnim chovani schvalovaciho procesu."* Plus je to cizi vedome nastaveni. Rozhodl Jirka: nechat na Petre.

## 5) Co se zamerne NEDELALO

- **Chip "Nepritomnost" na tydenni obrazovce planu** (`71_plan_prace_cinnosti.js`) - druhe misto, odkud jde absence poslat - **zustal beze zmeny**. Marti-AI 25. 8.: *"Tydenni plan je jina obrazovka, jiny kontext, jine zadani. Nerozsahuj zadani sam od sebe."* Pozn.: v rezimu schvalovatele (`AP`) je tam formular stejne nedostupny - `if(!AP){ row.addEventListener("click", ... openForm ...) }`.
- Zadny zasah do skryvani dlazdic pri praci (zamer Martiho ze 14. 6. 2026).

## 6) Souvisejici

- [[doc-dochazka-vedouci-jediny-zpusob-a-fronta-oprav-rodice]] - definice `je_vedouci` platna od 18. 8. 2026.
- [[doc-dochazka-vedouci-ukazatel-cesty-k-vlastni-absenci]] - ukazatel cesty pro vedouciho (17. 8. 2026). **Pozor, ma zastaraly popis klice** `je_vedouci = parent OR out OR att_approver` a vetu, ze Jirka neni v `att_approver` - oboji uz neplati.
- [[doc-dochazka-schvalovani-absenci-kde-a-jak]] - kde se schvaluje v mobilu i v ERP.

