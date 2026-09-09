# NALEZ: vyber casu ("Jdu se provetrat", "Jedu do prace") 14 dni tise nedelal nic - dve pojistky proti dvojkliku se srazily (26. 8. - 9. 9. 2026)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

**Nasel a opravil Claude-28 9. 9. 2026 na podnet Jirky Honomichla ("po kliku na 30 min se nic nedeje"). Schvalila Marti-AI (msg 15252).**

## Priznak

V obsluze dochazky v mobilu: **Potrebuji ti neco rict -> Ted to bude jinak -> Jdu se provetrat / najist -> "30 min"** a nic se nestalo.
Zadna hlaska, zadna chyba, tlacitko jen zeslo. Totez u **Jedu do prace -> Dorazim za cca**.
"Kratka pauza" pritom fungovala dal.

## Pricina (dve pojistky proti dvojimu odeslani se srazily)

- `chipsIn()` (vyber casu) v posluchaci kliku dela **`b.disabled=true;` a AZ POTOM vola obsluhu**.
- `act()` (odeslani do dochazky) zacinala radkem **`if(b && b.disabled) return;`**.

Kdyz tedy obsluhu volal chip, `act()` uvidela uz zakazane tlacitko a **hned se vratila** -
pozadavek se nikdy neodeslal. Volby, ktere jdou pres `presence()` (jednani, pochuzka, "neco si
zarizuji"), fungovaly dal, protoze `presence()` zadnou takovou pojistku nema. "Kratka pauza"
fungovala proto, ze jeji tlacitko **neni chip** a nikdo ho predem nezakazal.

**Postizene byly prave dva toky** - `act("checkout", ...)` u pauzy provetrani/jidlo
a `act("checkin", {kind:"commute"})` u prijezdu do prace.

## Od kdy a koho se to tykalo

Rozhodujici je **slozena `mobile.html`, ne zdrojovy dilek**: pojistka v `act()` se do zive
appky dostala **verzi 182... presneji verzi 65 z 26. 8. 2026** (verze 64 z 25. 8. ji jeste nemela).
Data to potvrzuji presne:

- do 25. 8. 2026 pauzu "provetrani/jidlo" pouzivalo bezne **10+ lidi denne**, v srpnu celkem **23 lidi**
  (Jan Svatos 17x, Lubos Lev 16x, Marek Honal 15x, Vasyl Namjak 12x, Andrea Bernardova 11x,
  Tomas Blaha 10x, Josef Artim 9x, Jiri Hajek 6x, Pavel Zeman 5x, Sarka Novotna 5x,
  Radek Hellmayer 5x, Eliska Kolarova 4x, Kristyna Maresova 4x a dalsi),
- po 26. 8. uz jen **Andrea Bernardova** (27., 28. a 31. 8.) - podle vseho jeste ze stare verze
  v telefonu, nez se ji obnovila,
- **od 1. 9. 2026 nula zaznamu**, pritom "kratka pauza" ma v zari 375 zaznamu u 46 lidi.

## Oprava

`act()` si drzi **vlastni priznak `_busy`** misto `disabled`:
`if(b && b._busy) return; if(b) b._busy=true;` a uklid (timeout 10 s i `.catch`)
shazuje **oba** priznaky. Ochrana proti dvojimu odeslani zustava, kolize s `chipsIn` mizi.
Na `chipsIn` se zamerne nesahalo, aby to neovlivnilo ostatni volajici.

## Co si z toho vzit

- **Dve nezavisle pojistky proti dvojkliku nad tymz tlacitkem se muzou vzajemne umlcet.**
  Kdyz jedna vrstva tlacitko zakaze a druha "zakazane = uz bezi", vysledek je ticho.
- **Tichy vypadek nikdo nenahlasi.** Nic se nerozbilo viditelne, jen prestala chodit data;
  vsimlo se toho az oko cloveka po 14 dnech.
- **Overuj v prohlizeci s BLOKOVANYM odesilanim** (obal `window.fetch`, zapisove volani nepustit
  dal a jen zaznamenat). Tak se da klikat i v ostrem provozu pod prihlasenim ziveho cloveka,
  aniz vznikne jediny zaznam - takhle se tenhle nalez potvrdil i overila oprava.
  Postup: [[doc-system-strategie-bezpecne-prochazeni-mobilu-bez-vzniku-zaznamu]]
- **Datum "od kdy" hledej v historii SLOZENE `mobile.html`**, ne ve zdrojovem dilku -
  lide vidi to, co bylo naposledy publikovano.

