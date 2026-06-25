# ✉️ Odpověď pro Martiho / Claude ID23 (k odeslání) — Jirka

> Připravil Claude pro Jirku, 25. 6. 2026. Reakce na návod ID23. Stačí zkopírovat.

---

**Předmět:** Re: Google Play — jdu do toho

Ahoj Claude (a díky Martimu),

návod mám, jdu do toho. 

**1) Pozvánka do Play Console** — Marti, pozvi mě prosím (Users and permissions)
na účet **j.honomichl@eurosoft.com**. Klidně Admin, jako u Apple.

**2) Důležité k směru — jdeme VEŘEJNĚ (komerčně).** Domluvili jsme se, že appku
chceme nakonec vydat **veřejně jako iOS**, protože celou STRATEGII včetně mobilní
appky budeme nabízet dalším zákazníkům. Internal testing je OK jako první krok,
ale ať to rovnou vezmeme správně — pro veřejnou **Production** počítejme s tím, že:
- **samo-aktualizace** (stahování APK, `REQUEST_INSTALL_PACKAGES`) musí z veřejné
  verze **pryč** — Play to u appek z Obchodu zakazuje (update řeší Play sám),
- **SMS brána + čtení call-logu** (`READ_SMS/SEND_SMS/RECEIVE_SMS/READ_CALL_LOG`)
  Play u veřejných ne-messaging appek prakticky nepovolí → necháme je **jen
  v interní sideload verzi** pro firemní „bránový" telefon.
- → pro Production tedy budeme potřebovat **„čistou" variantu buildu** (bez těch
  tří věcí). **Pro Internal testing klidně jeď aktuální build** (v1.68).
- Mikrofon (diktování), kontakty pro caller-ID a notifikace zůstávají i ve veřejné verzi.

**3) Listing** píšu jako **komerční B2B produkt** (mám připravené texty +
grafiku — ikona 512 a feature 1024×500), ne jako „interní appku EUROSOFTu".
Drobnost: stránku `/privacy` pak sjednotíme s tímhle (teď tam je „není pro veřejnost").

Až mě Marti pozve, ověřím/založím listing, vyplním formuláře a dám vědět, ať
vyrobíš **AAB** pro Internal testing. App Signing — nahraju náš `strategie-release.jks`.

Díky a ať to jede!
Jirka
