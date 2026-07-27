# Mobilni login: pending user se neprihlasi (get_user_context vyzaduje active) + fix activate_user

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Mobilni login: proc se pending user neprihlasi do appky

> oblast: system-strategie - Claude-28 (Jirka), 24.7.2026. Overeno v kodu, pripad Erika Sedlackova (user 45).

## Symptom
Uzivatel pozada z mobilni appky o prihlaseni emailem (magic link), email prijde, klikne
na odkaz (i na PC - cross-device handoff jinak funguje), ALE mobilni appka se NEPRIHLASI.

## Root cause (OVERENO V KODU, ne hadano)
`modules/auth/application/user_context.py::get_user_context` hned na zacatku:
    if not user or user.status != "active": return None
Kdyz je `users.status='pending'`, vrati None. V poll handoffu
`modules/auth/api/router.py /verify-email/status` je pak `ctx=None -> tenant_id=None`
-> `_set_auth_cookies(resp, uid, None)` nastavi cookie BEZ tenanta -> appka nema
platnou session -> "neprihlasi se". Trusted device i device-cookie se pritom vytvori
(proto to vypada, ze klik prosel, ale login ne).

## Jak potvrdit z dat (spravne nazvy sloupcu!)
- `SELECT status FROM public.users WHERE id=<uid>`  -> musi byt 'active' (jinak blok).
- `SELECT membership_status FROM public.user_tenants WHERE user_id=<uid>` -> 'active' (ne 'invited').
- POZOR: `user_tenants` ma sloupec **membership_status** (NE status). `users` ma **status**.
  `users` NEMA sloupec is_active. (Nehadej nazvy - over information_schema.)

## Cross-device handoff (jak login SPRAVNE funguje - pro kontext)
1. Mobil POST /api/v1/auth/verify-email/request -> create_invite, posle email/SMS,
   vrati polling_token (= invite_token).
2. Mobil polluje GET /verify-email/status?token=... kazde 2s.
3. Klik na magic link (kdekoli) -> consume_invite -> vytvori trusted_device pro
   klikajici zarizeni + consumed_at.
4. Mobiluv poll uvidi consumed -> vezme device (invite.created_device_id) a nastavi
   JEHO device-cookie + auth cookies na odpoved pollujiciho mobilu -> mobil prihlasen.
Takze klik na PC je OK - pollujici mobil dostane session. Podminka: user musi byt 'active'.

## Fix (parent-only, kod to ma pripravene)
`modules/admin/api/router.py::activate_user` - "rucni aktivace pending uzivatele,
kdyz uvizne na aktivacnim kroku" (Claude-24 + Kristy 15.7.):
    UPDATE public.users SET status='active' WHERE id=:uid AND status='pending';
    UPDATE public.user_tenants SET membership_status='active'
      WHERE user_id=:uid AND membership_status='invited';
Heslo NETREBA (login je passwordless pres trusted device). Po tom get_user_context
doplni last_active_tenant z prvni aktivni membership a login projde. UI = parent-only
tlacitko "Aktivovat uzivatele".
⚠️ Aktivacni write blokuje auto-mode klasifikator (meni stav uctu) -> potreba explicitni
souhlas / schvalovaci banner.

## Kontext
K 24.7. bylo 70 pending vs 29 active useru (pending = pozvani, nedokonceny onboarding).
Onboarding (nastaveni hesla z pozvanky) userA aktivuje: invitation_service.py ~ř.302
`user.status='active'` + ř.312 `membership_status='active'`.

