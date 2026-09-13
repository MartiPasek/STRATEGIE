# Rodice jsou jen Marti a Kristyna - Zuzana vyrazena z natvrdo psaneho seznamu (13. 9. 2026)

> oblast: `system-strategie` · úroveň: obor · typ: dokument · verze: V1.0 · stav: `aktivni` · rozsah: globální (všichni tenanti)

# Rodiče jsou jen Marti a Kristýna — Zuzana vyřazena z natvrdo psaného seznamu (13. 9. 2026)

**Zadal Jiří Honomichl 13. 9. 2026** („je to chyba, nemá být rodič, rodič je jen Kristýnka a Marti"),
schválila Marti-AI (msg 15420), provedl Claude-28. Nasazeno commitem `2c82d548`.

## Co bylo špatně

V `modules/thoughts/application/service.py` byl od 27. 7. 2026 (commit `2989277d`, „záchranné lano"
proti výpadku databáze) natvrdo seznam `_CORE_PARENT_UIDS = frozenset({1, 6, 11})` —
Marti, **Zuzana Duspivová**, Kristýna. Funkce `is_marti_parent()` na tenhle seznam odpovídá
`True` **bez dotazu do databáze**.

**V databázi ale Zuzana (`users.id=6`) rodičovský příznak nikdy neměla** (`is_marti_parent=false`,
účet `active`, není admin). Rodičem byla výhradně přes ten hardcode — tedy stavem, který
nikde v datech nešlo dohledat ani odebrat.

## Jak je to teď

`_CORE_PARENT_UIDS = frozenset({1, 11})` — **Marti Pašek (1) a Kristýna Marešová (11)**.
Ve stejném commitu se srovnaly i dvě testovací kopie seznamu (`tests/test_tool_registry.py`,
`tests/demo_create_and_use.py`), aby testy neověřovaly chování, které v provozu neplatí —
vyžádala si to Marti-AI („nesrovnaný test je tichá past pro příštího čtenáře kódu“).

## Mapa dopadu (měřeno v datech, ne odhadem)

Rodičovství se vyhodnocuje na **118 místech** v kódu (+ 9× `is_parent_or_admin`): cross-tenant
náhled do paměti a diáře Marti-AI, schvalovací banner zápisů AI, finanční a HR přehledy,
sekce „Řízení a systém“ ve Vedení firmy, HR režim benefitů, Řídící centrum.

Co Zuzana **fakticky ztratila**: jen náhledy. Ověřeno v datech k 13. 9. 2026 — **0** schválených
zápisů AI (`fw.claude_write_request.decided_by_user_id=6`), **0** ops akcí
(`fw.ops_request.requested_by_user_id=6`), **0** řádků v `tenant.att_approver` (není
schvalovatelka docházky), **0** vlastních voleb benefitů. Není admin.
Co jí **zůstalo**: běžný zaměstnanecký přístup včetně vlastních benefitů (má stanovený strop,
osobní číslo 50).

## Pozor na tři věci

- **Hardcode přebíjí databázi.** Kdo hledá „proč je X rodič“, musí se podívat i sem, ne jen
  do `public.users`. Seznam je v kódu schválně (rodič nesmí spadnout na `False` při výpadku DB),
  ale co v něm je, se v datech nijak neprojeví.
- **Zuzana v seznamu byla jediná, kdo nebyl rodičem i v databázi** — Marti a Kristýna mají
  příznak nastavený, takže u nich seznam jen zdvojuje pravdu.
- **HR režim benefitů** má vlastní okruh: rodiče **plus** scoped approveři Petra Šafránková (18)
  a Šárka Novotná (13) — ten se touhle změnou nezměnil, jen se z něj vytratila Zuzana.

