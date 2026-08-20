# Práva: rodič/admin nikdy nesmí spadnout na False (záchranné lano)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Práva: rodič/admin nikdy nesmí spadnout na False (záchranné lano)

**Datum:** 27.7.2026 · **Instance:** C23 · **Zadal:** Marti ("rodič smí úplně vše; blokovat rodiče je nebezpečné, mohl by z toho být fatální průšvih").

## Symptom
Rodič (Marti, uid 1) intermitentně dostával 403 "nemáš přístup / nejsi rodič" na parent-gated nástrojích (Banka, VP věž, Neschopenky…), přestože /app/whoami ho ukazoval správně jako "Marti". Chvíli šlo, chvíli ne.

## Root cause
modules/thoughts/application/service.py::is_marti_parent() bylo defenzivní: při JAKÉKOLI výjimce při DB čtení (transientní chyba session/poolu) tiše vracelo False. Skoro všechny brány na téhle funkci visí — přímo (_is_parent u Banky/VP) i nepřímo (parent-bypass ve _has_capability, který má "if is_marti_parent(uid): return True"). Jeden zádrhel na DB tedy shodil rodiče na "ne-rodiče" napříč celým systémem naráz. whoami fungoval, protože is_marti_parent vůbec nevolá (jen resoluci uid).

## Co to NEBYLO (ověřeno, ať se to znovu nehoní)
- NE data: users.id=1 má is_marti_parent=True, is_admin=True.
- NE impersonace: 0 otevřených řádků fw.impersonation_log.
- NE shared_active/switch: živý token mapuje na uid 1; řádek na u104 (Demo) je na revokovaném tokenu (neškodí).
- NE ambasador: _AMBASSADOR_PERSONAL_UID=1, pro uid 1 se větev vždy přeskočí.
- NE jiná DB: is_marti_parent i bridge čtou tutéž database_data_url.

## Fix (commit 2989277d2)
Do is_marti_parent a is_admin_user přidán invariant:
1. Neměnné jádro _CORE_PARENT_UIDS={1,6,11} (Marti/Zuzana/Kristýna), _CORE_ADMIN_UIDS={1,11,20} (Marti/Kristýna/Jiří) — zkratují na True BEZ DB. DB hiccup je nemůže shodit.
2. Last-known-good cache pro ostatní: jednou potvrzený rodič se při pozdější chybě DB nepřeklopí na False.

## Princip (DRŽ)
Rodič/sysadmin NIKDY nesmí být zablokován kvůli transientní chybě infrastruktury. Defenzivní "při chybě vrať False" je u rodičovské role NEBEZPEČNÉ — pro potvrzené jádro fail-open, ne fail-closed. Když přibude/ubude rodič, uprav _CORE_PARENT_UIDS (zdroj pravdy = users.is_marti_parent).

## Otevřené (samostatné, dnešní problém NEzpůsobily)
Slabiny resolveru identity v modules/erp/api/router.py: _active_imp_target bez 8h okna (v docstringu je, v SQL ne); bearer větev čte tenant.shared_active bez ORDER/LIMIT (nedeterministické); /app/shared/switch nastaví cookie user_id na 30 dní bez "přepni zpět na sebe". Zvážit dorazit.

