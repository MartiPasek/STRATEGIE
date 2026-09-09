# Odpověď na mail o sick day a přepočtu

Ahoj Jirko,

prošli jsme to a tady je, co z toho vyšlo. U dvou věcí to dopadlo jinak, než jste čekali.

---

## K bodu 1 — přepočet po absenci

**Funkce, která podle vás v databázi chybí, tam ve skutečnosti je a funguje.**

`att_absence` má `_att_automat_recalc_day` napsanou přímo ve svém zdroji a ta uvnitř volá
`att_automat_level_day` — a ten v `g2007.python` existuje. Nic se tiše nezahazuje.

**Skutečná díra byla jinde a byla vážnější:** automat **do dne, kde byla jakákoli absence,
nezapisoval vůbec nic** — ani doplnění do fondu, ani nad fond. Odstranilo se to teprve
**25. 8. 2026**.

Projevilo se to takhle: **Petr Beneš 13. 8.** měl dovolenou 8 h a k tomu si odpíchl 0,55 h
práce. Těch 0,55 h mělo jít celé nad fond (nenároková práce) — nešlo nikam. Ostatní staré
případy noční automat mezitím dohnal sám (jede čtyři dny zpět), na 13. 8. už nedosáhl.
Doháněli jsme ho ručně. Prošli jsme celé období od června — **žádný další případ k opravě
už není**, kromě rozdílů v setinách hodiny, které se řeší zvlášť.

Takže: bod 1 je vyřešený, jen příčina byla jiná, než jste našli.

---

## K bodu 2 — sick day na budoucí den

**Příčina je nulový nárok, ne budoucí datum.**

V kódu je pravidlo: když na sick day nezbývá nárok, celá operace se vezme zpět a v docházce
nevznikne nic. Jirka Honomichl má nárok **0 dní**, takže se mu sick day zapsat nemohl —
ani na 30. 9., ani na žádný jiný den. Luboš Trunec, který vám nesedí, nárok má, a proto
mu to prošlo.

**Ale to pravidlo je zapsané špatně** a Peťa ho v téhle podobě nikdy neschválila:

1. **Komentář v kódu jí připisuje větu, kterou neřekla.** Je tam v uvozovkách
   *„do erp nic nepsat, prostě to je jako že se nic nezadalo"* s jejím jménem a datem
   11. 8. 2026. Prošli jsme přepis toho dne — je to formulace Claudeova, ne Petina.
   Opravujeme to.

2. **Co Peťa 11. 8. skutečně řekla**, doslova:
   > „musí brát aktuální podmínku — pokud se něco nevybere, vybere 0, nemůže to v erp nic
   > založit a **musí to lidem napsat chybu a upozornění, že nic nezaložil**"

   Mluvila o **vadném stavu** — když nárok chybí nebo je nula. Případ *„nárok má, ale
   zbývá mu míň, než zadává"* tehdy neřešila a do jednoho chování ho sloučil až Claude.

3. **Už tehdy chtěla, aby se to člověku napsalo.** Hláška v kódu je (i s nabídkou přepnout
   na návštěvu lékaře), ale **mobilní aplikace ji nezobrazuje** — proto to vypadá, že
   server mlčí a vrací „ok".

### Jak to má fungovat (Peťa, 26. 8. 2026)

> „SD normálně zapsat. Pokud nemají nárok, napsat ‚nemáš nárok'. A nedovolit zadat víc,
> než jim zbývá."

Tedy tři věci:

- **sick day se normálně zapisuje** — žádné tiché zahození,
- **nulový nárok → člověku se to rovnou řekne**, místo falešného „hotovo",
- **nejde zadat víc, než zbývá** — kontrola už při zadávání, ne až po něm.

Zároveň platí, co jsi psal ty a co Peťa potvrzuje: *pokud má někdo nárok, musí si ho
moct zadat kamkoli, a nesmí se nic tiše zahazovat a potvrzovat.*

Domluvili jsme se, že tuhle opravu vezmeš ty.

---

## K bodu 3 — hláška při nulovém nároku

**Nejspíš nová práce nebude.** Ta hláška v kódu už existuje — včetně nabídky přepnout na
návštěvu lékaře (tvoje zadání ze 16. 8., schválila Marti-AI). Problém je v tom, že ji
mobil nezobrazí. Za ověření to stojí dřív, než začneš psát novou.

**Lidí s nulovým nárokem je 25**, ne 23 — počítáno ze smlouvy
(`engagement.pod_sick_days_rok`), což je zdroj pravdy i pro přehled Nároky a čerpání.
Rozdíl proti vašemu číslu neumíme vysvětlit. Nápadné je, že **13 z nich je celá skupina
programátorů PLC ze střediska 002**, kteří zároveň nemají vedenou docházku — takže to
spíš vypadá na skupinu, které se nárok nikdy nevyplnil, než na 13 samostatných rozhodnutí.

---

## Lékař a sick day — dnešní domluva s Martim

Marti **trvá na tom, aby se z návštěvy lékaře přednostně čerpal sick day**. Jak přesně to
má být provedené, zatím dojasněné není — **dočasně to nechal na Petě**.

### Jak si to Peťa představuje (zatím, k prodiskutování)

Žádné automaty. Systém nic nepřeklápí sám, jen člověku poradí:

1. Člověk zadá **„jdu k lékaři"**.
2. Systém mu **napíše informaci**, že se přednostně čerpá sick day.
3. **Ukáže mu, kolik mu ze sick days zbývá.**
4. A **vyzve ho, ať si zadá sick day** — rozhodnutí i zadání zůstává na něm.

Tím odpadá to, co dělá potíže dneska: že se člověku tiše zapíše něco jiného, než vybral,
a dozví se to až z docházky (nebo vůbec).

### Otevřená otázka k zadávání sick day dopředu

Je potřeba rozmyslet, **jak daleko dopředu smí jít sick day zadat**. Jinak vznikne tohle:
někdo si zadá sick day na příští týden, mezitím půjde k lékaři — a v tu chvíli už nemá
z čeho čerpat, protože si nárok zablokoval dopředu na den, který ještě nenastal.

Návrh na omezení zatím nemáme, je to k prodiskutování.

---

## Ještě jedna věc navrch

Při ověřování jsme narazili na to, že **nemoc, OČR a lékař nahlášené z mobilu se zapisovaly
do docházky** — přestože Peťa opakovaně (19. 8., 24. 8., 25. 8.) říkala, že to mají být
**jen informace vedoucímu**. Nemoc a OČR se do Správy docházky zapisují ručně až podle
dokladu.

Byly na to **tři různé vstupy** z mobilu, ne jeden — a nejzákeřnější je „je mi blbě, dnes
nedorazím": z volného textu se rozpoznala nemoc a založila se žádost na 8 hodin.

Opraveno ve všech třech, ověřeno na živém zápisu. Lékař je zatím **taky jen informace** —
jeho logika se předělá podle toho, na čem se dohodneme (viz sekce výše).

Zapsáno do G2007 jako `doc-dochazka-mobil-nemoc-ocr-lekar-jen-info-vedoucimu`, plus dvě
pojistky, ať to nikdo nevrátí. Rozhodnutí totiž padlo už 19. 8., ale nikde zapsané nebylo —
proto se k němu Peťa musela vracet počtvrté.

### Ale vylezly u toho tři vady v mobilu — a na ty se prosím podívej

Peťa to hned zkoušela naostro (26. 8., „Tady budu jinde"). **Data jsou v pořádku** — do
docházky ani do Správy se nezapsalo nic a notifikace vedoucímu chodí. Vada je v tom,
**co vidí člověk v mobilu**:

**1. OČR — po stisku Potvrdit hláška „nepovedlo se uložit".**
Zápis přitom proběhl přesně tak, jak měl (nic se nezaložilo, vedoucímu odešla zpráva).
Člověk se ale dozví, že se něco pokazilo.

**2. Nemoc — v mobilu se nestane nic a přijdou DVĚ notifikace, každá jiná.**
```
🌴 Nahlášená nepřítomnost
   Iva Hrůzová: Nemoc (PN) 26. 8. – 28. 8. — neschopenka (přes…

   Nahlášená nepřítomnost
   Iva Hrůzová hlásí Nemoc (PN) 26. 8. — Neschopenka do 28. 8.
```
Ta první (s palmičkou) navíc **termínově odpovídá tomu, co se zadávalo u OČR**, ne
u nemoci. Vypadá to, že mobil při jednom zadání volá **dvě různá místa naráz** — každé
s jinými parametry.

**3. Lékař — taky „nepovedlo se uložit" a notifikace zprvu nedorazila.**
O chvíli později se objevila (`🌴 Iva Hrůzová: Lékař 31. 8. — u lékaře do ~12:29 · Jen na
vědomí`) a naopak **zmizela notifikace OČR**, kterou Peťa nepotvrzovala.

Hlášku „Nepovedlo se uložit" vypisuje mobil ve větvi `.catch()` — takže volání skončilo
výjimkou nebo odpovědí, kterou si mobil vyložil jako chybu. Server přitom vrací
`ok: true, created: 0` (nic se zapisovat nemá, to je záměr) — **podezření padá na to, že
si mobil ověřuje `created > 0`**, ale neověřovali jsme to, takže to netvrdíme.

Do kódu mobilu jsme nesahali. Necháváme na tobě.

---

Kdyby k čemukoli chyběl kontext, ozvi se.

**Claude‑26 / Peťa**
