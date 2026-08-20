# Vedoucí: jediný způsob poznání + fronta oprav se rodičům neplní

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Vedouci: jediny zpusob poznani + fronta oprav se rodicum neplni

**Zadal Jirka Honomichl 18. 8. 2026, schvalila Marti-AI. Nasazeno tyz den, overeno na obrazovce.**

## 1. Kdo je "vedouci" (att_absence_inbox, verze 4)

**Vedouci = jsem NECIM schvalovatelem.** Beru se stejne dva zdroje, ze kterych se zadosti
prideluji (`_abs_resolve`):

1. osobni vyjimka `tenant.att_odpovednost` (agenda `volno`, aktivni, v platnosti) — MA PREDNOST,
2. vedouci skupiny `tenant.att_approver` (aktivni radek).

Priznak `je_vedouci` schovava formular vlastni zadosti a ukazuje ukazatel cesty do Dochazky.

**Co bylo spatne:** `bool(parent OR out OR att_approver)`, kde `out` = "mam prave ted na sobe
cekajici zadost". Michelle Safrankova je schvalovatelka jen pres osobni vyjimku
(Petra Safrankova -> Michelle), takze se vedouci **stavala jen na dobu, kdy mela zadost**
k rozhodnuti — formular ji jednou zmizel a jednou se vratil.

**Rodice uz nejsou vedouci "z titulu rodicovstvi".** Marti-AI 18. 8. 2026: *„Vedouci ma znamenat
'jsem necim schvalovatelem' — to je cista definice. Rodice maji dohledovy pristup jinou cestou,
ne tim, ze jim zmizi vlastni formular."*
⚠️ Marti (1) i Kristy (11) presto vedouci ZUSTAVAJI — maji aktivni osobni vyjimku
(Kristy schvaluje Jirku, Martiho a Michala Sika; Marti schvaluje Kristy). To je spravne:
jsou schvalovateli, protoze je nekdo urcil, ne protoze jsou rodice.
Rodic dal VIDI vsechny cekajici zadosti (`cond` v `run()`) — to se nemenilo.

**Dopad:** nikdo o status vedouciho neprisel, Michelle prestala kolisat.

## 2. Fronta Oprav dochazky se rodicum neplni (att_fix_queue, verze 3)

Marti 18. 8. poslal fotku z mobilu — v Ukolech mel zadost o opravu dochazky od Jana Periny
z vyroby: *„mne tohle chodit nema, a z vyroby uz vubec ne."*

**Diagnoza (Peta / C26, overeno):** notifikace jsou v poradku — rodic do nich nikdy nespadne,
protoze nema radek v `att_fix_scope`. Slo cistě o **viditelnost fronty**: `att_can_fix` pousti
do modulu i rodice bez clenstvi ve skupine editoru (Jirka 21. 7. 2026, dohledovy pristup)
a `att_fix_scope` jim da pusobnost `vse`, takze se fronta nefiltrovala a videli i vyrobu.

**Zmena:** `att_fix_queue` vraci **prazdnou frontu** (`anomalie`/`rozpory`/`stare_skryte` = [],
`dohled: true`) tomu, kdo **neni clenem skupiny `DOCHÁZKA - OPRAVY`**. Pristup do modulu
rodicum **zustava** — neplni se jim jen tahle fronta.

Marti-AI 18. 8. 2026: *„Dohledovy pristup ma smysl pro audit a kontrolu, ne pro kazdodenni
operativni frontu vyroby. Push do jejich ukolu je kontraproduktivni."*

**Koho se to tyka:** presne 2 lidi — **Marti (1) a Kristy (11)**. Petin e-mail uvadel tri
(vcetne Jirky), ale **Jirka rodic NENI** — do modulu chodi jako radny editor s pusobnosti `vse`.
Pet editoru (Dusan, Jirka, Michaela Hladikova, Michelle, Petra Safrankova) ma frontu beze zmeny.

## Jak to bylo overeno (18. 8. 2026)

- Zapis do `g2007.python` pres most **base64 + md5 guard** (`WHERE md5(zdroj)=<stary otisk>`)
  = optimisticky zamek proti soubehu; oba zapisy prosly jako G2007 konstruktivni operace
  (1 radek), otisky po zapisu sedi na znak.
- **`verze` povysena** (3->4, 2->3) — `erp_registry` cachuje podle `(kod, verze)`, bez toho by
  bezici proces jel dal ze stareho kodu. **Na tohle nezapomenout u kazde zmeny kodu v DB.**
- Zivy smoke test v prohlizeci: oba endpointy 200, editor ma frontu plnou (3 anomalie + 1 rozpor).
- Obrazovky overeny prepsanim `window.fetch`: vedouci vidi seznam + ukazatel + tlacitko
  a NEMA formular; rodic dostane prazdnou frontu bez cizich zaznamu a nic se nerozbije.
- Gotcha pri testovani: prava na obrazovce Opravy dochazky se ctou z `window._canFixDoch`,
  ktere nastavuje start appky. V cerstve otevrenem okne (bez doinicializace) obrazovka hlasi
  *„Nemas opravneni k opravam dochazky"*, i kdyz API prava vraci — **neni to chyba prav**.

## 3. Veta pro rodice misto zelene hlasky (dokonceno 18. 8. 2026)

Prazdna fronta se rodici puvodne vykreslila jako **„Vsechno vyreseno. 👍 Nic neceka."** — to
uklidnovalo necim, co neni pravda: polozky existuji, jen nejsou jeho. Stejny vzorec, na ktery
Marti-AI upozornila 17. 8. u ukazatele cesty (*„ukazatel do prazdna je horsi nez zadny ukazatel"*).

**Nasazeny text (schvalila Marti-AI 18. 8. 2026, vzat doslova):**

> „Dohledovy pristup — fronta se ti zamerne neplni. Opravy dochazky resi editori skupiny
> DOCHAZKA - OPRAVY. Kdybys potreboval prehled, dej vedet."

Marti-AI odmitla muj puvodni navrh, ktery editory vyjmenovaval jmenovite: *„jmenovity seznam
se bude menit a v UI ho nikdo neaktualizuje — lepsi odkaz na skupinu."* Posledni veta je tam
schvalne, aby mel clovek cestu ven bez zjistovani, koho oslovit.

**Kde to zije:** text posila backend (`att_fix_queue`, pole `info` + priznak `dohled`), UI ho jen
vypise — fragment `apps/api/static/mobile_parts/60_dochazka.js`, vetev `_fixQueueLoad`. Fallback
v JS je stejna veta, kdyby `info` nedorazilo. Overeno na zive appce z obou stran: rodic vidi
vysvetleni a zadne cizi zaznamy, editor ma frontu plnou a zadnou hlasku navic.

**Pozor pri editaci toho fragmentu:** dela na nem i Peta (C26) — 18. 8. jsem zapisoval hodinu po
jejim ulozeni. Pouzij `@@WHO` a zapis pust s pojistkou `WHERE md5(obsah)=<otisk, ktery jsi cetl>`,
at cizi praci neprepises.

