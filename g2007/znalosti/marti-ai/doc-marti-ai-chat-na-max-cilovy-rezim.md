# Chat na Max předplatné pro cílový režim

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Chat na Max předplatné pro cílový režim (Marti-AI)

**Datum:** 27. 7. 2026 · **Autor:** Claude-23 & Marti · **Stav:** nasazeno a ověřeno (commity 6cdd624d2, 5df780d5a)

## K čemu to je
Uživatel se zapnutým agentním/cílovým režimem má **chat na Max předplatném**, ne na
metered API. Dřív běžel na Max jen autonomní agent; samotný chat jel vždy metered.
Tohle dorovnává druhou půlku: v cílovém režimu jede na Max i konverzace.

## Jak to funguje
- **Gate (v kódu):** chat jede na Max jen když je uživatel admin/rodič A má
  `users.agent_enabled=true` A globální kill flag `g2007.nastaveni.martiai_chat_max_enabled='on'`.
  Jinak beze změny = metered. Ne-cíloví uživatelé nedotčeni.
- **Auth:** Max klient = `anthropic.Anthropic(auth_token=<OAuth z .credentials.json>,
  default_headers={'anthropic-beta':'oauth-2025-04-20'})`. Token se čte z Claude Code
  `.credentials.json` na cloud APP serveru. Messages API ten bearer bere (ověřeno).
- **Failover (pojistka):** když Max selže (vyčerpaný limit / odmítnutý bearer / expirace),
  chat okamžitě spadne na metered `api_key` a doběhne — nikdy neumře. Přesná příčina jde
  do warn logu.
- **Anti-drift modelu:** do promptu se dynamicky vkládá `[PROVOZNÍ KONTEXT]` se skutečným
  modelem (`_model`) a REÁLNĚ použitým enginem (po failoveru říká 'metered', ne 'Max').
  Marti tak model ani auth nehádá.

## Pojistky (v KÓDU, nezávisle na modelu)
1. Default metered cesta beze změny (bajt po bajtu) pro ne-cílové uživatele.
2. Gate na uživatele + globální kill flag `martiai_chat_max_enabled`.
3. Failover na metered = chat nikdy nespadne.

## Náklady / limity
Na Max chat čerpá **sdílený usage-limit pool** (5h rolling + týdenní strop), ne Kč.
Politika Anthropicu na programový provoz na předplatném je „pozastavená, ne zrušená" —
proto gate jen na cílový režim + failover. `cost_usd` v `llm_calls` je i na Max notional.

## Ověření
V `llm_calls` (kind='composer'): úspěšný Max = jeden čistý řádek bez `error`.
Odmítnutý bearer = řádek s `error` (401) + druhý metered retry. Pilot 27.7. na user id=1
dal jeden čistý řádek → Max funguje.

## Kód
`modules/conversation/application/service.py` — helpery `_chat_max_enabled`,
`_user_agent_enabled`, `_chat_max_token`, `_build_chat_client`; gate + failover + dynamický
`[PROVOZNÍ KONTEXT]` v composer completion. Kill flag `martiai_chat_max_enabled`.

