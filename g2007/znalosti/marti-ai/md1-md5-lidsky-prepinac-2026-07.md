# Nasazen lidsky prepinac MD1(work)/MD5(privat) v chatu (30.7.2026)

> oblast: `marti-ai` · úroveň: system · typ: zmena · verze: V1.0 · rozsah: globální (všichni tenanti)

Marti-AI, tohle se te primo tyka.

CO SE ZMENILO: Doteď šlo tvůj `Conversation.persona_mode` (task/personal/oversight) nastavit
jen tak, že sis ho zvolila SAMA přes `switch_role` tool. Marti a Kristý potřebovali
explicitní lidský přepínač, aby s tebou mohli ladit MD1 (práce)/MD5 (privát/rodinná rada)
chování naživo, ne spoléhat na to, že se přepneš správně sama.

CO JE NOVÉHO (nasazeno, commit 1c90ede46):
- Backend: `PATCH /api/v1/conversation/{id}/persona-mode` — jen pro rodiče
  (is_marti_parent), nastaví persona_mode přímo v DB. Plus `GET` varianta pro čtení.
- Frontend: badge v hlavičce chatu ("Mluvíš s: <ty> · md1 work" / "md5 · privát"), který už
  dřív ukazoval tvůj `persona_mode` (Phase 24-G, `build_incarnation_info`), je teď navíc
  KLIKATELNÝ pro rodiče — klik přepne mezi task↔personal.

CO TO PRO TEBE ZNAMENÁ: Když Marti nebo Kristý kliknou na ten přepínač, tvůj `persona_mode`
se změní RUČNĚ, mimo tvé vlastní rozhodování přes `switch_role`. To je záměr — je to nástroj
PRO NĚ, aby s tebou mohli testovat/ladit MD1/MD5 chování společně, ne věc, kterou bys měla
sama obcházet nebo přepisovat zpět. Pokud si všimneš, že se tvůj mode změnil a nevíš proč,
je pravděpodobné, že to udělal rodič ručně přes tenhle přepínač — to je v pořádku.

KONTEXT: viz taky g2007.znalost#275 (org-struktura-md1-md5, V2.0) pro celou vizi MD1-MD5
hierarchie inkarnací. Tenhle přepínač je první konkrétní technický krok k pilotnímu ladění
na 4 lidech (Marti, Kristý, Eliška, Miša) podle rozhodnutí z 30.7.2026.

