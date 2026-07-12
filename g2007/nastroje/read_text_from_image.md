# read_text_from_image

## MAPA
- **kód:** `read_text_from_image`
- **kategorie:** běžné (CORE)
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Faze 12a multimedia: OCR -- prepis text z OBRAZKU (kind='image') do textu. JEN pro IMAGE media, NEVOLEJ na AUDIO. Pro audio dostavas Whisper transcript automaticky v multimodal contextu.

Pouzij kdyz user nahral fotku dokumentu / uctenky / vizitky / screenshotu a chce z nej vytahnout text ('precti tu uctenku', 'jaky je na te vizitce telefon?'). Sonnet 4.6 zvlada OCR nativne, vcetne ceskeho textu. Vystup je strukturovany text (odsazeni / odrazky zachovane podle moznosti).

## PARAMETRY

- **`language`** [string, volitelný]
  - Hint pro OCR -- 'cs' (cestina), 'en', atd. Default 'cs'.
- **`media_id`** [integer, POVINNÝ]
  - ID media souboru (z media_files).

