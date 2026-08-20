# Přihlašovací odkaz - potvrzení tlačítkem, polling vázaný na žadatele a jen jednou, platnost 4 h (10.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co bylo špatně (ověřeno v kódu i v datech, ne domněnka)

Dvě samostatné věci. Pozor, **spálení tokenu funguje správně** — `consume_invite` filtruje `consumed_at IS NULL` a v datech má každá pozvánka právě jedno `consumed_at`. Kdo tvrdí, že odkaz není jednorázový, plete si to s tímhle:

**1) Polling endpoint rozdával session opakovaně.** `GET /verify-email/status?token=X` po nalezení už zkonzumované a nevypršené pozvánky nastavil device cookie na 90 dní plus auth cookies — a udělal to KAŽDÉMU, kdo přišel s tokenem, KOLIKRÁT chtěl, po celou platnost pozvánky (tehdy 24 h). Žádné spálení, žádná vazba na prohlížeč, který o odkaz žádal. Token přitom leží jako čitelný parametr v URL v e-mailové schránce. Kdo odkaz uvidí (poštovní automat, přeposlaný mail, firemní proxy, log, historie prohlížeče), mohl si z něj opakovaně vyrábět plnou session daného člověka.

**2) Odkaz přihlašoval pouhým otevřením.** Odkaz v e-mailu byl prostý GET na `/api/v1/auth/verify-email/confirm?token=...`. Samotné otevření URL token spálilo a přihlásilo. Automat, který odkazy v poště otevírá, tím token spálil dřív, než na něj člověk klikl, a člověk musel žádat nový.

## Jak se to pozná v auditu (užitečné při dalším šetření)

V `public.auth_audit` mají oba případy stejný `result='verify_consumed'`, liší se `layer_detail`:
- `Magic link invite #N` = skutečná konzumace tokenu (právě 1x na pozvánku),
- `sms invite #N` = polling status endpoint (mohlo být mnohokrát).

10.8. u pozvánky 197 (uid 65) to vypadalo takto: žádost z firemní IP 93.99.211.138 (Windows), skutečné kliknutí z JINÉ IP 46.135.22.219 se zařízením X11 Linux, pak čtyři dotazy status endpointu z firemní IP dostaly session. Automatické otevírání odkazů je ale VÝJIMEČNÉ, ne hromadné — v posledních ~40 pozvánkách je to ojedinělý případ. Díra platí bez ohledu na četnost.

## Co se nasadilo (commity 72001489 a 9c434d37, schválila Marti-AI)

1. **Potvrzení tlačítkem.** GET `/verify-email/confirm` už jen vykreslí stránku s tlačítkem a NESAHÁ do databáze (žádný vedlejší účinek, žádná informace ven). Token spálí a přihlásí až POST na stejnou cestu. Automaty a prefetch POST neposílají. Stejný vzor už v kódu byl u PWA pozvánek (`pwa_invite_confirm_screen` plus `pwa_invite_consume`) — auth flow se s ním jen srovnal.
2. **Polling vázaný na žadatele.** `/verify-email/request` vygeneruje tajemství, pošle ho žádajícímu prohlížeči v HttpOnly cookie `stg_poll` a jeho sha256 uloží do nového sloupce `public.trusted_device_invites.poll_secret_hash`. `/verify-email/status` vydá session jen tomu, kdo tajemství pošle; jinak vrátí `pending`, aby cizí nepoznal, že token platí, a zaloguje warning `VERIFY_STATUS odmitnuto - cizi prohlizec`.
3. **Session z pollingu nejvýš jednou.** Nový sloupec `session_delivered_at`. Druhý a další dotaz vrátí `consumed` BEZ cookies.
4. **Platnost self-request odkazu 24 h → 4 h** (`sec_magic_link_self_ttl_hours`). Pre-approve zůstává 72 h. Marti-AI výslovně odmítla 60 minut jako krátké (lidé si poštu otvírají s odstupem a přepínají zařízení).

## Rozhodnutí a odchylky, které je dobré znát

- **Odchylka od schváleného návrhu.** Marti-AI schválila B1 ve tvaru „po vydání session nastav expires_at na now". Nasazena je lepší varianta se sloupcem `session_delivered_at` — bezpečnostní vlastnost je stejná (session nejvýš jednou), ale UI při souběžných dotazech nedostane `expired` a nezobrazí falešnou chybu. V datech je vidět, že prohlížeč umí vystřelit čtyři dotazy během 350 ms, takže ten souběh je reálný.
- **Cross-device chování** (schváleno). Když člověk otevře odkaz na jiném zařízení, než odkud žádal, přihlásí se tam, kde odkaz otevřel. Původní zařízení session nedostane. Pro appku to ale funguje dál — o odkaz žádá WebView appky, ta drží cookie a poll, klik může proběhnout v jiném prohlížeči nebo poštovním klientovi. Přesně tenhle případ byl důvod, proč polling vůbec existuje.
- **Zpětná kompatibilita.** Pozvánky založené před nasazením nemají otisk, u nich se `/status` chová jako dřív. Okno je omezené platností odkazu.
- **Cookie `stg_poll` se nastavuje i pro neexistující e-mail**, aby útočník nepoznal rozdíl (anti-enumeration).
- **Texty o platnosti** (e-mail, hláška v `sms_login.html`, `VerifyEmailRequestResponse.message`) už neuvádějí pevný počet hodin, aby po další změně configu nezestárly.

## Jak se to ověřovalo (VČETNĚ živého průchodu, doplněno 10.8. 12:10)

Nasucho přes curl na produkci - otevření odkazu (GET) vrací stránku s tlačítkem a ŽÁDNOU cookie, POST s neplatným tokenem nepřihlásí, žádost o odkaz nastaví `stg_poll` jako HttpOnly Secure SameSite lax s Max-Age 14400 (4 h). Nové sloupce v `information_schema` existují. Chybový deník bez nových chyb.

**Živý průchod (Jirka, pozvánka #200):** vytvořena 12:06:03, platnost do 16:06:03 (přesně 4 h), `consumed_at` 12:06:51 (potvrzeno tlačítkem), `session_delivered_at` 12:06:57 (polling dostal session právě jednou), `poll_secret_hash` vyplněn. Čekací stránka se sama přepnula a otevřela appku.

**Simulace útoku na živém tokenu (se souhlasem Jirky):** volání `/verify-email/status` s jeho platným tokenem, ale BEZ cookie prohlížeče → HTTP 200, `status=pending`, **žádná Set-Cookie**, a v `fw.diag_log` warning `VERIFY_STATUS odmitnuto - cizi prohlizec, invite #200`. Odpověď `pending` (ne `consumed`) dokazuje, že zabrala VAZBA NA PROHLÍŽEČ, ne až pojistka „jen jednou" — obě pojistky jsou tedy ověřené samostatně.

**Poznámka k testování:** prostředí Claude Code blokuje AI iniciovat přihlašování (POST na verify-email/request i otevření login stránky v prohlížeči). Živou část musí proklikat člověk; AI pak ověří výsledek v DB a smí volat čtecí `/verify-email/status`. Počítej s tím při dalších změnách auth flow.

Autor - C28 (Jirka), zadání Jirka, odborné schválení Marti-AI, 10.8.2026. Souvisí s doc-system-strategie-session-trvale-prihlaseni-appky a doc-system-strategie-auth-session-model.

