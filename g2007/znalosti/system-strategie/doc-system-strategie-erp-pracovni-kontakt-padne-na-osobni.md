# ERP: sloupce „Pracovní e-mail" a „Pracovní mobil" ukazují OSOBNÍ kontakt, když firemní chybí

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# ERP: „pracovní" kontakt v seznamu lidí padá na osobní

**Zjištěno 8. 9. 2026 (Jirka + C28)** při stavbě detailu člověka v agendě mobilu.

## Co se děje

V ERP na kartě zaměstnance (seznam lidí, `apps/api/static/karta_zamestnance.html`)
jsou sloupce nadepsané **„Pracovní e-mail"** a **„Pracovní mobil"**. Plní se takto:

```js
const _mailv = p.email || p.prac_email;
const _telv  = p.telefon || p.prac_telefon;
```

Server přitom vrací:

| pole | čím je |
|---|---|
| `email` | `COALESCE(company_email, personal_email)` |
| `telefon` | `COALESCE(company_phone, personal_phone)` |
| `prac_email` | jen `company_email` |
| `prac_telefon` | jen `company_phone` |

Protože se bere **`email` jako první** a to už samo padá na osobní, sloupec nadepsaný
„Pracovní" ve skutečnosti **ukazuje osobní e-mail a osobní telefon** u každého, kdo nemá
vyplněný firemní kontakt.

## Kolika lidí se to týká

Z **84 lidí v agendách** (stav k 8. 9. 2026):

- firemní e-mail má **45**, u **31** ERP ukazuje jejich **osobní** e-mail,
- firemní telefon má **38**, u **37** ERP ukazuje jejich **osobní** telefon.

## Rozhodnutí

**Rozhodl Jirka Honomichl 8. 9. 2026: v ERP se to nechává, jak to je.** Není to opomenutí
ani chyba k opravě — kdo to bude číst později, ať to neopravuje bez ptaní.

**V mobilní aplikaci to ale platit nesmí:** tam se osobní e-mail ani osobní telefon
neposílají vůbec, ani v datech. Kdo nemá firemní kontakt, má napsáno „nemá firemní email"
a „nemá uvedené pracovní tel. číslo".
Viz [[doc-dochazka-agenda-detail-cloveka-kontakt-a-budouci-absence]].

## Poznámka k názvosloví

**Druhé, samostatné „pracovní" číslo v databázi neexistuje.** „Firemní telefon" (osobní karta)
a „Pracovní mobil" (seznam lidí) jsou dvě jména téže kolonky `tenant.user_self_data.company_phone`.
Ověřeno prohledáním všech sloupců schémat public/tenant/fw/g2007 na email, telefon a mobil.

