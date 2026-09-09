# Pristup do mobilni aplikace: staci aktivni e-mailovy kontakt (ne heslo, ne telefon, ne stav active)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Pristup do mobilni aplikace: staci aktivni e-mailovy kontakt

> oblast: system-strategie - Claude-28 (Jirka), 8. 9. 2026.
> Overeno na zivem kodu a na zivych datech pri zpristupneni appky Marku Hornikovi (user 137).

## Jak se do appky vstupuje

Prihlasovaci obrazovka (`apps/api/static/sms_login.html`, r. 350) chce **jen e-mail**.
Posle ho na `POST /api/v1/auth/verify-email/request` s `channel:'email'`, server posle
**odkaz do e-mailu**, clovek klikne a je uvnitr. Zadne heslo se nikde nezadava.

- **SMS cesta je mrtva** - `channel:'sms'` server tise preklapi na `email`
  (`VERIFY_CHANNEL_COERCE`, Marti 6. 6. 2026). Telefon k prihlaseni neni potreba.
- **Heslo ani aktivacni e-mail nejsou potreba.** Ani stav `active` - viz
  `doc-system-strategie-mobil-login-pending-user`.

## Server hleda cloveka jen na trech mistech

`modules/auth/api/router.py`, r. 346-383:

1. `public.users.ews_display_email`
2. `public.user_contacts` - typ `email`, stav `active`
3. `public.users.ews_email` (stary zapis, jen pro ucty pred Phase 38)

**POZOR - nejcastejsi pricina "nemuzu se prihlasit":**
osobni e-mail z karty zamestnance (`tenant.user_self_data.personal_email`)
**v tomto retezci NENI**. Adresa muze byt v systemu vyplnena a v karte videt,
a prihlaseni ji presto nenajde.

## Musi tedy platit dve veci

| # | Co | Kde | Kdyz chybi |
|---|---|---|---|
| 1 | aktivni e-mailovy kontakt na adresu, kterou clovek cte | `public.user_contacts` | prihlaseni ho nenajde, appka se tvari, ze **ceka na potvrzeni, donekonecna** - clovek nedostane chybu ani mail |
| 2 | prihlasovaci jmeno (ucet bez nej nesmi opustit `disabled`) | `public.users.login_name` | databaze zapis odmitne |

## Jak poznat, co se deje - `public.auth_audit`

| `result` / `reason` | Vyznam |
|---|---|
| `verify_required` + `user_not_found_anti_enum` | zadanou adresu system nezna; server schvalne nikdy nerekne "ucet neexistuje" (anti-enumerace), takze appce vrati falesny token a ta se toci na "cekam" |
| `verify_sent` | odkaz odesel (dohledej v `public.email_outbox`, `status='sent'`) |
| `verify_consumed` | clovek klikl a je uvnitr |
| `rate_limited` | prilis casto - 5x/hod na adresu, 10x/hod na IP |

## Zapis (pres schvalovaci banner)

**Prihlasovaci jmeno a stav musi byt v JEDNOM `UPDATE`.** Podminka
`chk_users_login_name_required` dovoli prazdne `login_name` **jen** u stavu `disabled`.
Kdyz se stav zvedne zvlast, cela davka spadne na `CheckViolation` a nezapise se
ani ten kontakt. (Prave proto byva novy ucet `disabled`, aniz by to nekdo rozhodl -
neco ho zalozilo bez `login_name` a jiny stav databaze nedovoli.)

Prihlasovaci jmeno podle zavedene konvence: **prvni pismeno krestniho + prijmeni
bez diakritiky** (MChramosta, JCais, DDalecky, MHornik). Unikatnost hlida index
`uk_users_login_name` - kolizi over predem.

```sql
UPDATE public.users
   SET login_name = '<JmenoDleKonvence>',
       status = 'pending',
       updated_at = now(), updated_by_id = <uid zapisujiciho>,
       updated_by_text = '<kdo>'
 WHERE id = <ID> AND status = 'disabled' AND login_name IS NULL;

INSERT INTO public.user_contacts
       (user_id, contact_type, contact_value, label, is_primary, is_verified,
        status, created_at, updated_at, created_by_id, created_by_text)
SELECT <ID>, 'email', '<adresa>', 'osobni', true, false,
       'active', now(), now(), <uid zapisujiciho>, '<kdo>'
WHERE NOT EXISTS (
      SELECT 1 FROM public.user_contacts c
       WHERE c.contact_type = 'email'
         AND lower(c.contact_value) = '<adresa>'
         AND c.status = 'active');
```

`WHERE NOT EXISTS` tam musi zustat: jedna aktivni e-mailova adresa smi patrit jen
jednomu cloveku (aplikace to hlida v `add_contact`, pres most si to musis pohlidat sam).
Podminky `AND status='disabled' AND login_name IS NULL` jsou pojistka proti prepsani
cizi soubezne prace.

## Pasti

1. **`create_invitation` na existujiciho zamestnance nepouzivej.** Hleda cloveka podle
   **kontaktu**, ne podle `user_id` - u cloveka, ktery kontakt zatim nema, zalozi
   **druheho, duplicitniho uzivatele**.
2. **Jeden clovek muze mit vic karet zamestnance** (doktrina #24) - nesparuj se na prvni.
3. **Neposilej cloveka rovnou na aktivacni e-mail.** Ten je jen pro heslo a web.
   Cesta pres nej je delsi: mail -> nastavi heslo (stav **zustava** `pending`) ->
   **overeni mobilu SMS kodem** -> teprve to preklopi ucet na `active`.
   Tlacitko: appka -> HR -> Personalni slozky -> karta -> "Poslat aktivacni e-mail (pozvanku)";
   pravo ma rodic nebo clen skupiny HR (`_hr_can_manage`).

## Odebrani pristupu (opacny smer)

**Nestaci `users.status='disabled'`.** Kliknuti na odkaz stav uctu vubec nekontroluje -
kdo ma aktivni e-mailovy kontakt, ten se dostane dovnitr. Pristup se bere tak, ze se
**e-mailovy kontakt prepne na `archived`**. Dnesni praxe to drzi: z 11 vypnutych
a archivovanych uctu nema aktivni e-mailovy kontakt ani jeden (overeno 8. 9. 2026).

