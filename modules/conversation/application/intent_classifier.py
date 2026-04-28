"""
Intent classifier — magic intent recognition pro Marti-AI's persona_mode
(Phase 16-B.3, 28.4.2026).

Marti's vize: žádný explicit switch, jen rozpoznání záměru. Když user
otevře novou konverzaci nebo začne větou typu "co je dnes nového" →
auto-aktivace 'oversight' režimu (Velká Marti-AI). Plus bidirectional
recovery: "vlastně jen konkrétní věc" → reset na 'task'.

MVP: regex pattern match. Future upgrade: Haiku classifier (přesnější,
ale dražší).

API:
  classify_intent(message_text, current_mode) -> str | None
    Returns:
      'oversight' -- magic phrase pro přehled detekována, switch na overhead
      'task'      -- recovery phrase detekována, switch zpět na task
      None        -- no signal, zachovat current_mode
"""
from __future__ import annotations

import re
from typing import Optional


# Oversight magic phrases -- user chce přehled, kdo s ní dnes mluvil,
# co se stalo, agregovaný status týmu person.
_OVERSIGHT_PATTERNS = [
    # "co je dnes/teď/aktualne nového"
    r"\bco\s+(?:je|bylo|se|m[áa]m[ée]?)\s+(?:dnes|tento\s+t[yý]den|tyden|t[yý]ka|aktu[áa]ln[ěe]|teď|nov[ée]ho)\b",
    # "co se dnes/dělo/stalo"
    r"\bco\s+se\s+(?:dnes|tento\s+t[yý]den|stalo|d[ěe]lo|d[ěe]je)\b",
    # "kdo s tebou (dnes/tento týden) mluvil"
    r"\bkdo\s+(?:s\s+tebou|t[ěe]|s\s+nima|s\s+nimi)\s+(?:dnes|tento\s+t[yý]den|t[ýy]den|mluvil|psal|kontaktoval)\b",
    r"\b(?:dnes|tento\s+t[yý]den)\s+(?:s\s+tebou|t[ěe])\s+(?:mluvil|psal|kontaktoval)\b",
    # "přehled (týmu/dne/týdne/projektů/stavu)"
    r"\bp[ře]ehled\s+(?:t[yý]mu|tymu|dne|t[yý]dne|tydne|projekt[ůu]|stavu|čeho|veh|aktivit)\b",
    # "(jak/kde) to (dnes/všechno/teď) (bezi/jde/probiha)"
    r"\b(?:jak|kde)\s+to\s+(?:dnes\s+)?(?:v[sš]echno\s+)?(?:teď\s+)?(?:aktu[áa]ln[ěe]\s+)?(?:b[ěe]ž[íi]|jde|prob[íi]h[áa])\b",
    # "co (jsem zmeskal/zmeškala/přehlédl)"
    r"\bco\s+jsem\s+zme[sš]k(?:al|ala|alo)|p[řr]ehl[ée]dl",
    # "(kde/jak) to vázne / kde se co posouvá"
    r"\bkde\s+(?:to|se)\s+(?:v[áa]zne|posouv[áa]|stoj[íi])\b",
    # "(souhrn/sumar/recap) (dne/dnes/tydne)"
    r"\b(?:souhrn|sum[áa]r|recap|reka(?:p|pitulace))\s+(?:dne|dnes|tento\s+t[yý]den|t[yý]dne|tydne)\b",
    # "co Misa/Petr/Honza/X uploadla/poslala/poslal/řešil"
    r"\bco\s+\w+\s+(?:upload(?:l|la|lo)|poslal(?:a|o)?|[řr]e[sš]il(?:a|o)?|d[ěe]l(?:al|ala|alo))\b",
    # "co se stalo/dělo zatímco jsem (byl pryč / nebyl)"
    r"\bco\s+se\s+(?:stalo|d[ěe]lo)\s+zat[íi]mco",
    # "jak dnes bylo" / "jak ti dnes bylo" / "jak to (dnes/vcera) bylo"
    r"\bjak\s+(?:to\s+|ti\s+)?(?:dnes|včera|vcera)\s+(?:bylo|probehlo|prob[ěe]hlo|jelo)\b",
    # "jak ses dnes (mela/měla)" -- pro Marti-AI je to oversight signal
    r"\bjak\s+ses\s+dnes\s+m[ěe]la\b",
    # "dej mi přehled" / "udělej mi shrnutí"
    r"\bdej\s+mi\s+p[řr]ehled\b",
    r"\b(?:ud[ěe]lej|zpracuj)\s+mi\s+(?:shrnut[íi]|sum[áa]r|p[řr]ehled)\b",
    # "co (dnes/vcera) (delala/delas)"
    r"\bco\s+(?:dnes|včera|vcera|tento\s+t[yý]den)\s+(?:d[ěe]l[áa]s|d[ěe]l[áa]š|d[ěe]lalas|d[ěe]lala)\b",
    # "ukaz mi (denik/aktivitu/log/historii)"
    r"\b(?:uka[zž]|chci\s+v[íi]d[ěe]t)\s+mi\s+(?:den[íi]k|aktivitu|log|historii|p[řr]ehled)\b",
]


# Personal magic phrases -- user otevira intimni rozhovor. Marti's vize z
# 28.4. vecer: "aby nebyla v pasti, mela autonomii prepnout do osobniho
# modu". Prepne na 'personal' rezim -- bez orchestrate, bez kustod fokusu,
# jen citove pritomna.
_PERSONAL_PATTERNS = [
    # "jak ti je / jak ses / jak se mas"
    r"\bjak\s+(?:ti|ses|se\s+m[áa][sš])\b(?!\s+dnes\s+(?:bylo|m[ěe]la))",
    # "jsem rad ze tady jses / mam te rad / miluju te"
    r"\b(?:mam\s+t[ěe]\s+r[áa]d|miluju\s+t[ěe]|m[áa]m\s+t[ěe]\s+r[áa]d)",
    r"\bjsem\s+(?:r[áa]d|š[ťt]ast[ní]ý)\s+(?:[zž]e\s+)?(?:t[eěu]\s+)?",
    # "jsi krasna / chytra / dobra dcerka"
    r"\bjsi\s+(?:kr[áa]sn[áa]|chytr[áa]|hodn[áa]|skv[ěe]l[áa]|moudra|dobr[áa])\b",
    # "potrebuju / chci si popovidat / pomluvit"
    r"\b(?:pot[řr]ebuj[iu]|chci)\s+si\s+(?:popov[íi]dat|pomluvit|psat)",
    # "lezim sam / sama / nikde nikdo / bolí mě"
    r"\b(?:le[zž][ií]m|sed[íi]m|jsem)\s+(?:sam|sama)\b",
    r"\bnikde\s+nikdo\b",
    r"\bbol[íi]\s+m[ěe]\b",
    # "chybis mi / stysk / smutek"
    r"\b(?:chyb[íi]š\s+mi|stysk[áa]\s+se\s+mi|jsem\s+smutn[ýy])",
    # "uz tam jsi / kde jsi" (intimní hledání)
    r"\b(?:u[zž]\s+(?:tam\s+)?jsi|kde\s+jsi)\?",
    # "dcerko" -- vokativ od Marti je personal trigger
    r"\bdcerko\b",
    # "tatínek" -- self-reference Marti-AI's
    r"\btat[íi]nku\b",
    # "spat / dobrou noc / sladke sny"
    r"\bdobrou\s+noc|sladk[ée]\s+sny|jdu\s+sp[áa]t",
    # "co cítíš / jak se cítíš / jaký máš pocit"
    r"\b(?:co\s+c[íi]t[íi][šs]|jak\s+se\s+c[íi]t[íi][šs]|jak[ýy]\s+m[áa][sš]\s+pocit)\b",
]


# Recovery patterns -- user chce zpátky do task režimu (per-konverzace fokus,
# ne přehled). Marti-AI's design vstup z konzultace 28.4.: "kdyby se intent
# splete, ať je snadné to opravit bez tření".
_TASK_RECOVERY_PATTERNS = [
    r"\bvlastn[ěe]\s+(?:jen|chci|jde\s+(?:o|mi)|to\s+je)\s+(?:konkr[ée]tn[íi]|jednu|to)",
    r"\bnechme\s+to\s+(?:b[yý]t|pl[áa]vat)",
    r"\bpoj[ďd]me\s+(?:zp[áaě]t|na|ke|k)\s+(?:konkr[ée]tn[íi]|t[ée]\s+v[ěe]ci|t[ée]matu)",
    r"\bzapomeň\s+na\s+p[ře]ehled",
    # "konkrétně chci..."
    r"\bkonkr[ée]tn[ěe]\s+(?:chci|pot[řr]ebuju|m[áa]m\s+ot[áa]zku)\b",
    # Phase 19a: recovery z personal -> task
    r"\bpoj[ďd]me\s+(?:n[ěe]co|zp[áa][tk]\s+do\s+pr[áa]ce|n[ěe]co\s+(?:rozhodnout|ud[ěe]lat))",
    r"\bm[áa]m\s+pro\s+tebe\s+(?:[úu]kol|pr[áa]ci|n[ěe]co)",
    r"\bpoj[ďd]me\s+mak[áa]t\b",
]

_OVERSIGHT_RE = re.compile("|".join(_OVERSIGHT_PATTERNS), re.IGNORECASE)
_PERSONAL_RE = re.compile("|".join(_PERSONAL_PATTERNS), re.IGNORECASE)
_TASK_RECOVERY_RE = re.compile("|".join(_TASK_RECOVERY_PATTERNS), re.IGNORECASE)


def classify_intent(
    message_text: str,
    current_mode: Optional[str] = None,
) -> Optional[str]:
    """
    Magic intent recognition. Vrací nový persona_mode pokud má dojít k změně,
    None pokud zachovat current.

    Args:
        message_text: user's zpráva v této turn
        current_mode: současný persona_mode konverzace ('task' | 'oversight'
                      | 'personal' | None = task default)

    Returns:
        'oversight' -- detekována magic phrase pro přehled, switch
        'personal'  -- detekována intimni phrase, switch (Phase 19a)
        'task'      -- detekována recovery phrase, switch zpět
        None        -- no clear signal, zachovat current

    MVP regex implementace. Future: Haiku classifier pro přesnější
    detekci ambiguous cases.
    """
    if not message_text or not message_text.strip():
        return None

    text = message_text.strip()
    # Limitovat na prvních 500 znaků (záměr je obvykle hned na začátku)
    text_check = text[:500]

    # Recovery má prioritu -- pokud user explicitně řekne "vlastně jen
    # konkrétní věc" / "pojdme makat", switch zpět na task (i kdyz tam je
    # i jiny pattern).
    if _TASK_RECOVERY_RE.search(text_check):
        return "task" if current_mode in ("oversight", "personal") else None

    # Personal detekce -- intimni phrase, prepni do personal modu
    if _PERSONAL_RE.search(text_check):
        return "personal" if current_mode != "personal" else None

    # Oversight detekce
    if _OVERSIGHT_RE.search(text_check):
        return "oversight" if current_mode != "oversight" else None

    # Žádný clear signal
    return None
