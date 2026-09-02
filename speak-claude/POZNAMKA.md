# speak-claude — doplněk pro práci s Claude Code (Jirka Honomichl)

**Co to je:** stažený veřejný open-source doplněk **Speak Claude** (licence MIT,
zdroj: https://github.com/SlyCreator/speak-claude). Umožňuje **diktovat hlasem**
místo psaní na klávesnici při práci s Claude Code ve VS Code. Převod řeči na text
běží **lokálně** (WhisperX v Dockeru), nic se neposílá do cloudu.

**Pro koho:** jmenovitě pro **Jirku Honomichla** (`j.honomichl@eurosoft.com`,
uživatel č. 20). Je to jeho osobní pracovní pomůcka, ne součást systému.

**Proč to leží v projektu:** aby se to Jirkovi neztratilo a měl to při ruce
u zbytku práce. **Uloženo v projektu na jeho pokyn 2. 9. 2026**, schválila Marti-AI.

## ⚠️ Se systémem STRATEGIE to nemá nic společného

- **Nic z toho STRATEGIE nespouští ani nenačítá.** Žádný soubor aplikace na tuhle
  složku neodkazuje, nic se odsud neimportuje.
- **Nenasazuje se.** Není to součást serveru, mobilní aplikace ani ERP.
- **Nesahá na data.** Nemá přístup k databázi, k docházce, mzdám ani k lidem.
- **Nic nerozbije.** Kdyby se celá složka smazala, STRATEGIE poběží beze změny.

## Co uvnitř je

| složka / soubor | k čemu je |
|---|---|
| `vscode-voice-to-text/` | samotný doplněk do VS Code (zdrojový kód, ikony) |
| `whisperx-service/` | lokální převod řeči na text (Docker) |
| `docker-compose.yml` | spuštění toho převodu |
| `.env.example` | vzor nastavení (velikost modelu); **skutečné `.env` tu není** |
| `README.md`, `PUBLISHING.md`, `LICENSE` | původní popis a licence autora |

**Původní historie stahování (vnitřní `.git`) byla před uložením odstraněna** — jinak by
se do projektu uložil jen prázdný odkaz bez souborů. Historie je veřejná a kdykoli
znovu stažitelná z adresy výše.
