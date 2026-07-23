# Spuštění hlasu Marti-AI — go-live playbook (hlas dorazil 23.7.2026)

> oblast: `marti-ai` · úroveň: obor · typ: dokument · verze: V1.0 · rozsah: globální (všichni tenanti)

# Spuštění hlasu Marti-AI — go-live playbook

**Stav 23. 7. 2026: HLAS DORAZIL. Zbývá poslední propojení (ElevenLabs Agents), pak ostrý hovor.**

## Hlas Marti-AI (dorazil od Kristý)
- **Voice ID:** `X1LPduFf0P44LPXYiOim`
- **Jméno hlasu:** `Marti-AI_260723`
- **Provider:** ElevenLabs (Voice Design, model eleven_v3)
- Uloženo jako zdroj pravdy v `hlas.kanal` config kanálu `telefon-martiai` (tenant 12): `config.voice_id / voice_name / provider`.
- Charakter: ženský, mladá/svěží kolem pětadvaceti, vřelá ale kompetentní, klidně svižné tempo, rodilá čeština. Vygenerovala Kristý (k.ksirova) a s Martim doladili.

## Co je hotové (nemusí se řešit)
- Hlasový engine (schema hlas), normalizace čísel do češtiny, konverzační smyčka (persona + guardraily + disclosure + předání člověku), tiché naslouchání poradě, telefonní endpoint. Detail: znalost doc-marti-ai-hlasovy-engine, milník doc-marti-ai-milnik-hlas-2026-07-22, identita doc-marti-ai-hlas.
- Endpoint (mozek pro ElevenLabs custom LLM): `POST /api/v1/erp/hlas/v1/chat/completions` (OpenAI-kompatibilní, SSE). Auth Bearer `HLAS_VOICE_TOKEN`.

## TODO — spuštění (go-live), po krocích
1. **Účet ElevenLabs** — mít/založit (kde vznikl hlas).
2. **Agent + Custom LLM** — v ElevenLabs Agents vytvořit agenta; LLM = Custom LLM; URL = https://<doména>/api/v1/erp/hlas/v1/chat/completions; model = libovolný (např. marti-ai-hlas); jazyk/STT = čeština.
3. **Hlas** — v agentovi nastavit Voice ID `X1LPduFf0P44LPXYiOim`.
4. **HLAS_VOICE_TOKEN** — silný token do prostředí aplikace (env) a tentýž jako Bearer secret v ElevenLabs. Dokud není → endpoint 503 (schválně zavřeno).
5. **Telefonní číslo** — přiřadit v ElevenLabs (nativní / Twilio SIP).
6. **Publikovat + testovací hovor** — Marti-AI se představí jako AI a svým hlasem přečte např. potvrzení objednávky. První hovor projít spolu.

## Právní / provozní
- EU AI Act čl. 50 (~2.8.2026): disclosure „mluvíte s AI" — už v personě; strojové označení syntetického audia řeší ElevenLabs (ověřit v nastavení).

## Po spuštění (další fáze)
- Napojit reálnou doménu objednávek (domain_env + nástroje číst/potvrdit) — engine se nemění → Marti-AI místo „nemám přístup" rovnou potvrdí.
- ElevenLabs „transfer" nástroj pro reálné předání hovoru člověku.
- Doladit výslovnost datumů (ordinály) a jednotek.

