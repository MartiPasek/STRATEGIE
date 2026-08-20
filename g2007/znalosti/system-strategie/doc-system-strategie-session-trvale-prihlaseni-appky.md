# Trvalé přihlášení v appce - klouzavá session 90 dní + tiché obnovení ze známého zařízení (10.8.2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)


## Co se dělo (příznak)

10.8.2026 přišla za Jirkou vlna uživatelů mobilní appky, že je appka odhlásila a musí znovu přes e-mailový odkaz. Nešlo o výpadek ani útok.

## Příčina (ověřeno v kódu i datech)

Cookie `user_id` měla natvrdo `max_age=60*60*24*30` (30 dní) a nastavovala se POUZE v `_set_auth_cookies` (modules/auth/api/router.py), tedy jen při přihlášení. **Nikde se neobnovovala.** Každý uživatel proto vypadl přesně 30. den po přihlášení, i kdyby appku otevíral denně.

Data to potvrdila - všech 6 lidí, co si 10.8. dopoledne žádalo nový odkaz (uid 48, 52, 57, 65, 66, 83), se naposledy přihlásilo 7.-10.7., tedy 31 až 34 dní zpět. Byl to doběh červencové vlny onboardingu. Dalších 18 lidí mělo vypadnout do tří týdnů.

Druhá půlka problému - `trusted_devices` cookie `strategie_device_token` platí 90 dní a lidé ji měli, ale `_resolve_uid_raw` (modules/erp/api/router.py) bere identitu POUZE z Bearer tokenu nebo z cookie `user_id`. Device cookie se používala jen ve vrstvách `check_security_layers`, ne k obnově session. Endpoint `verify-email/request` navíc vrstvy netestuje a odkaz pošle vždy - proto museli i lidé se známým telefonem přes e-mail.

## Řešení (commit 5f329697, schválila Marti-AI)

1. **`settings.session_cookie_max_age_days = 90`** (core/config.py) místo natvrdo 30 dní.
2. **Klouzavé prodloužení** v `request_id_middleware` (apps/api/main.py) - při každém použití se cookie posune dopředu, takže lhůta běží od POSLEDNÍHO použití, ne od přihlášení. Set-Cookie nejvýš 1x denně přes marker cookie `stg_sess_ref` (datum).
3. **Tiché obnovení** `_sess_restore_from_device` - když `user_id` cookie chybí, ale telefon pošle platný `strategie_device_token`, server session obnoví sám bez e-mailu. Identita se propašuje i do právě běžícího requestu přepsáním hlavičky cookie ve `scope`.

## Pravidla, která u toho platí (schválila Marti-AI 10.8.)

- Tiché obnovení JEN pro role `employee` a `member` a JEN pro lidi bez `is_admin` a bez `is_marti_parent`. Ven jdou role `owner` a `ambassador` a všichni správci a rodiče - privilegovaný účet se má přihlašovat vědomě. Ověřeno na datech - povoleno 56 lidí, zakázáno 3 správci a 1 owner.
- Shodu IP Marti-AI vědomě NEvyžaduje - mobil přepíná mezi 4G a WiFi, false positive by byl vysoký.

## PASTI, na které si dát pozor (všechny reálně hrozily)

1. **NEkontroluj `users.status = 'active'`.** Zaměstnanci, kteří si nikdy nenastavili heslo, mají status `pending` - všech 6 postižených lidí bylo `pending`. Kontrola na 'active' by opravu vypnula přesně těm, komu má pomoct. Ven patří jen `disabled` a `archived`. Ze stejného důvodu se nedá použít `get_user_context` - ta vrací None, když status není 'active'.
2. **Middleware nesmí sahat na `/api/v1/auth/*`.** Logout maže cookies přes `delete_cookie` a prodloužení by hned za tím přilepilo Set-Cookie se starým `user_id` - poslední Set-Cookie v prohlížeči vyhrává a člověk by se z appky nedostal ven. Stejně tak exit-demo, demo-login, potvrzení odkazu, impersonace.
3. **Sdílený telefon.** ERP endpoint pro přepnutí uživatele PINem (`shared_active`) nastavuje `user_id` cookie MIMO `/auth/*`. Bez pojistky by prodloužení přepnutí tiše vrátilo zpět. Proto se před nastavením cookie prochází `response.raw_headers` a když odpověď sama nastavuje `user_id`, middleware nesahá na nic.
4. **Demo a impersonace se neprodlužují.** Demo má cookies záměrně session-scoped (rozhodnutí Martiho 27.7.), `imp_token` má vlastní krátkou platnost.
5. **Necti `request.cookies` před přepsáním hlaviček** - Starlette si je v Requestu cachuje a cache by držela starý nepřihlášený stav. Proto se cookies parsují ze syrové hlavičky pomocnou funkcí `_sess_parse_cookies`.
6. **V `apps/api/main.py` NENÍ modulový `logger`** - `logger.info` by shodilo každé tiché obnovení na NameError. Použit vlastní `_sess_log = get_logger(...)` a import `get_logger` doplněn.

## Jak se to ověřovalo

Živě přes curl na produkci - Set-Cookie s `Max-Age=7776000` (90 dní), opakovaný požadavek se stejným markerem už nic nenastavuje, logout dál maže cookies a nic je nevrací, neplatný i poškozený device token nikoho nepřihlásí a nic neshodí. Chybový deník po nasazení bez nových chyb (asyncio hláška u restartu běží denně už týdny, se změnou nesouvisí). Appka v prohlížeči normálně načtená a přihlášená.

## Otevřená věc - samostatná bezpečnostní díra

Přihlašovací odkaz z e-mailu NENÍ na jedno použití. 10.8. byl u uid 65 tentýž odkaz zkonzumován 5x během 3 sekund z různých user agentů včetně X11 Linux, tedy automatická kontrola odkazů poštovního serveru. Každá konzumace zakládá nové `trusted_device` a vrací platné auth cookies, takže skener dostane přístup do appky. Marti-AI to má zapsané v paměti (id 440). Řešit samostatně, ne v této opravě.

Autor - C28 (Jirka), zadání Jirka, odborné schválení Marti-AI, 10.8.2026.

