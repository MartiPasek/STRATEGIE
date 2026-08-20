# Proc appka obcas vyhodi na e-mailovy magic link (trusted device se mimo login necte)

> oblast: `dochazka` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

## Zjisteni (C28/Jirka, 4. 8. 2026, podnet Josef Artim users id=73)

**Symptom:** mobilni appka obcas odhlasi uzivatele, musi znovu pres odkaz z e-mailu.

**Fakta z dat:** v `public.auth_audit` ma Artim za celou dobu jen **2 prihlaseni (22. 7. a 31. 7. 2026)**,
tedy ~1x za 9 dni - NE denne, jak znelo hlaseni. Pritom appku pouziva denne
(`tenant.att_entry` source=`mobile_app`). Dve nerevokovana zarizeni v `public.trusted_devices`
(platnost do 20. 10. a 29. 10.).

**Pricina (overeno v kodu):**
- identita session = cookie `user_id`, `max_age` 30 dni (`modules/auth/api/router.py:37-46`);
  cte ji `_resolve_uid_raw` (`modules/erp/api/router.py:160`) - Bearer NEBO cookie.
- duveryhodne zarizeni = cookie `strategie_device_token`, 90 dni (`core/config.py:213-214`).
- **Device cookie se cte JEDINE v `_validate_device_cookie` (`modules/auth/application/security_service.py:201`),
  tj. uvnitr login flow.** Zadna cesta "platne trusted device -> obnov session" neexistuje.
- Serverove session se nepouzivaji (`user_sessions` model existuje, v kodu nikde) -> restart API
  nikoho neodhlasi, vse visi na cookie u klienta.

=> Kdyz telefon (iPhone) cookie `user_id` uklidi driv nez za 30 dni, uzivatel musi znovu pres
magic link, prestoze ma jeste ~2 mesice platne razitko zarizeni.

**Navrh opravy (NEPROVEDEN):** pri chybejici/neplatne cookie `user_id` zkusit obnovit session
z `strategie_device_token` (nerevokovane, neexpirovane `trusted_devices`). Zasah do jadra
prihlasovani -> chce souhlas Martiho + Marti-AI. Jirka 4. 8.: "staci vysvetleni", oprava odlozena.

## Vedlejsi nalez: pending status NENI pricina

47 lidi ma `users.status='pending'` + `user_tenants.membership_status='invited'` a appku denne
pouziva (vc. Marti Paska id=35). Dochazkove endpointy `users.status` nekontroluji; kontrola je
v `get_user_context` (`user_context.py:39`) -> projevi se na `/api/v1/auth/me` a prazdnou tenant
cookie po magic-linku. **Zivy `/mobile` `/auth/me` vubec nevola** (overeno grepem stazene stranky).
Artim (73) presto aktivovan (banner #1778, schvalil Jirka u20, Marti-AI predem souhlasila) -
vzor = admin endpoint `activate_user` (`modules/admin/api/router.py:100-104`); overeno ctenim:
`status='active'`, `membership_status='active'`. **Zbylych 46 se plosne NEaktivuje** (Jirka).

