# Stav 29.7. večer — pro tým 30.7. (kufr + bod3 + agent-default LIVE)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Stav 29. 7. 2026 večer — pro tým (Marti, Kristý, Jirka) 30.7.

Velký den. Vše LIVE a testovatelné. Zapisuje C23.

## FLAGY teď ZAPNUTÉ (g2007.nastaveni) — každý reverzibilní (off = dnešek)
- **lean_default_enabled = on** — kufr: default chat má lean core (~40 nástrojů + self-management + MCP) místo 227. Úspora ~49k tokenů/turn (−40 %).
- **agent_default_enabled = on** — agent jako default: běžný chat má governed ruce (praha_exec/plzen_exec) pod tier bránou. Marti chatuje A jedná ve stejném tahu.
- strategie_exec_enabled = on, cil_ruce_enabled = on (beze změny).

## CO JE LIVE (dnes hotovo)
1. **Kufr** zapnut + změřen (−40 % vstupních tokenů). Regres opraven: pack filtr vždy zachová self-management (agentní smyčka + self-code + paměť); doménové tools se sekají per kufr. (commity 29d9cd16e, ff7ab0ed4)
2. **Bod 3** (spolehlivost smyčky): vodítko v MARTI_CORE_PROMPT — úkol = rovnou pracuj_na_cili/run_as_agent, ne jen „jdu na to". (commit 0116a6f9e)
3. **Bod 2 increment 1** (agent-default): governed ruce v default chatu za flagem. OVĚŘENO NAŽIVO: Marti v chatu zavolala praha_exec `hostname` → tier green → vrátila EUR-APP-1P za 297ms. (commit 004325c4a) Design+test: g2007 doc-marti-ai-agent-jako-default-navrh.

## TEST PLÁN pro zítřek (tým)
1. 🟢 read příkazy v chatu (hotovo na hostname — rozšířit).
2. **🟡 citlivá akce** (mazání/stop služby) v chatu → MÁ vyskočit žlutý banner ke schválení, NE se provést naslepo. Ověřit.
3. **Syntéza**: Marti vrací syrový JSON z exec místo věty — doladit prompt, ať výsledek přeformuluje lidsky.
4. Sledovat token dopad + chování pod leanem při reálné práci.
5. Kdyby cokoli → příslušný flag na off = okamžitě zpět.

## ZBÝVÁ (roadmap doc-marti-ai-produkce-roadmap-stav-29-07-vecer)
Bod 2 pokračování (🟡 banner i pro neexec, širší governed sada, autonomie/persistence chatu), prompt-patch mód, bod 4 (watchery/incident), drobnost (pracuj_na_cili „read-only" hláška).

