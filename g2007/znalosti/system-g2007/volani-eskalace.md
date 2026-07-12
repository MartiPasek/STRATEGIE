# Jednotné volání nástrojů + chybová eskalace

> oblast: `system-g2007` · úroveň: system · typ: architektura · verze: V1.0 · rozsah: globální (všichni tenanti)

# Jednotné volání nástrojů + chybová eskalace

Nástroj je sdílená schopnost volatelná třemi volajícími přes jeden dispatcher: **LLM, automat, člověk.**

- **LLM** jde mapa → popis → parametry → provedení (popis = rozhodovací vrstva).
- **Automat** popis přeskakuje (je naprogramovaný): mapa → parametry → provedení.

**Chybová eskalace (klíč bezpečnosti):** když automat zavolá nástroj a ten selže, chování `pri_chybe = 'eskaluj_llm'` vyvolá LLM s celým kontextem (jako běžný turn) a předá mu „zkusil jsem X s argumenty Y, selhalo Z". LLM se z chyby vzpamatuje stejně jako dnes. **Automat tak nikdy nezhorší stav oproti dnešku — při chybě se stane dneškem.** V řeči Graph7 je to přechodová podmínka: OK → další krok, CHYBA → eskaluj.

Kdo smí volat co, řeší práva (profese / kvalifikace / kufr) a příznak `automat_safe`.

