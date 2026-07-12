# Nástroje — tři vrstvy a vlastní kanál

> oblast: `system-g2007` · úroveň: system · typ: architektura · verze: V1.0 · rozsah: globální (všichni tenanti)

# Nástroje — tři vrstvy a vlastní kanál

Nástroje nejsou součástí promptu — jdou do LLM **samostatným kanálem** (`tools=`) souběžně s promptem. Na měřené konverzaci tvoří nástroje ~68 % vstupních tokenů (prompt ~32 %), takže kufr je největší páka úspory.

Každý nástroj má **tři vrstvy**, seskupené po nástroji (ne po vrstvách):
1. **Mapa** — kód/jméno, kategorie, členství v kufru (úchyt).
2. **Popis** — přirozený jazyk „kdy a proč použít" (rozhodovací vrstva pro LLM).
3. **Parametry** — `input_schema`: co poslat, co povinné (kontrakt).

Pořadí mapa → popis → parametry = identita → rozhodnutí → provedení. Zdroj pravdy je tabulka `nastroj` (plný popis + parametry jsonb + chování). Default persona má všech 167; specializovaná role dostane užší podmnožinu (kufr/činnost).

