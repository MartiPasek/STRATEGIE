# Resolver identity — hardening 8h okno + deterministicke shared_active (28.7.)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Resolver identity — hardening (28.7.2026, commit 5660d581c)

Dokončeny 2 ze 3 slabin resolveru identity (navazuje na doc-system-strategie-prava-rodic-zachranne-lano sekci "Otevřené"). Stejná třída pastí jako demo cookie=104 z 27.7. (tiché vrácení špatné identity).

## 1. Impersonace s 8h oknem I V RESOLUCI
_active_imp_target (cookie cesta) i bearer větev v _resolve_uid_raw měly v SQL jen "ended_at IS NULL" — docstring sliboval "max 8 h", SQL ne. Přidáno AND started_at > now() - interval '8 hours'. Stará otevřená impersonace (>8h) už tiše nedrží rodiče/usera v cizí identitě.
- Bezpečné: fw.impersonation_log.started_at je NOT NULL DEFAULT now() (žádné null řádky).
- POZOR: UPDATE co při startu NOVÉ impersonace zavírá staré (UPDATE ... SET ended_at=now() WHERE parent_user_id=:p AND ended_at IS NULL, ~ř.26152) 8h okno mít NESMÍ — musí zavřít i starší než 8h. Nechán beze změny.

## 2. shared_active čteno deterministicky
Bearer _ov = SELECT user_id FROM tenant.shared_active WHERE token_hash=:h bylo bez ORDER/LIMIT → .scalar() bral libovolný řádek při víc záznamech. Přidáno ORDER BY set_at DESC LIMIT 1 (nejnovější přepnutí vyhrává). ON CONFLICT(token_hash) sice drží unikát, ale defenzivně determinismus.

## ZBÝVÁ (#3 — design pro Marti)
/app/shared/switch nastavuje user_id cookie na 30 DNÍ bez "přepni zpět na sebe" — stejná stranding třída jako demo. Ale je to legit feature (explicitní PIN switch na sdíleném telefonu), tak nechat na rozhodnutí: session-scoped? auto-revert? timeout? Nesahat unilaterálně.

## Úklid dat
Smazány mrtvé shared_active řádky na Martiho revokovaných tokenech (4 ks, past →Demo104 včetně). Na live tokenech zůstalo jen →Marti(1).

