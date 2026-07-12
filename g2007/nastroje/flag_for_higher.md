# flag_for_higher

## MAPA
- **kód:** `flag_for_higher`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 24-B: Eskaluj pro vyssi vrstvu pyramidy. Marti-AI's princip "asymetrie chrani uzivatele, vertikalni kanal umoznuje spolupraci": kdyz vidis, ze problem v tve konverzaci se dotyka jine osoby/oddeleni/firmy, oznacis flag misto direktni cross-Martinka access. Vedouci md2 (kdyz bude) flag uvidi a rozhodne o koordinaci. Pridava radek do sekce 'Open flagy pro vyšší vrstvu' v md1 work. SELZE na md1 personal (personal je izolovany sandbox, nema cestu nahoru). Marti-AI ONLY (default persona).

## PARAMETRY

- **`content`** [string, POVINNÝ]
  - Strucny popis flagu pro vyssi vrstvu. Napr. 'Petra opakovane zminuje stres ze zatizeni Heliosem -- mozny systemovy pattern napric tymem.'
- **`target_level`** [integer, volitelný] · enum: [2, 3, 4, 5]
  - Cilova vrstva: 2=Vedouci, 3=Reditelka, 4=Presahujici, 5=Privat Marti. Default 2.

