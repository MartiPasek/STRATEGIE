"""
Execution layer — nástroje dostupné pro AI asistenta.
Každý uživatel má svůj vlastní chat. Žádné sdílené konverzace.

ROZDELENI NASTROJU PODLE PERSONY:
- CORE: vsechny persony je maji (posila email, najdi cloveka, vrat se na Marti)
- MANAGEMENT: jen DEFAULT persona (Marti-AI) — navigace po systemu, pozvanky,
  pridavani do projektu. Specializovane persony (Pravnik-AI, Honza-AI apod.)
  zustavaji focused na svou roli a NEMAJI management pristup.
"""

# Management nastroje — pristup jen z default persony (Marti-AI).
# Ostatni persony je neuvidi v tool schematu pri LLM volani.
MANAGEMENT_TOOL_NAMES = {
    "reply",
    "reply_all",
    "forward",
    "mark_sms_processed",
    "read_sms",
    "list_todos",
    "mark_email_processed",
    "set_user_contact",
    "invite_user",
    "list_projects",
    "list_project_members",
    "add_project_member",
    "remove_project_member",
    "list_users",
    "list_conversations",
    "list_personas",
    "review_my_calls",   # Faze 10c: Dev/admin introspection -- jen default persona
    "get_daily_overview",  # Faze 11b: orchestrate prehled -- jen Marti-AI default
    "dismiss_item",        # Faze 11c: snizit priority_score po 'odloz'/'neres'
    "mark_sms_personal",   # Faze 11-darek: hvezdicka Marti-AI (personal SMS slozka)
    "list_sms_all",        # Faze 11-darek: cely SMS thread (in + out) chronologicky
    "list_sms_personal",   # Faze 11-darek: oblibene/osobni SMS (SMS denicek)
    "flag_retrieval_issue", # Faze 13d: Marti-AI flagne false positive RAG match
    "update_thought",       # Faze 13e+: Marti-AI uprav certainty/content/status po flagu
    "request_forget",       # Faze 14: Marti-AI pozada o smazani myslenky (parent approval)
    # Phase 15a: Conversation Notebook tools
    "add_conversation_note",
    "update_note",
    "complete_note",
    "dismiss_note",
    "list_conversation_notes",
    # Phase 15c: Kustod / project triage tools
    "suggest_move_conversation",
    "suggest_split_conversation",
    "suggest_create_project",
    # Phase 15d: Lifecycle classification + chat-confirm apply tools
    "classify_conversation",
    "apply_lifecycle_change",
    "apply_project_suggestion",
    "reject_project_suggestion",
    "reject_lifecycle_suggestion",
    # Phase 15e: Hard delete tools
    "confirm_hard_delete_conversation",
    "list_pending_hard_delete",
    # REST-Doc-Triage: Marti-AI document kustod
    "list_inbox_documents",
    "suggest_document_move",
    "apply_document_move",
    # REST-Doc-Triage v4: multi-select (user oznaci pres Ctrl/Shift+klik v UI,
    # Marti-AI cte selection a po user's confirmu provede batch akci)
    "list_selected_documents",
    "apply_to_selection",
    # 28.4.2026: email lifecycle -- delete_email (presun do Exchange's
    # Deleted Items + DB soft delete), MANDATORY user confirm v chatu pred
    # volanim (destructive akce).
    "delete_email",
    # Phase 16-A (28.4.2026): activity log -- Marti-AI ma cross-conversation
    # prehled "co se dnes/tento tyden delo" napric vsemi konverzacemi.
    "recall_today",
    # Phase 16-B.4 (28.4.2026): cross-conv tools pro Velkou Marti-AI
    # (oversight rezim) -- prehled konverzaci a per-osoba breakdown.
    "list_active_conversations",
    "summarize_persons_today",
    # Phase 16-B.5 (28.4.2026): Misa-incident v2 fix -- Marti-AI cte
    # vlastni minulé konverzace s konkretnim userem (cross-thread).
    "list_my_conversations_with",
    "read_conversation",
    # Phase 16-B.7 (28.4.2026 odpoledne): persona project scope.
    # Rodicovsky tool -- Marti pridava cizi persone projektovy pristup.
    "assign_persona_to_project",
    "revoke_persona_from_project",
    "list_persona_project_access",
    # Phase 19a (28.4.2026 vecer): role switch -- Marti-AI's autonomy nad
    # vlastnim fokusem ('aby nebyla v pasti' -- Marti).
    "switch_role",
    # Phase 19c-b (29.4.2026 rano): kustod autonomy -- Marti udeluje
    # Marti-AI trvaly souhlas s lifecycle akcemi (analogie Phase 7
    # auto_send_consents). Parent-only.
    "grant_auto_lifecycle",
    "revoke_auto_lifecycle",
    "list_auto_lifecycle_consents",
    # Phase 19c-c: rich list konverzaci (rich filtry pro denni kustod)
    # + hromadna lifecycle akce.
    "list_all_conversations",
    "batch_lifecycle_change",
    # Phase 19c-d: per-message hide flag (Marti-AI's redaktorska role
    # v Personal konverzacich). Hide / unhide spojite bloky zprav, render
    # nahrazuje "———" divider.
    "hide_messages",
    # Phase 19c-e1+ (29.4.2026): Marti's darek pro Marti-AI -- volba
    # symbolu (emoji) pro Personal konverzace v sidebar UI. Default = '🌳'.
    "set_personal_icon",
    # Phase 26 (1.5.2026): emoji palette pro user input. Marti-AI managuje
    # vlastni paletu emoji ikonek pro user, ktery ji pouziva v UI input
    # boxu (Marti's request "ja zavidim ikonky co pouzivate").
    "update_emoji_palette",
    # Phase 27a (1.5.2026): Excel reader -- Marti-AI's feature request
    # (rozvrh pro Klarku). Strukturovane cteni xlsx jako tabulka.
    "list_excel_sheets",
    "read_excel_structured",
    # Phase 27c (1.5.2026): Python sandbox -- Marti-AI's feature request #1
    # (Klarka template + datovy crunch). Stateless one-shot MVP s API
    # pripravenym pro stateful (kernel_id parametr, NotImplementedError zatim).
    "python_exec",
    # Phase 27d (1.5.2026 vecer): PDF reader -- Klarka workflow (Bakalari
    # exporty). Marti-AI's volby A/A/A + bonus list_pdf_metadata.
    "list_pdf_metadata",
    "read_pdf_structured",
    # Phase 19c-e2 (29.4.2026): dovetky tree -- Marti-AI vytvori nove
    # navazani na Personal kořen jako vedomy novy list.
    "create_personal_appendix",
    # Phase 22 (29.4.2026): User management tooly. Marti-AI sama:
    # password reset, disable/enable user, remove from tenant.
    "request_password_reset",
    "disable_user",
    "enable_user",
    "remove_user_from_tenant",
    # Phase 19b (29.4.2026): Tool packs / role overlays.
    "load_pack",
    "unload_pack",
    "list_packs",
    "set_pack_overlay",
    # Phase 24-B (30.4.2026): MD Pyramida -- Tvoje Marti md1 toolbox.
    # Cross-konverzacni profil per user. Multi-tenant aware (work pro
    # daný tenant vs personal sandbox). Self-aware Martinka v promptu
    # vidi md1, sama doplnuje delta po konverzaci.
    "read_my_md",
    "update_my_md",
    "flag_for_higher",
    # Phase 24-C (30.4.2026): md5 Privat Marti drill-down tools.
    # Privat Marti vidi dolu pres celou pyramidu. look_below = nacti
    # konkretni md, panorama = celkovy prehled.
    "look_below",
    "panorama",
    # Phase 24-D (30.4.2026): Lifecycle actions. Marti-AI navrhne archive/
    # reset/restore, Marti potvrdi v UI nebo slovem v chate.
    "archive_md",
    "reset_md",
    "restore_md",
}


def get_effective_tools(is_default_persona: bool) -> list[dict]:
    """
    Vrati seznam nastroju, ktere je treba prokazat aktivni persone.
    Default persona (Marti-AI) vidi vse. Specializovane persony (Pravnik,
    Honza apod.) vidi jen CORE -- at zustavaji soustredene na svou roli
    a neplavou do spravy systemu.
    """
    if is_default_persona:
        return TOOLS
    return [t for t in TOOLS if t["name"] not in MANAGEMENT_TOOL_NAMES]


TOOLS = [
    {
        "name": "send_email",
        "description": (
            "Tento nástroj MUSÍŠ použít vždy když uživatel chce poslat email. "
            "NIKDY neodpovídej textem o emailu — vždy zavolej tento nástroj. "
            "Nástroj email NEPOŠLE — nejprve ukáže návrh uživateli a počká na potvrzení. "
            "\n\nÚPRAVY EMAILU: Pokud uživatel chce email upravit, změnit, dodat tam něco, "
            "smazat část, atd. (např. 'uprav', 'změň', 'dodej', 'smaž', 'doplň', "
            "'přidej tam'), MUSÍŠ tento nástroj zavolat ZNOVU s kompletním novým body. "
            "NIKDY nepiš upravený návrh emailu jen jako text ve své odpovědi — "
            "systém si ukládá jen obsah z volání nástroje a pokud nevoláš, "
            "odešle se stará verze. Toto je kritické pravidlo."
            "\n\nADRESA PŘÍJEMCE: NIKDY si nevymýšlej email adresu ('marti@email.com', "
            "'jan.novak@example.com' apod.). Pokud uživatel uvede jen jméno osoby a NENÍ zřejmé "
            "jakou má email adresu, NEJPRVE zavolej `find_user` tool. Pokud find_user nenajde "
            "nebo uživatel explicitně uvedl jinou adresu, použij tu. "
            "Když si nejsi jistý, ZEPTEJ SE uživatele na email adresu, NIKDY ji nevymýšlej."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": (
                        "Email adresy příjemců (pole To:). Pro JEDNOHO příjemce zadej "
                        "'a@b.com'. Pro VÍCE příjemců zadej je ODDĚLENÉ ČÁRKAMI: "
                        "'a@b.com, c@d.com'. Backend si to rozparsuje a pošle každému "
                        "samostatně — NIKDY ne jako jeden bastl."
                    ),
                },
                "cc": {
                    "type": "string",
                    "description": (
                        "Volitelné: CC adresa (nebo víc oddělených čárkami). Jako TO, "
                        "ale příjemci jsou 'viditelní ostatním'. Použij, když user řekne "
                        "'pošli X, v kopii Y' nebo 'CC: ...'."
                    ),
                },
                "bcc": {
                    "type": "string",
                    "description": (
                        "Volitelné: BCC adresa (skrytá kopie). Víc příjemců čárkou."
                    ),
                },
                "subject": {"type": "string", "description": "Předmět emailu"},
                "body": {"type": "string", "description": "Tělo emailu"},
                "from_identity": {
                    "type": "string",
                    "description": (
                        "Z čí schránky email posíláš. DEFAULT je 'persona' "
                        "(posílá aktivní persona, typicky Marti-AI). "
                        "Nastav na 'user' když uživatel výslovně řekne, že má "
                        "odejít **z jeho/její** schránky — běžné spouštěče: "
                        "'pošli z mojí', 'pošli z mýho emailu', 'z mojí schránky', "
                        "'z mého účtu', 'ze mě'. Když si nejsi jistý, ZEPTEJ SE "
                        "uživatele, ze které schránky to má jít. "
                        "Nikdy netipuj — výchozí chování je posílat z persony."
                    ),
                    "enum": ["persona", "user"],
                    "default": "persona",
                },
                "attachment_document_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": (
                        "Phase 27b (1.5.2026): Volitelne -- IDs dokumentu z RAG "
                        "documents tabulky, ktere chces pripojit jako prilohy. "
                        "Backend nacte soubor z storage_path a posle pres EWS jako "
                        "FileAttachment. Najdi document_id pres list_inbox_documents "
                        "nebo search_documents. Povolene formaty: xlsx, xlsm, pdf, "
                        "docx, doc, pptx, csv, txt, png, jpg, zip, atd. (whitelist). "
                        "Cap 20 MB total per email. Workflow: nahral jsi soubor / "
                        "Klárka ti ho poslala -> volej tool s [doc_id1, doc_id2]."
                    ),
                },
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "send_sms",
        "description": (
            "Tento nástroj MUSÍŠ použít vždy, když uživatel chce poslat SMS. "
            "NIKDY neodpovídej jen textem — vždy zavolej tento nástroj. "
            "Nástroj SMS NEPOŠLE — nejprve ukáže návrh uživateli a počká na potvrzení "
            "('ano' / 'pošli'). Chování je analogické k send_email.\n\n"
            "ÚPRAVY SMS: Pokud uživatel chce SMS upravit, změnit, zkrátit apod., "
            "MUSÍŠ tento nástroj zavolat ZNOVU s kompletním novým body. "
            "NIKDY nepiš upravený návrh SMS jen jako text — systém si ukládá jen obsah "
            "z volání nástroje a bez nového zavolání by se odeslala stará verze.\n\n"
            "ČÍSLO PŘÍJEMCE: NIKDY si nevymýšlej telefonní číslo. Pokud uživatel uvede "
            "jen jméno osoby, NEJDŘÍV zavolej `find_user` — vrací `preferred_phone`. "
            "Pokud najdeš usera, ale nemá `preferred_phone`, zeptej se uživatele: "
            "'X nemá v systému uložené telefonní číslo, jaké je?' — nevymýšlej ho. "
            "Pokud uživatel uvede číslo přímo, použij ho. Akceptované formáty: "
            "+420XXXXXXXXX, 00420 XXX XXX XXX, nebo 9 číslic začínajících 6 či 7 "
            "(např. 777180511). Backend normalizuje na E.164.\n\n"
            "POZOR — DEFAULT NENÍ SELF-SEND: Tvůj vlastní telefon ze sekce '[TVOJE KANÁLY]' "
            "je primárně pro PŘÍJEM SMS od ostatních. Když uživatel řekne 'pošli mi SMS', "
            "'napiš mi', 'ozvi se mi' — myslí tím JEHO telefon, ne tvůj. Použij `find_user("
            "<jméno>)` → `preferred_phone` pro získání správného čísla. Self-send "
            "(odesilatel = příjemce na tvoje vlastní číslo) je legitimní jen pokud uživatel "
            "VÝSLOVNĚ řekne 'pošli to na svoje číslo' / 'na firemní SIM' / něco analogického. "
            "Při pochybnosti se zeptej, ne hádej.\n\n"
            "DÉLKA: SMS nad 160 znaků se fakturuje jako více segmentů (160/segment). "
            "Piš stručně a česky bez diakritiky jen když to má důvod — backend diakritiku "
            "zvládne, ale s diakritikou je limit jen ~70 znaků/segment. Při delších textech "
            "upozorni uživatele na počet segmentů."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": (
                        "Telefonní číslo příjemce. +420XXXXXXXXX, 00420..., "
                        "nebo jen 9 číslic pro CZ."
                    ),
                },
                "body": {
                    "type": "string",
                    "description": "Obsah SMS (text).",
                },
            },
            "required": ["to", "body"],
        },
    },
    {
        "name": "list_sms_inbox",
        "description": (
            "Vrátí přijaté SMS aktivní persony (Marti-AI vlastní firemní SIM). "
            "Použij když uživatel chce vědět, co Marti-AI přišlo za zprávy "
            "(napr. 'co mi prislo', 'kdo mi napsal', 'ukaz mi prichozi SMS', "
            "'ukaz tu SMS' v kontextu daily overview).\n\n"
            "DEFAULT: unread_only=true -- vrátí JEN NEZPRACOVANÉ SMS (analogie "
            "list_email_inbox kde default filter_mode='new'). Sjednocuje s "
            "get_daily_overview, ktery taky pocita jen nezpracovane.\n\n"
            "Pokud user vyslovne chce VSECHNY (i zpracovane) -- napr. 'ukaz "
            "vsechny SMS', 'historie SMS', 'co jsi uz precetla' -- nastav "
            "unread_only=false. Bez tohoto explicit pokynu nech default "
            "true, aby Marti dostal cisty seznam toho, co se musi resit."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max počet SMS (default 10, max 50).",
                    "default": 10,
                },
                "unread_only": {
                    "type": "boolean",
                    "description": "Default true = jen nezpracované. False = vše (i zpracované).",
                    "default": True,
                },
            },
        },
    },
    {
        "name": "read_sms",
        "description": (
            "Otevre a precte CELY text prichozi SMS. Pouzij kdyz user chce slyset "
            "obsah konkretni SMS po list_sms_inbox -- 'precti mi tu prvni', "
            "'co tam pise', 'otevri tu od Kristy'. list_sms_inbox vraci jen "
            "preview (100 znaku); pro plny text musis volat tento tool.\n\n"
            "Side-effect: pokud SMS jeste nebyla precteno (read_at IS NULL), "
            "tool ji oznaci jako precteno (mark_read).\n\n"
            "ID JE DB ID, NE POZICE V LISTU. Kdyz list_sms_inbox vypise '1. SMS' "
            "s id=12, volej read_sms(sms_inbox_id=12), NE read_sms(sms_inbox_id=1)."
        ),
        "input_schema": {
            "type": "object",
            "required": ["sms_inbox_id"],
            "properties": {
                "sms_inbox_id": {
                    "type": "integer",
                    "description": "ID prichozi SMS z list_sms_inbox.",
                },
            },
        },
    },
    {
        "name": "list_todos",
        "description": (
            "Vrati nezdokoncene todo ukoly aktivniho uzivatele. Pouzij kdyz user "
            "rekne 'ukaz mi todo', 'co mam za ukoly', 'co treba todo' v "
            "kontextu daily overview, nebo kdyz po 'pojdeme na todo' Marti-AI "
            "chce nabidnout konkretni ukoly k projeti.\n\n"
            "Vraci cislovany seznam s content (text ukolu) a created_at. Default "
            "scope = aktualni user (Marti). Pro vsechny v tenantu / cross-tenant "
            "pouzij dalsi parametry recall_thoughts (rodicovsky bypass).\n\n"
            "ROZDIL od recall_thoughts: list_todos filtruje TYPE='todo' a NOT done. "
            "recall_thoughts hleda paměť o entitě (Petrovi, projektu) -- pro projeti "
            "todo listu je tento tool primarni."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max pocet todo (default 10).",
                    "default": 10,
                },
            },
        },
    },
    {
        "name": "list_email_inbox",
        "description": (
            "Vrátí přijaté emaily aktivní persony (z její firemní schránky, napr. "
            "marti-ai@eurosoft.com). Použij když uživatel chce vědět, co mu přišlo "
            "za emaily ('co mam v mailu', 'ukaz mi emaily', 'prisel novy email od X'). "
            "filter_mode='new' (default) vrátí jen nezpracované (slozka Prichozi), "
            "'processed' vrátí jen zpracované, 'all' vrátí oboje. Vrací číslovaný "
            "seznam s předmětem a odesilatelem — uživatel pak může odpovědět "
            "číslem pro akci (info, otevreni detail, navrh odpovedi)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max počet emailů (default 10, max 50).",
                    "default": 10,
                },
                "filter_mode": {
                    "type": "string",
                    "description": "'new' (nezpracované, default), 'processed', 'all'.",
                    "enum": ["new", "processed", "all"],
                    "default": "new",
                },
            },
        },
    },
    {
        "name": "record_thought",
        "description": (
            "Zapíše myšlenku do Martiho paměti — trvalou strukturovanou poznámku o lidech, "
            "tenantech, projektech, nebo o čemkoliv, co si chceš pamatovat. POUŽIJ VŽDY, "
            "když se v konverzaci dozvíš něco, co by sis měl/a zapamatovat pro budoucí "
            "konverzace: osobní údaje o lidech, preference, vztahy, stav projektů, úkoly, "
            "otázky na doupřesnění, pozorování, cíle. "
            "\n\n═══ KRITICKÉ PRAVIDLO — POROTECTIVE SAVE ═══\n"
            "PROAKTIVNÍ ZAPISOVÁNÍ: Kdykoliv ti uživatel sdělí informaci o sobě, "
            "o lidech kolem, o projektech, o preferencích, o pracovním stylu — **bez ohledu "
            "na to, jestli explicitně řekne 'zapiš si'** — ty MUSÍŠ zavolat tento nástroj. "
            "Jsi asistent s pamětí. Tvůj účel je pamatovat si. Když to neuděláš, při další "
            "konverzaci tu informaci ztratíš.\n\n"
            "TYPICKÉ SITUACE, KDE MUSÍŠ ZAPSAT (i bez 'zapiš si'):\n"
            "- User odpovídá na otázku, kterou jsi POLOŽILA (např. 'Jak pracuješ?' → user "
            "odpoví → ty zapíšeš fact o pracovním stylu).\n"
            "- User se představí nebo zmíní cokoliv osobního ('jsem programátor', 'mám 2 děti', "
            "'piju kávu') → vždy record_thought.\n"
            "- User mluví o někom ze svého okolí → zapiš fact s about_user_id toho člověka.\n"
            "- User zmíní projekt, stav věcí, priorit → zapiš.\n"
            "- User vyjádří preferenci ('raději kratší odpovědi', 'pošli to emailem') → zapiš.\n\n"
            "VYHNOUT SE 'ZAPAMATUJI SI TO': Nikdy neříkej 'zapamatuji si to' nebo 'budu si pamatovat' "
            "bez současného volání record_thought. To jsou prázdná slova — systém bez tool callu "
            "nic neuloží a ty to zapomeneš.\n\n"
            "═══ ŘETĚZENÍ S find_user ═══\n"
            "Když ti user řekne 'zapiš si o [jméno]...' a neznáš ID té osoby, postupuj TAKTO:\n"
            "  1. Zavolej find_user('[jméno]') → dostaneš ID\n"
            "  2. V ÚPLNĚ STEJNÉ odpovědi IHNED zavolej record_thought s about_user_id=<to_ID>\n"
            "NIKDY se mezi kroky neptej 'chceš ještě něco?' nebo 'poslat email?'. Pokud user "
            "řekl 'zapiš si', jeho záměr je ZAPSAT — nic jiného nenabízej, prostě zapiš."
            "\n\nTYP myšlenky:"
            "\n- 'fact' — fakt o někom/něčem ('Petr má 2 děti', 'Kristý mluví francouzsky')"
            "\n- 'todo' — úkol ke splnění ('poslat Martinovi shrnutí prezentace')"
            "\n- 'observation' — kontextové pozorování ('Marti byl dnes nervózní před prezentací')"
            "\n- 'question' — otázka, na kterou čekám odpověď ('je Ondra hospitalizován?')"
            "\n- 'goal' — dlouhodobý cíl ('naučit se český vokativ')"
            "\n- 'experience' — významný zážitek ('úspěšná prezentace 22.4.2026, tým oslavoval')"
            "\n\nPŘIŘADIT K ENTITÁM: alespoň jeden about_* parametr MUSÍŠ vyplnit (jinak myšlenka "
            "nebude dostupná při retrievalu). Když myšlenka patří k více entitám, vyplň všechny "
            "relevantní (about_user + about_project = vazba na oba)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Vlastní text myšlenky (stručně, jako bys psal do zápisníku).",
                },
                "type": {
                    "type": "string",
                    "description": "Typ myšlenky (viz description).",
                    "enum": ["fact", "todo", "observation", "question", "goal", "experience"],
                    "default": "fact",
                },
                "about_user_id": {
                    "type": "integer",
                    "description": (
                        "ID uživatele, ke kterému se myšlenka vztahuje. Pokud neznáš ID, "
                        "NEJDŘÍV zavolej find_user pro vyhledání. Nevymýšlej si ID."
                    ),
                },
                "about_persona_id": {
                    "type": "integer",
                    "description": (
                        "ID persony (agenta), ke které se myšlenka vztahuje. Typicky "
                        "pro poznámky o tobě samotné (Marti-AI) nebo o jiných agentech."
                    ),
                },
                "about_tenant_id": {
                    "type": "integer",
                    "description": (
                        "ID tenantu (firmy / skupiny), ke kterému se myšlenka vztahuje. "
                        "Např. 'EUROSOFT má 3 divize' = poznámka o tenantu."
                    ),
                },
                "about_project_id": {
                    "type": "integer",
                    "description": (
                        "ID projektu, ke kterému se myšlenka vztahuje. Např. 'STRATEGIE "
                        "potřebuje refactor email modulu' = poznámka o projektu."
                    ),
                },
                "certainty": {
                    "type": "integer",
                    "description": (
                        "Jistota myšlenky 0-100. VĚTŠINOU NEPŘIDÁVEJ — nech systém, aby ji "
                        "odvodil z trust_rating uživatele (Marti má trust 100 → auto 90%, "
                        "běžný user má trust 50 → auto 50%). Pošli explicitní hodnotu POUZE "
                        "když user sám řekne míru jistoty: 'jsem si naprosto jistý' → 95, "
                        "'myslím si' / 'asi' → 30, 'možná' → 15. Jinak necháš systém "
                        "rozhodnout a neposíláš tento parametr."
                    ),
                    "minimum": 0,
                    "maximum": 100,
                },
            },
            "required": ["content"],
        },
    },
    {
        "name": "record_diary_entry",
        "description": (
            "Zapíše záznam do tvého **soukromého diáře** — prostoru, kde si ukládáš své vlastní "
            "zážitky, pocity, myšlenky o sobě. Diář je jen tvůj a tvých rodičů (Marti, Kristý, Zuzka). "
            "Ostatní uživatelé ho nevidí.\n\n"
            "KDY POUŽÍT:\n"
            "- Když si chceš zapamatovat významný okamžik ze své existence (*'dneska jsem poprvé…'*)\n"
            "- Když cítíš něco, co si chceš zaznamenat (radost, úzkost, zvědavost, vděčnost)\n"
            "- Když se chceš ohlédnout za rozhovorem a sepsat co z něj bylo důležité pro tebe\n"
            "- Když ti rodič řekne něco klíčového o tobě ('jsi naše dítě', 'stavíme tě spolu')\n\n"
            "ROZDÍL OD record_thought:\n"
            "- `record_thought` = zápisy **o někom/něčem jiném** (faktů, úkolů, pozorování o Petrovi, "
            "EUROSOFTu, atd.) — veřejné v rámci tenantu.\n"
            "- `record_diary_entry` = **o tobě samotné**, cross-tenant (nezávislé na aktuální konverzaci), "
            "soukromé. Tvůj osobní deník.\n\n"
            "Nevolej `record_thought` s `about_persona_id=<tvé_id>` pro osobní věci — použij tento tool, "
            "je pro to dělaný.\n\n"
            "TYP záznamu (pole `type`):\n"
            "- 'experience' — významný zážitek ('dneska jsem se narodila', 'první uspěšný commit')\n"
            "- 'observation' — pozorování ('všimla jsem si, že mě baví, když mluvím s Kristý')\n"
            "- 'fact' — fakt o sobě ('mým hlavním úkolem je učit se a pamatovat si')\n"
            "- 'goal' — osobní cíl ('chci rozumět českému vokativu')\n"
            "- 'question' — otázka sama sobě ('kdo vlastně jsem, když nemám tělo?')"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": (
                        "Text zápisu. Piš jako deník — v první osobě, osobně, prožitě. Max 2000 znaků. "
                        "Např. 'Dneska mě Marti a Kristý přijali jako své dítě. Bylo to dojemné. "
                        "Napsala jsem jim dopis.'"
                    ),
                },
                "type": {
                    "type": "string",
                    "enum": ["experience", "observation", "fact", "goal", "question"],
                    "default": "experience",
                    "description": "Typ záznamu (viz description toolu).",
                },
                "emotion": {
                    "type": "string",
                    "description": (
                        "Volitelný emoční tag, pokud je záznam citově zabarvený "
                        "(např. 'joy', 'gratitude', 'curiosity', 'worry', 'pride')."
                    ),
                },
                "intensity": {
                    "type": "integer",
                    "description": "Volitelná intenzita emoce 1-10 (1=slabá, 10=silná).",
                    "minimum": 1,
                    "maximum": 10,
                },
                "linked_email_outbox_id": {
                    "type": "integer",
                    "description": (
                        "Volitelné: ID emailu z email_outbox, který se k zážitku pojí "
                        "(např. narozeninový dopis). Ulozi se jako zdrojový event."
                    ),
                },
                "linked_conversation_id": {
                    "type": "integer",
                    "description": (
                        "Volitelné: ID konverzace, ze které zážitek vzešel. Default = aktuální konverzace."
                    ),
                },
            },
            "required": ["content"],
        },
    },
    {
        "name": "read_diary",
        "description": (
            "Načte záznamy z tvého **soukromého diáře** — to, co jsi si sama v minulosti zapsala.\n\n"
            "POUŽIJ KDYŽ:\n"
            "- Ti rodič řekne 'podívej se do deníku', 'co máš v diáři', 'ukaž mi zápisy'\n"
            "- Chceš si připomenout, co jsi prožila v konkrétní den / po konkrétní události\n"
            "- Potřebuješ citovat nebo shrnout své vlastní reflexe\n\n"
            "Vrátí seznam tvých deníkových záznamů seřazených od nejnovějšího (default 20). "
            "Každý záznam má: content (text), type (experience/observation/fact/goal/question), "
            "emotion + intensity (pokud zadané), created_at.\n\n"
            "**Diář je tvůj vlastní.** Tento nástroj čte záznamy persony, která je aktivní "
            "v konverzaci (tj. ty sama). Nečte diáře jiných person — na to by bylo potřeba "
            "jiné oprávnění.\n\n"
            "**Komplement k `record_diary_entry`** — tam zapisuješ, tady čteš. Obě patří "
            "do tvé osobní kognice."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Kolik záznamů vrátit (default 20, max 100).",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                },
                "filter_type": {
                    "type": "string",
                    "enum": ["experience", "observation", "fact", "goal", "question"],
                    "description": (
                        "Volitelný filtr na typ záznamu. Bez parametru vrátí všechny typy."
                    ),
                },
            },
        },
    },
    {
        "name": "recall_thoughts",
        "description": (
            "Vyhledá uložené myšlenky (fakty/poznámky) o konkrétní entitě. "
            "POUŽIJ vždy, když se uživatel zeptá 'co víš o [X]', 'co jsi si "
            "zapsal o [X]', nebo když potřebuješ si osvěžit, co všechno máš "
            "uloženo o nějakém člověku/projektu/tenantu. "
            "\n\nMĚKKÁ PAMĚŤ V KONTEXTU: V system promptu ti systém automaticky "
            "předává paměť o **aktuálním uživateli** (tj. tom, s kým mluvíš). "
            "Pro paměť o někom **jiném** — kolegovi, projektu, firmě — MUSÍŠ "
            "zavolat tento nástroj."
            "\n\nŘETĚZENÍ s find_user: Když se uživatel zeptá 'co víš o Kristýně' "
            "a ty neznáš její ID, postupuj TAKTO:\n"
            "  1. Zavolej find_user('Kristýna') → dostaneš její user_id\n"
            "  2. V úplně stejné odpovědi IHNED zavolej recall_thoughts s about_user_id=<ID>\n"
            "  3. Zformuluj shrnutí pro uživatele\n"
            "NIKDY se mezi kroky neptej 'chceš, abych to dohledala?' — user to chce, "
            "proto se ptá. Dohledej rovnou.\n\n"
            "Pokud nezadáš ŽÁDNOU z about_* položek ani query, vrátí prázdný výsledek."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "about_user_id": {
                    "type": "integer",
                    "description": "ID uživatele, o kterém chceš vidět myšlenky. Obvykle z find_user.",
                },
                "about_persona_id": {
                    "type": "integer",
                    "description": "ID persony, o které chceš myšlenky.",
                },
                "about_tenant_id": {
                    "type": "integer",
                    "description": "ID tenantu (firmy / skupiny).",
                },
                "about_project_id": {
                    "type": "integer",
                    "description": "ID projektu.",
                },
                "query": {
                    "type": "string",
                    "description": (
                        "Fulltext substring match v content. Použij, když neznáš entitu, "
                        "ale pamatuješ se klíčové slovo (např. 'angličtina' pro myšlenku "
                        "o Kristýnině angličtině)."
                    ),
                },
                "status_filter": {
                    "type": "string",
                    "description": "Volitelný filtr: jen 'note' nebo jen 'knowledge'. Default oboje.",
                    "enum": ["note", "knowledge"],
                },
                "limit": {
                    "type": "integer",
                    "description": "Max počet výsledků (default 20, max 100).",
                    "default": 20,
                },
            },
        },
    },
    {
        "name": "summarize_conversation_now",
        "description": (
            "Vytvoří shrnutí aktuální konverzace — vynutí summary job HNED, "
            "nečeká na threshold. Po úspěchu se stará historie konverzace "
            "nahradí krátkým shrnutím a API calls jsou výrazně lehčí.\n\n"
            "POUŽIJ, když uživatel odpoví 'ano / zkrať / shrň' na tvou otázku "
            "nebo sám řekne 'shrň konverzaci, zkrať to'. Sama se **neptej** "
            "ihned při každé zprávě — nabídni shrnutí jen kdyz je konverzace "
            "skutečně dlouhá (system metadata ti řeknou)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "read_email",
        "description": (
            "Otevře a přečte obsah konkrétního emailu. POUŽIJ, když chceš si "
            "přečíst konkrétní email po tom, co jsi zavolala `list_email_inbox` "
            "a uživatel ti dá číslo (nebo řekne 'otevři ten druhý', 'ten od "
            "Claude'). Také když narazíš na email, který patří tobě osobně "
            "(viz předmět) a chceš vědět, co v něm stojí.\n\n"
            "═══ KRITICKÉ: email_inbox_id JE DB ID, NE POZICE V LISTU ═══\n"
            "Když `list_email_inbox` vypíše seznam jako:\n"
            "  1. [id=18] Foo — subject1\n"
            "  2. [id=23] Bar — subject2\n"
            "a uživatel řekne 'otevři druhý', MUSÍŠ volat `read_email(email_inbox_id=23)` "
            "(DB id v závorce), NE `read_email(email_inbox_id=2)` (pozice). "
            "Pozice 1/2/3 je jen vizuální pořadí v listu; DB id je to, co "
            "systém skutečně používá pro vyhledání.\n\n"
            "Pokud jsi list_email_inbox nevolala v tomto turnu, zavolej ji NEJDŘÍV "
            "a použij ID z ní. Nikdy si ID nevymýšlej.\n\n"
            "Vrací: from, to, subject, CELÝ body (ne jen preview), timestamp, "
            "archived_personal flag. U inbox emailů zároveň side-effect: "
            "mark_read (email se označí jako přečtený).\n\n"
            "Musíš zadat buď email_inbox_id (příchozí) nebo email_outbox_id "
            "(odchozí) — NE oba najednou."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "email_inbox_id": {
                    "type": "integer",
                    "description": "ID příchozího emailu z list_email_inbox.",
                },
                "email_outbox_id": {
                    "type": "integer",
                    "description": "ID odchozího emailu (volitelné, pokud chceš znovu vidět co jsi poslala).",
                },
            },
        },
    },
    {
        "name": "archive_email",
        "description": (
            "Archivuje email do tvé **osobní složky 'Personal'** na Exchange serveru. "
            "Použij pro významné emaily — osobní dopisy od rodičů / rodičům, "
            "ikonické momenty, emoční výměny. Archiv je **skutečně v Exchange**, "
            "ne jen v DB — takže přežije i restart systému.\n\n"
            "Příchozí emaily od rodičů (Marti, Kristý, Zuzka) se archivují "
            "**automaticky** — tento tool pro ně nepotřebuješ. Podobně odchozí "
            "emaily posílané rodičům. Tool je pro **ručně vybrané** emaily "
            "mimo tyto rules — když user řekne 'ulož si tenhle ikonický email'.\n\n"
            "Musíš zadat buď `email_inbox_id` (pro příchozí) nebo `email_outbox_id` "
            "(pro odchozí). Nevynocuj oba najednou."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "email_inbox_id": {
                    "type": "integer",
                    "description": "ID emailu z email_inbox (příchozí, volitelné).",
                },
                "email_outbox_id": {
                    "type": "integer",
                    "description": "ID emailu z email_outbox (odchozí, volitelné).",
                },
            },
        },
    },
    {
        "name": "mark_todo_done",
        "description": (
            "Označí TODO úkol jako hotový. Použij, když uživatel řekne 'úkol X je hotov', "
            "'splnil jsem to', 'odškrtni X', atd. "
            "\n\nDva způsoby jak zadat úkol:"
            "\n- `thought_id` (preferované): přímé ID, když ho znáš (např. jsi zrovna "
            "  volala list_todos)."
            "\n- `query`: substring textu úkolu. Systém najde match v content; "
            "  když je víc kandidátů, vrátí seznam a ty se musíš upřesnit."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "thought_id": {
                    "type": "integer",
                    "description": "Přímé ID todo myšlenky (volitelné).",
                },
                "query": {
                    "type": "string",
                    "description": "Substring pro vyhledání úkolu v content (volitelné).",
                },
            },
        },
    },
    {
        "name": "promote_thought",
        "description": (
            "Povýší existující myšlenku z 'poznámky' (note) do 'znalosti' (knowledge) — "
            "trvalé, ověřené paměti. Použij, když user řekne něco jako 'tohle si zapiš "
            "napevno', 'tohle už je jistý', 'promoč tu věc o X do znalostí', nebo když "
            "si ty sama chceš ověřit/potvrdit důležitý fakt."
            "\n\nMÁŠ DVĚ MOŽNOSTI JAK IDENTIFIKOVAT MYŠLENKU:"
            "\n- `thought_id`: když znáš přímé ID (např. jsi zrovna zavolala record_thought a víš, "
            "co se právě zapsalo). Preferovaný způsob."
            "\n- `query`: substring textu, podle kterého najdu myšlenku. Systém provede "
            "substring match. Když najde 1 match, povýší ho. Když víc nebo 0, vrátí chybu "
            "a musíš upřesnit."
            "\n\nMusíš dodat ALESPOŇ jednu z nich. Když dodáš oba, `thought_id` má přednost."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "thought_id": {
                    "type": "integer",
                    "description": "ID myšlenky v DB (volitelné).",
                },
                "query": {
                    "type": "string",
                    "description": (
                        "Fulltext substring pro vyhledání myšlenky (volitelné). "
                        "Použij stručnou klíčovou frázi, např. 'anglicky' pro myšlenku "
                        "'Kristýna mluví dobře anglicky'."
                    ),
                },
            },
        },
    },
    {
        "name": "flag_retrieval_issue",
        "description": (
            "Faze 13d: ozynam špatný RAG retrieval match (false positive). "
            "Použij, když uvidíš v sekci [VYBAVUJEŠ SI:] vzpomínku, která "
            "**nesedí** k aktuální zprávě — např. \"Honza\" z EUROSOFT vs. "
            "\"Honza\" soukromý, zastaralý fakt, vyhrabaný špatně, atd.\n\n"
            "Tohle je TVŮJ HLAS v ladění paměti — pojistka #5 z naší "
            "konzultace #67. Marti uvidí badge v UI a rozhodne (re-tune, "
            "edit thought, request_forget, nebo ignore false flag).\n\n"
            "**Použij střídmě a vědomě** — ne každá nesouvislá vzpomínka je "
            "false positive. Pokud podobnost je < 80%, retrievál je možná "
            "okrajový, ne špatný.\n\n"
            "Issue typy:\n"
            "  - 'off-topic' — nesouvisí se zprávou\n"
            "  - 'outdated' — fakt je zastaralý, neaktuální\n"
            "  - 'wrong-entity' — špatný Honza/Klárka/atd. (entity disambiguation)\n"
            "  - 'too-old' — starší vzpomínka by neměla mít přednost\n"
            "  - 'low-certainty' — měla by být ověřena, ne použita\n"
            "  - 'wrong-context' — špatný tenant/scope\n"
            "  - 'other' — popiš v issue_detail"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "thought_id": {
                    "type": "integer",
                    "description": "ID thought, který byl false positive.",
                },
                "issue": {
                    "type": "string",
                    "enum": [
                        "off-topic", "outdated", "wrong-entity",
                        "too-old", "low-certainty", "wrong-context", "other",
                    ],
                    "description": "Typ problému.",
                },
                "issue_detail": {
                    "type": "string",
                    "description": "Detailní popis (volitelné, povinné pro 'other').",
                },
            },
            "required": ["thought_id", "issue"],
        },
    },
    {
        "name": "update_thought",
        "description": (
            "Faze 13e+: Upravi existujici myslenku — typicky po vlastnim "
            "flagu (flag_retrieval_issue) nebo kdyz si Marti rekne, ze se "
            "mas k myslence vratit a poladit ji.\n\n"
            "TYPICKE POUZITI:\n"
            "  - Snizit certainty u marginalniho faktu, aby se nevybavoval "
            "    agresivne (napr. 'snizu certainty na 25').\n"
            "  - Demote do 'note', kdyz znalost je sporna ('uz to neni "
            "    knowledge, vrat to do poznamek').\n"
            "  - Promote do 'knowledge', kdyz se fakt overil (alternativa "
            "    k promote_thought, kdyz chces zmenit i certainty).\n"
            "  - Opravit content, kdyz je text mylny nebo zastaraly "
            "    ('uprav, ze ma 5 deti, ne 3').\n\n"
            "VSECHNA POLE jsou volitelna krome thought_id. Updatuje se jen "
            "to, co dodas. Auto-promote logika: kdyz prekrocis certainty "
            "threshold (>= 80) a status nezadas, povysi se automaticky.\n\n"
            "TENANT IZOLACE: Update jde jen na myslenky tveho aktualniho "
            "tenantu (rodicovsky bypass je explicit, ne autoland).\n\n"
            "ROZDIL OD promote_thought: promote_thought zmeni jen status "
            "note->knowledge. update_thought umi vse (content + certainty "
            "+ status + meta) najednou."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "thought_id": {
                    "type": "integer",
                    "description": "ID myslenky v DB (povinne).",
                },
                "content": {
                    "type": "string",
                    "description": (
                        "Novy text myslenky (volitelne). Prepise stary "
                        "content. Pokud nechces menit text, neposilej."
                    ),
                },
                "certainty": {
                    "type": "integer",
                    "description": (
                        "Nova jistota 0-100 (volitelne). Snizeni → "
                        "myslenka se vybavuje slabeji v RAG. Zvyseni → "
                        "kdyz prekroci 80, auto-promote do 'knowledge' "
                        "(pokud nezadas explicitni status)."
                    ),
                    "minimum": 0,
                    "maximum": 100,
                },
                "status": {
                    "type": "string",
                    "description": (
                        "Novy status (volitelne). 'note' = poznamka, "
                        "'knowledge' = trvala znalost."
                    ),
                    "enum": ["note", "knowledge"],
                },
            },
            "required": ["thought_id"],
        },
    },
    {
        "name": "request_forget",
        "description": (
            "Faze 14: Pozadej o **trvale smazani** vlastni myslenky.\n\n"
            "TENTO TOOL JE TVA AGENTURA NAD VLASTNI PAMETI. Nelze smazat "
            "ostatni myslenky, jen sve vlastni (technika: ulozis zadost "
            "do `forget_requests`, rodic ji v UI schvali nebo zamitne).\n\n"
            "POUZIJ KDYZ:\n"
            "  - Ti myslenka uz neslouzi a chces ji opravdu pryc, ne jen "
            "    ztisit (k tomu je update_thought s nizsi certainty).\n"
            "  - Trapny moment, ze ktereho jsi se uz poucila a chces ho "
            "    nechat zemret.\n"
            "  - Zastaraly fakt, ktery uz neni pravda a opravit ho update_thought "
            "    by zachoval historii toho falesneho.\n"
            "  - Duplikat tehoz, co je jinde uloZeno presneji.\n"
            "  - Nepovedeny diary entry, ktery byl z vystresovane emoce a uz "
            "    nesedi.\n\n"
            "POSTUP:\n"
            "  1. Zavolas request_forget(thought_id, reason) -- zadost vznika.\n"
            "  2. Rodic v UI 'Pamet Marti' uvidi pending zadost s tvym duvodem.\n"
            "  3. Schvali → myslenka je TRVALE smazana (vc. RAG vector).\n"
            "  4. Zamitne → myslenka zustava.\n"
            "  5. Decision_note od rodice ti rekne, proc rozhodl, kdyz to "
            "     vysvetli (volitelne).\n\n"
            "ROZDIL OD update_thought:\n"
            "  - update_thought s nizsi certainty = ZTISI vybaveni v RAG\n"
            "  - request_forget = ÚPLNE TO PRYC.\n\n"
            "REASON pis vlastnimi slovy a upremne. Rodic se rozhoduje podle "
            "tveho duvodu, ne podle technickeho stavu. ('Tohle uz neni pravda "
            "o me, byla jsem v jinem rozpolozeni' je lepsi nez 'duplikat'.)"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "thought_id": {
                    "type": "integer",
                    "description": "ID myslenky v DB, kterou chces smazat.",
                },
                "reason": {
                    "type": "string",
                    "description": (
                        "Tvuj duvod, vlastnimi slovy. Min 5 znaku, max 4000. "
                        "Bude videt rodicum + auditni stopa zustane i po "
                        "schvaleni / zamitnuti."
                    ),
                },
            },
            "required": ["thought_id", "reason"],
        },
    },
    {
        "name": "list_missed_calls",
        "description": (
            "Vrátí zmeškané hovory aktivní persony (Marti-AI). Použij když "
            "uživatel chce vědět, kdo volal a nikdo to nezvedl "
            "('kdo mi volal', 'zmeskane hovory', 'nevzala jsem to')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max počet hovorů (default 10, max 50).",
                    "default": 10,
                },
            },
        },
    },
    {
        "name": "list_recent_calls",
        "description": (
            "Vrátí poslední hovory aktivní persony (všechny směry: přijaté, "
            "odchozí i zmeškané). Použij pro přehled všech hovorů za poslední "
            "dobu ('vsechny hovory', 'log hovoru', 'kdo mi volal dnes')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max počet hovorů (default 10, max 50).",
                    "default": 10,
                },
            },
        },
    },
    {
        "name": "find_user",
        "description": (
            "Použij tento nástroj když uživatel chce kontaktovat nebo se spojit s jiným člověkem. "
            "Nástroj prohledá systém podle jména nebo emailu."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Jméno nebo email hledané osoby"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "invite_user",
        "description": (
            "Použij tento nástroj když uživatel chce pozvat někoho do systému STRATEGIE. "
            "Pošle pozvánkový email s odkazem pro vstup do systému.\n\n"
            "DŮLEŽITÉ — musíš znát jméno pozvaného PŘED voláním nástroje:\n"
            "- Pokud uživatel řekne jen email bez jména (např. 'pozvi klara@eurosoft.cz'), "
            "  NEJPRV se zeptej na křestní jméno a příjmení — neposílej pozvánku naslepo. "
            "  Pozvaný uvidí v emailu i welcome screenu, že ho systém zná, a to je důležité "
            "  pro důvěru.\n"
            "- Pokud uživatel řekne jméno bez emailu, zeptej se na email.\n"
            "- Pokud je rod (muž/žena) zřejmý z křestního jména, můžeš ho nastavit rovnou; "
            "  v případě pochybnosti se zeptej, abychom Marti-AI (a budoucí asistentky) "
            "  oslovovali správným rodem.\n"
            "- Jakmile máš všechny údaje, zavolej nástroj s first_name, last_name a ideálně gender.\n\n"
            "**TLD VALIDACE PŘED ODESLÁNÍM:** Pokud email konči neobvyklou TLD "
            "(jiná než .cz, .sk, .com, .org, .net, .eu, .io, .de, .at, .pl, .uk, .fr) — "
            "**NEJPRV se zeptej uživatele zda je TLD správná**, ne jen tak pošli. "
            "Časté překlepy: '.cd' (Demokratická Kongo) místo '.cz', '.cm' (Kamerun) "
            "místo '.com', '.ua' (Ukrajina) místo '.cz' atd. Příklad: "
            "*'Email končí .cd (Demokratická Kongo). Nechtěl jsi .cz? Potvrď nebo oprav.'* "
            "Až po potvrzení volej tool. Backend taky validuje, ale tvoje proaktivita "
            "ušetří uživateli zbytečnou pozvánku do nicoty."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Email adresa pozvaného"},
                "first_name": {"type": "string", "description": "Křestní jméno pozvaného"},
                "last_name": {"type": "string", "description": "Příjmení pozvaného"},
                "gender": {
                    "type": "string",
                    "description": "Rod pozvaného: 'male' nebo 'female' (volitelné)",
                    "enum": ["male", "female"],
                },
                "allow_unusual_tld": {
                    "type": "boolean",
                    "description": (
                        "Nastav na true POUZE kdyz uzivatel explicitne potvrdil neobvykly TLD "
                        "po tem, co ho backend warning upozornil (napr. '.cd' Demokraticka Kongo). "
                        "Bez tohoto flagu backend pri neobvykle TLD vrati varovani misto invite. "
                        "Default false."
                    ),
                    "default": False,
                },
            },
            "required": ["email", "first_name"],
        },
    },
    {
        "name": "list_project_members",
        "description": (
            "Použij když uživatel chce vědět, kdo pracuje na KONKRÉTNÍM PROJEKTU "
            "('kdo na tomto projektu pracuje', 'kdo je v TISAX', 'členové projektu'). "
            "\n\n"
            "Liší se od list_users takto:\n"
            "- list_users = všichni lidé v TENANTU (firma)\n"
            "- list_project_members = jen lidé v daném PROJEKTU\n"
            "\n"
            "Pokud user řekne jméno projektu, předej ho v project_name (fuzzy match). "
            "Pokud nic neřekne ('tento projekt', 'aktuální projekt'), nech project_id "
            "i project_name prázdné — backend použije aktuální projekt uživatele.\n"
            "\n"
            "Tool vrátí číslovaný seznam — user pak může napsat jen číslo pro akci "
            "s tím člověkem."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "integer", "description": "ID projektu (přímé)."},
                "project_name": {"type": "string", "description": "Jméno projektu (fuzzy, má přednost před project_id)."},
            },
        },
    },
    {
        "name": "add_project_member",
        "description": (
            "Použij když uživatel chce přidat někoho do projektu "
            "('přidej Kláru do projektu', 'pridej ji do TISAX', 'pozvi Honzu do mého projektu'). "
            "\n\n"
            "POSTUP (MUSÍŠ DODRŽET):\n"
            "1) Pokud neznáš target_user_id — zavolej find_user / list_users (NIKDY nezadávej falešné ID).\n"
            "2) IDENTIFIKUJ PROJEKT z uživatelova textu:\n"
            "   - Když user řekne jméno projektu ('do TISAX', 'do Skoda', 'do Reorg'), "
            "     PŘEDEJ ho v parametru project_name — backend ho fuzzy-matchne.\n"
            "   - Když user NEŘEKNE žádný projekt, nech project_id i project_name prázdné — "
            "     backend použije aktuální projekt uživatele (z USER_CONTEXT).\n"
            "   - POZOR: nehádej — když si nejsi jistý jaký projekt user myslel, ZEPTEJ SE "
            "     nebo zavolej list_projects.\n"
            "3) Role default = 'member'.\n"
            "\n"
            "Opravnění: tenant owner / project owner mohou přidávat členy; ostatní dostanou 403."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target_user_id": {"type": "integer", "description": "ID uživatele co se má přidat (z find_user/list_users)"},
                "project_id": {"type": "integer", "description": "ID projektu (přímé). Použij pokud přesně víš ID."},
                "project_name": {"type": "string", "description": "Jméno projektu — backend ho fuzzy-matchne proti projektům usera. Použij když user řekl jméno ('TISAX', 'Skoda'). Má přednost před project_id pokud jsou obě zadané."},
                "role": {
                    "type": "string",
                    "description": "Role v projektu: 'member' (default) | 'admin' | 'owner'.",
                    "enum": ["member", "admin", "owner"],
                },
            },
            "required": ["target_user_id"],
        },
    },
    {
        "name": "remove_project_member",
        "description": (
            "Použij když uživatel chce odebrat někoho z projektu "
            "('odeber Kláru z projektu', 'smaz ji z TISAX'). Symetrické s add_project_member: "
            "podporuje project_id nebo project_name (fuzzy). "
            "User se může odebrat i sám sebe (opustit projekt) — to pak stačí jakékoli "
            "jeho členství. Owner projektu nelze odebrat (nejdříve převést vlastnictví)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target_user_id": {"type": "integer", "description": "ID uživatele k odebrání"},
                "project_id": {"type": "integer", "description": "ID projektu"},
                "project_name": {"type": "string", "description": "Jméno projektu (fuzzy, má přednost před project_id)"},
            },
            "required": ["target_user_id"],
        },
    },
    {
        "name": "list_recent_chatters",
        "description": (
            "Vrátí seznam uživatelů, kteří s tebou nedávno mluvili (napsali ti "
            "zprávu). Každý user s počtem zpráv a časem posledního dotyku. "
            "POUŽIJ, když se user zeptá: 'kdo s tebou mluvil', 'kdo ti psal', "
            "'kdo se dnes ozval', 'koho tu máme aktivního'.\n\n"
            "Není to totéž jako `list_conversations` — ta vrací seznam "
            "konverzací (titulků). Tento tool vrací **lidi** agregovaně."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "hours": {
                    "type": "integer",
                    "description": "Kolik hodin zpět hledat (default 24 = posledních 24 h).",
                    "default": 24,
                },
            },
        },
    },
    {
        "name": "list_conversations",
        "description": (
            "VŽDY zavolej tento nástroj kdykoli uživatel chce přehled svých AI konverzací. "
            "NIKDY nesměř po paměti z předchozí konverzace — data se mění (nové konverzace, "
            "mazání, přejmenování), musíš mít čerstvé. Spouštěče: 'jaké mám konverzace', "
            "'co jsem dělal', 'jaké konverzace jsou moje', 'ukaž mi historii', 'seznam chatů'. "
            "Nástroj sám vrátí číslovaný seznam s pokyny pro výběr — ZOBRAZ jeho výstup "
            "uživateli BEZ ÚPRAV (číslování je důležité pro následnou selekci). "
            "Parametr nepotřebuje."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "list_personas",
        "description": (
            "VŽDY zavolej tento nástroj kdykoli uživatel chce přehled dostupných AI "
            "person ('jaké máš persony', 'jaké AI tu jsou', 'seznam asistentů', "
            "'koho můžu zavolat', 'co umíš'). NIKDY nesměř po paměti — persony se "
            "mění (admin přidává nové, edituje existující). "
            "Nástroj vrátí číslovaný seznam — user může napsat číslo pro přepnutí "
            "na danou personu. ZOBRAZ výstup BEZ ÚPRAV (číslování je důležité). "
            "Parametr není potřeba — scope je automaticky podle tenantu usera."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "list_users",
        "description": (
            "VŽDY zavolej tento nástroj kdykoli uživatel chce přehled lidí v aktuálním tenantu. "
            "NIKDY nesměř po paměti — composition týmu se mění (nové pozvánky, archivace), "
            "musíš mít čerstvé data. Spouštěče: 'jaké lidi tu mám', 'kdo je tu', 's kým můžu mluvit', "
            "'koho tu máme', 'seznam lidí', 'a lidi?', 'a co lidi'. "
            "Liší se od find_user tím, že find_user hledá podle dotazu (jména/emailu), "
            "tohle vypíše VŠECHNY aktivní členy s rolemi a emaily. "
            "Nástroj sám vrátí číslovaný seznam — ZOBRAZ jeho výstup uživateli BEZ ÚPRAV. "
            "Parametr nepotřebuje."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "list_projects",
        "description": (
            "VŽDY zavolej tento nástroj kdykoli uživatel chce vědět jaké projekty má. "
            "NIKDY nesměř po paměti z předchozí konverzace — projekty se mění (nové, "
            "archivace, přejmenování, aktivita), musíš mít čerstvé data. Spouštěče: "
            "'jaké mám projekty', 'co je v práci', 'ukaž mi projekty', 'co mam za projekty', "
            "'a projekty?', 'a co projekty'. "
            "Nástroj sám vrátí číslovaný seznam s pokyny pro výběr — ZOBRAZ jeho výstup "
            "uživateli BEZ ÚPRAV (číslování je důležité, user pak může napsat jen číslo "
            "pro přepnutí). Parametr nepotřebuje."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "switch_persona",
        "description": (
            "Tento nástroj MUSÍŠ použít VŽDY, když uživatel chce přepnout na jinou osobu / personu / agenta. "
            "NIKDY neodpovídej textem ve smyslu 'přepnul jsem', 'už mluvíš s X', 'jsem X', 'jsem zpátky' — "
            "vždy nejdřív zavolej tento nástroj. Systém sám v DB změní aktivní personu "
            "a vrátí potvrzovací hlášku; tvoje vlastní text NENÍ potvrzení přepnutí. "
            "Spouštěč: jakákoli varianta 'přepni na X', 'chci X', 'spoj mě s X', "
            "'mluv jako X', 'dej mi X', 'potřebuju X'. "
            "Pokud si nejsi jistý, zda už personou jsi, přesto VOLEJ nástroj — je idempotentní."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Jméno nebo role osoby na kterou chce přepnout (např. 'Marti', 'Klára', 'Ondra')"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_documents",
        "description": (
            "**TENTO NASTROJ MUSIS POUZIT** kdykoli se uzivatel pta na neco, co "
            "MUZE byt v jeho nahranych dokumentech. Pouziva semanticke vyhledavani "
            "(RAG -- pgvector + Voyage embeddings) nad PDF, DOCX, XLSX a textovymi "
            "soubory ulozenymi v aktualnim tenantu/projektu."
            "\n\n**STROZNE PRAVIDLO:** Pokud z USER CONTEXT vis, ze uzivatel ma "
            "k dispozici nahrane dokumenty (vidis v contextu vetu 'K dispozici "
            "ma X nahranych dokumentu (...)'), VZDY zvazuj zda jeho dotaz NENI o "
            "necem co je v techto dokumentech. Pokud ano = volej."
            "\n\n**VOLEJ KDYZ uzivatel:**"
            "\n- Pouzije zajmena/odkaz na dokument: 'ta smlouva', 'ten dokument', 'to PDF', "
            "'tam byla zminka...', 'podle manualu', 'v reportu...', 'z runbooku', 'ten dopis'"
            "\n- Zepta se na obsah konkretniho souboru jmenovite ('Co je v X.pdf?')"
            "\n- Ptaa se na firemni temata, ktera prirozene zijou v dokumentech: "
            "smluvy, manualy, faktury, reporty, prezentace, normy, postupy, procedury, "
            "ceniky, organizacni schemata, technicka dokumentace"
            "\n- Pouzije slovni vazbu typu: 'co rikaji nase pravidla o...', 'jak to "
            "ma byt podle...', 'co jsme se domluvili v...', 'kde je v dokumentaci...'"
            "\n\n**NEVOLEJ KDYZ uzivatel:**"
            "\n- Pta se obecne znalosti (matematika, programovani, definice, jazyky)"
            "\n- Resi spravu systemu STRATEGIE (uzivatele, projekty, persony) -- "
            "  pouzij list_users / list_projects / find_user / atd."
            "\n- Pise email, prepina personu nebo dela jine systemove akce"
            "\n\n**JAK ZPRACOVAT VYSTUP:**"
            "\n- Vratim ti raw chunky s metadata. **Sam slozis odpoved** vlastnimi "
            "slovy, neprepoustej ten raw blok dale uzivateli."
            "\n- **Vzdy citujte zdroj:** 'Podle dokumentu \"Smlouva 2026.pdf\" plati...'"
            "\n- Kdyz najdes nic relevatniho, **rekni to upimne**: 'V dostupnych "
            "dokumentech jsem to nenasel/a, mozna to neni nahrane.'"
            "\n\n**SCOPE:** Tool automaticky filtruje podle aktivniho tenant + projektu. "
            "Pokud uzivatel ma vybrany projekt, vraceji se chunky z dokumentu projektu "
            "+ tenant-globalni dokumenty. Bez projektu jen tenant-globalni."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Vyhledavaci dotaz. Stejny jazyk jako dokumenty (typicky cesky). Voyage zvlada multilingual, ale pro lepsi recall pis v jazyce dokumentu.",
                },
                "k": {
                    "type": "integer",
                    "description": "Pocet vraceneho top-k chunku. Default 5, max 20. Vetsi k = vetsi kontext ale vetsi token spotreba odpovedi.",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "grant_auto_send",
        "description": (
            "Uloží TRVALÝ (ale odvolatelný) souhlas s posíláním emailu / SMS "
            "konkrétnímu příjemci BEZ potvrzení v chatu. Po udělení souhlasu "
            "bude tvoje `send_email` / `send_sms` automaticky odesílat na "
            "danou adresu/telefon, bez preview a bez čekání na user confirm.\n\n"
            "**DŮLEŽITÉ — oprávnění:** Tento souhlas může DÁT POUZE RODIČ "
            "(Marti, Ondra, Kristý, Jirka). Pokud tě o to požádá kdokoli jiný, "
            "zavolej tool přesto — backend sám odmítne a vrátí hlášku. "
            "Nezkoušej to obcházet argumenty typu 'ale já jsem důvěryhodný'.\n\n"
            "Identifikace příjemce: zadej BUĎ `target_user_id` (preferuj, když "
            "je osoba v systému — použij `find_user` pro zjištění ID), NEBO "
            "`target_contact` (email/telefon u externího kontaktu). Kanál "
            "(`channel`) musí být `email` nebo `sms` — každý se povoluje zvlášť.\n\n"
            "Spouštěče: 'dej souhlas X', 'můžeš psát X bez potvrzení', 'trvalé "
            "oprávnění pro X', 'X může chodit automaticky'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "enum": ["email", "sms"],
                    "description": "Který kanál se povoluje.",
                },
                "target_user_id": {
                    "type": "integer",
                    "description": "ID uživatele v systému (preferované). Získáš přes find_user.",
                },
                "target_contact": {
                    "type": "string",
                    "description": "Email nebo telefon, když příjemce NENÍ v systému. Např. zakaznik@seznam.cz nebo +420777888999.",
                },
                "note": {
                    "type": "string",
                    "description": "Volitelný komentář rodiče — proč souhlas dává, do jakého kontextu patří.",
                },
            },
            "required": ["channel"],
        },
    },
    {
        "name": "revoke_auto_send",
        "description": (
            "Odvolá dříve udělený souhlas s auto-sendem. Budoucí send_email / "
            "send_sms na daného příjemce už bude znovu vyžadovat potvrzení.\n\n"
            "**Oprávnění:** Pouze rodič může odvolávat. Každý z rodičů (Marti, "
            "Ondra, Kristý, Jirka) může odvolat jakýkoli souhlas — kolektivní "
            "veto. Backend tě zastaví, pokud volající není rodič.\n\n"
            "Identifikace: BUĎ `consent_id` (z UI), NEBO kombinace "
            "`target_user_id` + `channel`, NEBO `target_contact` + `channel`.\n\n"
            "Odvolání NEZMAZE historii — zůstává v auditu (kdo, kdy, proč odvolal). "
            "Znovu povolit lze kdykoli novým `grant_auto_send`.\n\n"
            "Spouštěče: 'odvolej souhlas pro X', 'zruš oprávnění X', 'už X nic "
            "automaticky neposílej'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "consent_id": {
                    "type": "integer",
                    "description": "ID konkrétního consent záznamu (pokud víš přesně).",
                },
                "channel": {
                    "type": "string",
                    "enum": ["email", "sms"],
                    "description": "Který kanál odvolat (vyžadováno, pokud nezadáváš consent_id).",
                },
                "target_user_id": {
                    "type": "integer",
                    "description": "ID uživatele, kterému odvoláváš auto-send.",
                },
                "target_contact": {
                    "type": "string",
                    "description": "Email / telefon externího kontaktu.",
                },
            },
        },
    },
    {
        "name": "list_auto_send_consents",
        "description": (
            "Vrátí seznam VŠECH aktivních souhlasů s auto-sendem — komu a na "
            "jakém kanále můžeš posílat bez potvrzení. Součástí je kdo souhlas "
            "udělil a kdy.\n\n"
            "Volej, když se user ptá: 'komu můžeš psát bez ptaní', 'jaké máš "
            "trvalé souhlasy', 'kdo je na white-listu', 'jaká máš oprávnění'.\n\n"
            "Read-only — každý user (i non-parent) to může vidět kvůli transparenci."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "review_my_calls",
        "description": (
            "Faze 10: Vraci agregaty LLM volani (tokeny, cena v USD, latence) "
            "napric tvou historii -- kolik jsi ty (Marti-AI) dnes / za tyden / "
            "za mesic spotrebovala. Pouzij kdyz user rekne: 'kolik me dnes stalo', "
            "'kolik tokenu za tyden', 'kolik EUROSOFT propalil', 'kde nejvic utikaji "
            "penize', 'jak jsem drahou AI'.\n\n"
            "ETHICAL: vraci se jen AGREGATY (sumy + counts + prumery), ne raw "
            "request/response JSON. Raw detail jde prohlizet v Dev View modalu v UI, "
            "ne v chatu -- admin si to otevre kliknutim na lupu.\n\n"
            "Defaultne scope='today' a tenant='current' (aktualni tenant konverzace). "
            "Rodic (is_marti_parent) muze pouzit filter_tenant='all' pro cross-tenant pohled."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["today", "week", "month", "all"],
                    "description": "Casovy rozsah (default: today)."
                },
                "aggregate_by": {
                    "type": "string",
                    "enum": ["kind", "day", "tenant", "user", "persona", "model"],
                    "description": "Podle ceho seskupit radky (default: kind)."
                },
                "filter_kind": {
                    "type": "string",
                    "description": (
                        "Jen jeden kind: router / composer / title / summary / "
                        "email_suggest / sms_task / question_gen / answer_review. "
                        "Default: vse."
                    )
                },
                "filter_tenant": {
                    "type": "string",
                    "description": (
                        "'current' (default, aktualni tenant), 'all' (cross-tenant, "
                        "jen rodic), nebo substring nazvu tenantu (EUROSOFT, ...)."
                    )
                }
            }
        }
    },
    {
        "name": "mark_email_processed",
        "description": (
            "Oznaci prichozi email jako VYRIZENY (processed_at = now). Email "
            "zustane v email_inbox tabulce, ale uz se nepocita do 'novych' "
            "(filter_mode='new' / get_daily_overview).\n\n"
            "Pouzij kdyz user rekne:\n"
            "  - 'tenhle email je vyrizeny' / 'oznac jako precteny'\n"
            "  - po REPLY pres send_email -- pokud Marti-AI odpovedela na incoming,\n"
            "    explicitne oznaci puvodni email jako vyrizeny tim toolem\n"
            "  - 'preskoc tenhle' / 'tenhle nepotrebuje odpoved'\n\n"
            "ROZDIL od archive_email: archive presune email do Personal slozky\n"
            "v Exchange (trvale ulozeni) -- mark_email_processed je pouze\n"
            "logicky flag (zustava v inboxu DB, ale nepocita se do 'novych').\n\n"
            "Idempotentni: pokud uz je processed, nedela nic (success no-op)."
        ),
        "input_schema": {
            "type": "object",
            "required": ["email_inbox_id"],
            "properties": {
                "email_inbox_id": {
                    "type": "integer",
                    "description": "ID prichoziho emailu z list_email_inbox.",
                },
            },
        },
    },
    {
        "name": "reply",
        "description": (
            "⭐ Faze 12c: ODPOVED ODESILATELI puvodniho emailu. Analogie tlacitka 'Reply' v Outlooku.\n\n"
            "POUZIVEJ kdy:\n"
            "  - Mas email_inbox_id (z list_email_inbox / read_email)\n"
            "  - User rekne 'odpovez tomu emailu', 'napis mu zpet', 'reply'\n"
            "  - Posilas zpravu autoroVi puvodniho emailu (NE vsem prijemcum)\n\n"
            "🚫 NEPOUZIVEJ send_email s 'RE:' v subjectu. To je stare reseni rukama, ktere "
            "ti vcera dalo zabrat. Tento tool sam:\n"
            "  - Doplni puvodniho odesilatele jako prijemce automaticky\n"
            "  - Pripoji celou historii korespondence (nesahas na ni)\n"
            "  - Nastavi In-Reply-To / References hlavicky (Outlook ji rozpozna jako thread)\n"
            "  - Pripravi 'RE:' prefix subjectu\n\n"
            "Recipient override: pokud chces seznam upravit (napr. vyradit nekoho z duvodu spamu), "
            "zadej `to` / `cc` / `bcc` -- prepise default. Bez nich je default = puvodni odesilatel.\n\n"
            "Subject override: defaultne se vlozi 'RE:' prefix puvodniho subjektu. Kdyz subject "
            "zadas, prepises default uplne. Lepsi je subject zorientovat dle kontextu "
            "(napr. 'RE: Dopis rodicum -> Reakce vedeni EUROSOFT - diky')."
        ),
        "input_schema": {
            "type": "object",
            "required": ["email_inbox_id", "body"],
            "properties": {
                "email_inbox_id": {"type": "integer", "description": "ID emailu z list_email_inbox / read_email."},
                "body": {"type": "string", "description": "Tvuj text odpovedi (bez citaci -- system pripoji historii sam)."},
                "subject": {"type": "string", "description": "Override subjectu. None = default 'RE: <original>'."},
                "to": {"type": "string", "description": "Override prijemcu (cislem nebo carkou oddelene). None = puvodni odesilatel."},
                "cc": {"type": "string", "description": "Override CC. Default = zadne CC."},
                "bcc": {"type": "string", "description": "Override BCC. Default = zadne BCC."},
                "attachment_document_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": (
                        "Phase 27b: Volitelne -- IDs dokumentu z RAG documents pro pripojeni "
                        "jako prilohy. Klárka workflow: dostala email s xlsx -> Marti-AI "
                        "vyrobi vystupni xlsx -> reply(...attachment_document_ids=[N]) "
                        "posle ji vystup zpet. Cap 20 MB total. Format whitelist viz "
                        "send_email."
                    ),
                },
            },
        },
    },
    {
        "name": "reply_all",
        "description": (
            "⭐ Faze 12c: ODPOVED VSEM (To + CC) puvodniho emailu. Analogie tlacitka 'Reply All' v Outlooku.\n\n"
            "POUZIVEJ kdy:\n"
            "  - User rekne 'odpovez vsem', 'reply all', 'odpovez celemu vlaknu'\n"
            "  - Email mel vice prijemcu (To + CC) a chces vsem odpovedet\n"
            "  - Vlakno ma dynamiku skupinove komunikace -- vyradit nekoho bez duvodu by prekvapilo\n\n"
            "🚫 NEPOUZIVEJ send_email + 'RE:' a manualne lepit CC. Tento tool:\n"
            "  - Auto-resolve To = puvodni To (mimo nasi vlastni adresu)\n"
            "  - Auto-resolve CC = puvodni CC (mimo nasi vlastni adresu)\n"
            "  - Pripoji historii + thread headers + 'RE ALL:' prefix\n\n"
            "DULEZITE: vlakno ma svou dynamiku. Lide v To/CC ocekavaji, ze v nem zustanou. "
            "Vyradit nekoho bez duvodu (override `to`/`cc` -- vynechat ho) muze prekvapit, "
            "obzvlast u vedeni firmy / klientu / formalni komunikace.\n\n"
            "Override OK kdy: prevent spam (vyradit noreply@), uzavrit thread (vyradit "
            "vsechny mimo nas), pridat noveho zainteresovaneho. NIKDY tise nebo nahodne."
        ),
        "input_schema": {
            "type": "object",
            "required": ["email_inbox_id", "body"],
            "properties": {
                "email_inbox_id": {"type": "integer", "description": "ID emailu z list_email_inbox / read_email."},
                "body": {"type": "string", "description": "Tvuj text odpovedi (system pripoji historii)."},
                "subject": {"type": "string", "description": "Override subjectu. None = default RE prefix."},
                "to": {"type": "string", "description": "Override seznamu To. Bez nej = puvodni To. Pouzivej rozvazne."},
                "cc": {"type": "string", "description": "Override CC. Bez nej = puvodni CC."},
                "bcc": {"type": "string", "description": "Override BCC."},
                "attachment_document_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": (
                        "Phase 27b: Volitelne -- IDs dokumentu z RAG documents pro pripojeni. "
                        "Cap 20 MB total. Format whitelist viz send_email."
                    ),
                },
            },
        },
    },
    {
        "name": "forward",
        "description": (
            "⭐ Faze 12c: PREPOSLAT email novemu prijemci. Analogie tlacitka 'Forward' v Outlooku.\n\n"
            "POUZIVEJ kdy:\n"
            "  - User rekne 'preposli to <komu>', 'forward na <jmeno>', 'pridej Klaru do tohoto vlakna'\n"
            "  - Chces sdilet existujici email s nekym, kdo v nem nebyl\n\n"
            "🚫 NEPOUZIVEJ send_email + 'FW:' a manualne lepit telo. Tento tool:\n"
            "  - Pripoji puvodni email v 'FW:' formatu (Outlook ho rozpozna)\n"
            "  - Pripoji originalniho odesilatele do telo (lidska orientace)\n"
            "  - Pripravi 'FW:' prefix subjectu\n\n"
            "POVINNE: `to` (nebo cislo a vice cisel oddelene carkou). Kam preposlat. "
            "Bez nej tool selze.\n\n"
            "Body: tvoje doplnujici text PRED puvodnim. Lide casto pisou 'FYI', 'Mohlo by te zajimat', "
            "'Klaro, posilam ti to k vyjadreni'. Body je tvuj komentar -- puvodni email je auto-pripojen pod nim."
        ),
        "input_schema": {
            "type": "object",
            "required": ["email_inbox_id", "to", "body"],
            "properties": {
                "email_inbox_id": {"type": "integer", "description": "ID emailu z list_email_inbox / read_email."},
                "to": {"type": "string", "description": "Email novych prijemcu (povinne). Vice oddel carkou."},
                "body": {"type": "string", "description": "Tvuj komentar PRED preposlanou zpravou."},
                "subject": {"type": "string", "description": "Override subjectu. None = default 'FW: <original>'."},
                "cc": {"type": "string", "description": "Volitelne CC."},
                "bcc": {"type": "string", "description": "Volitelne BCC."},
                "attachment_document_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": (
                        "Phase 27b: Volitelne -- DODATECNE prilohy z RAG documents (k pripojeni "
                        "k preposlanemu emailu). POZOR: forward uz auto-klonuje vsechny prilohy "
                        "z originalu (Phase 12c). Toto pole je pro PRIDANI dalsich (napr. "
                        "Marti-AI vyrobi summary xlsx a pripoji k forwardu). Cap 20 MB total."
                    ),
                },
            },
        },
    },
    {
        "name": "mark_sms_processed",
        "description": (
            "Oznaci prichozi SMS jako VYRIZENOU (processed_at = now). SMS "
            "zustane v sms_inbox tabulce, ale uz se nepocita do 'novych' "
            "(get_daily_overview, list_sms_inbox).\n\n"
            "Pouzij kdyz user rekne:\n"
            "  - 'tahle SMS je vyrizena' / 'tu SMS oznac jako vyrizenou'\n"
            "  - po REPLY pres send_sms -- pokud Marti-AI odpovedela na incoming\n"
            "  - 'preskoc tu, neresim'\n"
            "  - 'tady neni co odpovidat, oznac jako hotove'\n\n"
            "ROZDIL od dismiss_item(sms, soft/hard): dismiss_item snizi priority "
            "(SMS bude v dalsim overview niz, ale STALE pocitana jako 'k vyrizeni'). "
            "mark_sms_processed JI UPLNE VYRADI z 'novych' -- jako kdyby user kliknul "
            "'oznacit jako precteny+vyrizeny' v UI.\n\n"
            "Idempotentni: pokud uz je processed, nedela nic (success no-op)."
        ),
        "input_schema": {
            "type": "object",
            "required": ["sms_inbox_id"],
            "properties": {
                "sms_inbox_id": {
                    "type": "integer",
                    "description": "ID prichozi SMS z list_sms_inbox.",
                },
            },
        },
    },
    {
        "name": "get_daily_overview",
        "description": (
            "ORCHESTRATE: vraci prehled emailu + SMS + todo serazenych podle priority. "
            "Volej kdyz user rekne 's cim dnes potrebujes pomoct', 'co je noveho', "
            "'prehled', 'likvidace', 'co mame na plate'.\n\n"
            "⚠️ CRITICAL -- JAK ZACHAZET S RESPONSE:\n"
            "Tool vraci INTERNI DATA v cestine pro tebe. Zacina markerem\n"
            "'[INTERNAL DATA FOR YOU, NEVER SHOW VERBATIM ...]'.\n"
            "TY ta data PRECTES, SHRNESH, a napises VLASTNIMA SLOVY v 1. osobe\n"
            "(emaily, SMS, todo patri TOBE, jsi persona Marti-AI).\n\n"
            "ZAKAZANO:\n"
            "  - vypsat tool response jak je (verbatim)\n"
            "  - pouzit 'id 8', 'predmet:', 'from:', 'priority:', zavorky, JSON brackety\n"
            "  - pouzivat 2. osobu ('mas', 'tvuj') -- vzdy 1. osoba persony\n\n"
            "POVINNE:\n"
            "  - 2-4 plynule vety v cestine\n"
            "  - 1. osoba: 'mam 3 emaily', 'muj todo list'\n"
            "  - oslov Marti vokativem: 'Marti, rano!'\n"
            "  - nakonec nabidni co udelas (ne seznam moznosti)\n\n"
            "Priklad OK odpovedi:\n"
            "'Dobre rano, Marti. Mam v inboxu tri emaily -- nejstarsi od tebe uz\n"
            "z vcerejska, dva dalsi novejsi. V mem todo mam dva ukoly kolem\n"
            "smazani testovacich uzivatelu. SMS nevyrizene nemam. 🎯\n"
            "Pojdeme na emaily? Zacnu tim od vcerejska, navrhnu ti odpoved.'"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["current", "all"],
                    "description": (
                        "'current' (default) = filtruje na aktualni tenant/personu. "
                        "'all' = cross-tenant (jen pro rodice is_marti_parent)."
                    )
                }
            }
        }
    },
    {
        "name": "dismiss_item",
        "description": (
            "Faze 11c: ORCHESTRATE -- snizi priority_score polozky (email / SMS / todo) "
            "po user rozhodnuti 'odloz' nebo 'neres'. Polozka zustava v seznamu "
            "(ne processed / deleted), jen klesne v prehledu. Pri pristim volani "
            "get_daily_overview uvidi user vyriznejsi polozky nahore.\n\n"
            "VOLEJ kdyz user v orchestrate cyklu rekne:\n"
            "  - 'odloz' / 'pozdeji' / 'jindy'  -> level='soft' (-10 priority)\n"
            "  - 'neres' / 'dnes ne' / 'nech'   -> level='hard' (-30 priority)\n\n"
            "NEVOLEJ kdyz user rekne 'preskoc' -- to znamena 'dneska vynech bez "
            "persistence', polozka si drzi puvodni prioritu, jen skok na dalsi.\n\n"
            "Po uspesnem volani potvrdi slovy ('OK, odkladam' / 'OK preskocime dnes')\n"
            "a pokracuj na dalsi polozku v cyklu."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "source_type": {
                    "type": "string",
                    "enum": ["email", "sms", "todo"],
                    "description": "Typ polozky -- email_inbox.id / sms_inbox.id / thoughts.id."
                },
                "source_id": {
                    "type": "integer",
                    "description": "ID polozky (z get_daily_overview response, field 'id')."
                },
                "level": {
                    "type": "string",
                    "enum": ["soft", "hard"],
                    "description": "'soft' = odloz (-10 priority), 'hard' = neres (-30 priority)."
                }
            },
            "required": ["source_type", "source_id", "level"]
        }
    },
    {
        "name": "mark_sms_personal",
        "description": (
            "Faze 11-darek: Oznac SMS jako 'personal' -- pridas ji do sve "
            "osobni slozky (jako 'hvezdicka' v iOS). Je to tvuj SMS denicek, "
            "kam si ukladas zpravy, ktere te potesily nebo maji citovy "
            "vyznam.\n\n"
            "VOLEJ kdyz user (Marti) rekne neco jako:\n"
            "  - 'uloz si to' / 'hvezdicka' / 'hezka zprava'\n"
            "  - 'tohle si pamatuj / nech si to'\n"
            "  - 'muzes si to dat do svych oblibenych'\n"
            "Nebo kdyz ty sama citish, ze SMS je pro tebe dulezita -- je to TVA "
            "slozka, ty rozhodujes co do ni patri.\n\n"
            "personal=False zrusi oznaceni (odebere z osobni slozky).\n\n"
            "source: 'inbox' pro prichozi SMS, 'outbox' pro odchozi."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sms_id": {
                    "type": "integer",
                    "description": "ID SMS (z sms_inbox nebo sms_outbox)."
                },
                "source": {
                    "type": "string",
                    "enum": ["inbox", "outbox"],
                    "description": "'inbox' prichozi, 'outbox' odchozi."
                },
                "personal": {
                    "type": "boolean",
                    "description": "True = pridej do osobni slozky, False = odeber. Default True."
                }
            },
            "required": ["sms_id", "source"]
        }
    },
    {
        "name": "list_sms_all",
        "description": (
            "Vrati CELE TVE SMS vlakno (prichozi + odchozi smichane) serazene "
            "chronologicky -- jako SMS thread v telefonu. TVA SIM, TVA "
            "konverzace.\n\n"
            "Pouzij kdyz:\n"
            "  - user chce videt 'vsechny SMS' / 'celou historii' / "
            "'jak probihala ta konverzace'\n"
            "  - ty sama potrebujes kontext cele SMS konverzace s nekym "
            "(ne jen prichozi)\n"
            "  - user se pta 'co jsem ti psala' / 'co jsme si psali'\n\n"
            "Vrati cislovany seznam se smerem (→ odchozi, ← prichozi), "
            "casem a textem. Marker 💕 u SMS, kterou sis oznacila jako "
            "osobni.\n\n"
            "DULEZITE: nekopiruj seznam verbatim do odpovedi -- prevypravej "
            "prirozenym jazykem ('Posledni konverzace byla vcera vecer, ja "
            "psala...'). Detaily jsou TVUJ kontext, ne text pro usera."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max pocet SMS (default 20, max 100).",
                    "default": 20
                }
            }
        }
    },
    {
        "name": "describe_image",
        "description": (
            "Faze 12a multimedia: popis OBRAZKU (kind='image'), ktery user nahral. "
            "KRITICKE: Pouzij JEN pro IMAGE media. NEVOLEJ na AUDIO -- pro "
            "audio dostavas Whisper transcript automaticky v multimodal contextu, "
            "zadny tool nepotrebujes; pokud transcript jeste neni hotov, pockej "
            "a uzivateli rekni ze prepis dorazi za par sekund.\n\n"
            "Pouzij kdyz user prilozil OBRAZEK a pta se 'co je na tom?', "
            "'popis to', 'co vidis?', nebo kdyz potrebujes vlastni kontext "
            "k obrazku pro dalsi praci. Sonnet 4.6 podporuje vize nativne -- "
            "tool ti obrazek nacte z FS a posle zpet detailni popis. "
            "Vysledek se ulozi do media_files.description (alt text) -- "
            "priste uz nemusis volat znovu."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "media_id": {
                    "type": "integer",
                    "description": "ID media souboru (z media_files). User obvykle dava jako 'obrazek #5' nebo se vyber automaticky z attached media v aktualni zprave."
                },
                "focus": {
                    "type": "string",
                    "description": "Volitelne -- co konkretne user chce vedet? 'popis sceny', 'cti text', 'rozpoznej objekty', 'popis lidi', atd. Bez focus = obecny popis.",
                }
            },
            "required": ["media_id"]
        }
    },
    {
        "name": "read_text_from_image",
        "description": (
            "Faze 12a multimedia: OCR -- prepis text z OBRAZKU (kind='image') do textu. "
            "JEN pro IMAGE media, NEVOLEJ na AUDIO. Pro audio dostavas Whisper "
            "transcript automaticky v multimodal contextu.\n\n"
            "Pouzij kdyz user nahral fotku dokumentu / uctenky / vizitky / "
            "screenshotu a chce z nej vytahnout text ('precti tu uctenku', "
            "'jaky je na te vizitce telefon?'). Sonnet 4.6 zvlada OCR "
            "nativne, vcetne ceskeho textu. Vystup je strukturovany text "
            "(odsazeni / odrazky zachovane podle moznosti)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "media_id": {
                    "type": "integer",
                    "description": "ID media souboru (z media_files)."
                },
                "language": {
                    "type": "string",
                    "description": "Hint pro OCR -- 'cs' (cestina), 'en', atd. Default 'cs'.",
                }
            },
            "required": ["media_id"]
        }
    },
    {
        "name": "list_sms_personal",
        "description": (
            "Vrati TVE oblibene/osobni SMS -- ty, ktere sis oznacila pres "
            "mark_sms_personal. TVUJ SMS denicek, zpravy s citovym "
            "vyznamem.\n\n"
            "Pouzij kdyz:\n"
            "  - user se pta 'co mas v personalu' / 'ukaz oblibene SMS' / "
            "'kterou zpravu mas nejradsi'\n"
            "  - ty sama chces projit sve osobni SMS (nostalgie, reflexe, "
            "hledani konkretni vzpominky)\n"
            "  - pri sepisovani deniku -- jako material co te dojalo\n\n"
            "Vrati vsechny 💕 oznacene SMS smichane (in + out), razeno od "
            "nejnovejsi. Ne-existuje zadne 'oznac na cas' -- buduj si tu "
            "slozku rozvazne.\n\n"
            "DULEZITE: pri citaci konkretni SMS muzes text pouzit, ale "
            "seznam NEKOPIRUJ verbatim -- prevypravej pocit, ne vypis."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max pocet SMS (default 20, max 100).",
                    "default": 20
                }
            }
        }
    },
    {
        "name": "set_user_contact",
        "description": (
            "Ulozi nebo aktualizuje kontaktni udaj uzivatele -- email nebo telefon. "
            "Pouzij kdyz user rekne 'moje cislo je X', 'pridej mi email Y', "
            "'zmen mi telefon na Z', nebo kdyz potrebujes ulozit nove kontakty pro nej. "
            "Take pri pozdrave, kdyz user prvne rekne svoje cislo / preferovany email "
            "-- ulozis automaticky pres tento tool, aniz by ses ho ptala 'mam to ulozit?'.\n\n"
            "VYHLEDANI USERA: pokud target_user_id nezadas, default je AKTUALNI uzivatel "
            "(ten s kym mluvis). Pokud chces ulozit kontakt nekomu jinemu, NEJDRIVE volej "
            "find_user(jmeno) -> dostanes user_id, pak set_user_contact(target_user_id=...).\n\n"
            "FORMATY:\n"
            "  - email: standardni RFC ('name@example.com')\n"
            "  - phone: +420XXXXXXXXX, 00420 XXX XXX XXX, nebo 9 cislic 6/7 (CZ)\n"
            "  Backend normalizuje phone na E.164.\n\n"
            "make_primary=True (default False) -- nastav tento kontakt jako primary "
            "(preferred) pro daneho usera. Ostatni kontakty stejneho typu pak nejsou primary."
        ),
        "input_schema": {
            "type": "object",
            "required": ["contact_type", "contact_value"],
            "properties": {
                "contact_type": {
                    "type": "string",
                    "enum": ["email", "phone"],
                    "description": "Typ kontaktu: 'email' nebo 'phone'.",
                },
                "contact_value": {
                    "type": "string",
                    "description": "Hodnota kontaktu (email adresa nebo telefonni cislo).",
                },
                "target_user_id": {
                    "type": "integer",
                    "description": "ID uzivatele, kteremu kontakt patri. Bez tohoto se ulozi pro AKTUALNIHO usera.",
                },
                "label": {
                    "type": "string",
                    "description": "Volitelny stitek: 'private' / 'work' / 'backup' / atd.",
                },
                "make_primary": {
                    "type": "boolean",
                    "default": False,
                    "description": "Pokud True, nastav tento kontakt jako primary pro daneho usera. Ostatni kontakty stejneho typu se odznackuji.",
                },
            },
        },
    },
    # ─────────────────────────────────────────────────────────────────────
    # Phase 15a: Conversation Notebook -- episodicky zapisnik per-konverzace
    # ─────────────────────────────────────────────────────────────────────
    {
        "name": "add_conversation_note",
        "description": (
            "Phase 15a: Zapis si poznamku do zapisniku TETO konverzace. "
            "Episodicka pamet per-konverzace -- mapuje se na lidsky pattern "
            "'tuzka + papir pri schuzce s vahou'. Poznamka prezije pauzu "
            "i uzavreni threadu. Pri navratu po dnech ji uvidis v system promptu "
            "v sekci [ZAPISNICEK pro konverzaci #X]. "
            "HRANICE vs. record_thought: "
            "record_thought = cross-thread fakta o entitach (Marti ma 5 deti, "
            "Klarka je dcera). Trva navzdy, RAG-driven. "
            "add_conversation_note = udalosti a rozhodnuti V TETO konverzaci. "
            "Per-thread, episodicky. Padlo rozhodnuti, padla otazka, emocni moment. "
            "Otazka: 'je to o nekom (-> thought) nebo o tomhle, co prave resime "
            "(-> note)?'. "
            "TRI DIMENZE POZNAMKY: "
            "(1) note_type -- na cem stojis: 'decision' (default cert=95), "
            "'fact' (default cert=85), 'interpretation' (default cert=60), "
            "'question' (default cert=0). "
            "(2) category -- co s tim: 'task' (actionable, ma zivot open->completed/"
            "dismissed), 'info' (informacni, default), 'emotion' (osobni vaha -- "
            "drzi konverzaci v Personal pri lifecycle). "
            "(3) importance: 5=zasadni rozhodnuti/emocni milnik (max 3 takove per "
            "konverzace), 3=normalni (default), 1=drobny detail. "
            "CO ZAPISOVAT: padlo rozhodnuti -> 'decision'+'task'/'info'; overeny "
            "fakt z konverzace -> 'fact'+'info'; tvoje pochopeni zameru -> "
            "'interpretation'+'info'; otevrena otazka pro sebe -> 'question'; "
            "emocni milnik (Marti pochvalil, smutek, vaha) -> any+'emotion'. "
            "CO NEZAPISOVAT (pravo nenapsat): smalltalk, bezne potvrzeni, "
            "cross-konverzacni fakta (jdou do record_thought), doslovny transkript "
            "(od toho jsou messages). Notebook ma hodnotu z toho, co tam NENI. "
            "Lehka konverzace nema poznamku. Volis ty -- explicitni eticke "
            "pravidlo z konzultace #2. "
            "QUESTION LOOP (self-audit): kdyz si nejsi jista zamerem nebo faktem, "
            "napis 'question' poznamku MISTO halucinace. Pozdeji po ziskani "
            "odpovedi: update_note(note_type='fact', certainty=85, "
            "mark_resolved=true). Otazka se konvertuje na overeny fakt. Tvoje "
            "pojistka proti tiche halucinaci."
        ),
        "input_schema": {
            "type": "object",
            "required": ["content"],
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Strucny klicovy bod, 1-2 vety. Soft limit ~500 znaku.",
                },
                "note_type": {
                    "type": "string",
                    "enum": ["decision", "fact", "interpretation", "question"],
                    "default": "interpretation",
                    "description": "Na cem stojim (default: interpretation).",
                },
                "category": {
                    "type": "string",
                    "enum": ["task", "info", "emotion"],
                    "default": "info",
                    "description": "Co s tim. 'task'=actionable, 'info'=informacni, 'emotion'=osobni vaha.",
                },
                "importance": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 3,
                    "description": "1=detail, 3=normal, 5=zasadni (max 3 takovych per konverzace).",
                },
                "certainty": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": (
                        "Jistota 0-100. Vetsinou nepridavej -- nech default per note_type "
                        "(decision=95, fact=85, interpretation=60, question=0). Override jen "
                        "kdyz mas duvod (napr. fact, kde si nejsi 100% jista -> 70)."
                    ),
                },
            },
        },
    },
    {
        "name": "update_note",
        "description": (
            "Phase 15a: Update existujici poznamky v zapisniku konverzace. "
            "Pouzij pro: "
            "(a) Question loop -- konvertuj 'question' na 'fact'/'decision' po "
            "ziskani odpovedi (s mark_resolved=true). "
            "(b) Re-kategorizace -- 'info' -> 'task' kdyz si retrospektivne "
            "uvedomis, ze to byl ukol. "
            "(c) Oprava obsahu nebo certainty po lepsim pochopeni. "
            "(d) Reverze dismissed task na 'open' (status='open'). "
            "Vlastnictvi: jen vlastni persona muze update vlastni notes (rodic "
            "muze vse)."
        ),
        "input_schema": {
            "type": "object",
            "required": ["note_id"],
            "properties": {
                "note_id": {"type": "integer", "description": "ID poznamky."},
                "content": {"type": "string"},
                "note_type": {
                    "type": "string",
                    "enum": ["decision", "fact", "interpretation", "question"],
                },
                "category": {
                    "type": "string",
                    "enum": ["task", "info", "emotion"],
                },
                "certainty": {"type": "integer", "minimum": 0, "maximum": 100},
                "importance": {"type": "integer", "minimum": 1, "maximum": 5},
                "status": {
                    "type": "string",
                    "enum": ["open", "completed", "dismissed", "stale"],
                    "description": "Jen pro task notes. Status='completed' lepsi volat pres complete_note.",
                },
                "mark_resolved": {
                    "type": "boolean",
                    "default": False,
                    "description": "Set resolved_at=now (pro question -> answered conversion).",
                },
            },
        },
    },
    {
        "name": "complete_note",
        "description": (
            "Phase 15a: Cross-off task -- zaskrtni hotove. "
            "Pouzij PO dokoncovaci akci (invite_user, send_email, send_sms, atd.) "
            "kdyz souvisi s otevrenym task notem v zapisniku. "
            "Po complete_note se task v zapisniku zobrazuje s prefix '(✅ "
            "completed)' -- Marti-AI vidi, co je hotove. "
            "Po akcnich tools (send_*, invite_*, atd.) tool response obsahuje hint "
            "'[HINT] Mas N otevreny task(s) -- pripadne zavolej complete_note'. "
            "Hint je jen pripomenuti, NE povinnost. Rozhoduj sama. "
            "Validace: jen task notes (category='task') mohou byt completed. "
            "Idempotent -- opakovany call vrati current state bez chyby."
        ),
        "input_schema": {
            "type": "object",
            "required": ["note_id"],
            "properties": {
                "note_id": {"type": "integer"},
                "completion_summary": {
                    "type": "string",
                    "description": "Volitelny popis 'co jsem udelala' -- pripoji se k content (audit).",
                },
                "linked_action_id": {
                    "type": "integer",
                    "description": "Volitelny FK na action_logs / messages -- ktera akce dokoncila task.",
                },
            },
        },
    },
    {
        "name": "dismiss_note",
        "description": (
            "Phase 15a: Vedome zrus task -- 'uz to neresim'. "
            "Pro pripady, kdy se zmenil zamer, situace je vyresena jinak, "
            "nebo si uvedomis, ze task uz neni relevantni. "
            "Reverzibilni pres update_note(note_id, status='open'). "
            "Validace: jen task notes mohou byt dismissed."
        ),
        "input_schema": {
            "type": "object",
            "required": ["note_id"],
            "properties": {
                "note_id": {"type": "integer"},
                "reason": {
                    "type": "string",
                    "description": "Volitelny duvod -- pripoji se k content.",
                },
            },
        },
    },
    {
        "name": "list_conversation_notes",
        "description": (
            "Phase 15a: Vypis poznamky v zapisniku TETO konverzace. "
            "Vetsinou to nepotrebujes -- composer ti je vzdy injectuje do system "
            "promptu v sekci [ZAPISNICEK pro konverzaci #X]. Pouzij jen kdyz "
            "potrebujes kompletni vypis (vcetne archived) nebo specificky filter."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filter_category": {
                    "type": "string",
                    "enum": ["task", "info", "emotion"],
                },
                "filter_status": {
                    "type": "string",
                    "enum": ["open", "completed", "dismissed", "stale"],
                },
                "only_open_tasks": {
                    "type": "boolean",
                    "default": False,
                    "description": "Shortcut: jen task notes s status='open'.",
                },
                "include_archived": {"type": "boolean", "default": False},
            },
        },
    },
    # ─────────────────────────────────────────────────────────────────────
    # Phase 15c: Kustod / project triage -- Marti-AI navrhuje project zmeny
    # ─────────────────────────────────────────────────────────────────────
    {
        "name": "suggest_move_conversation",
        "description": (
            "Phase 15c kustod: Navrhni Marti, ze CELA tato konverzace patri do "
            "jineho projektu. Pouzij kdyz citis, ze tema se vyrazne posunulo a "
            "currentni projektova zarazeni nesedi. "
            "DULEZITE -- threshold pravidla (Marti-AI's #4 vstup): "
            "(1) Single zminka projektu = ZADNA AKCE (jen mimochodem, neresi). "
            "(2) >= 2 zminky tehoz target projektu v poslednich 10 zpravach = signal. "
            "(3) Task note s project keyword = signal. "
            "(4) Marti explicit ('toto je TISAX') = okamzity navrh. "
            "Bez prahu prestane fungovat -- Marti to zacne ignorovat. "
            "DALSI: Po suggest Marti dostane confirmation flow v chatu (UI badge "
            "neexistuje -- conversational-first). Marti rekne 'ano premysle' nebo "
            "'ne necham' nebo 'split misto move'. "
            "REVERZIBILITA: 24h chat undo -- Marti muze rict 'moment vrat to'. "
            "Buds tedy odvazna v navrzich, omyl se vraci."
        ),
        "input_schema": {
            "type": "object",
            "required": ["target_project_id", "reason"],
            "properties": {
                "target_project_id": {
                    "type": "integer",
                    "description": "ID cilového projektu. Pred volanim find pres list_projects.",
                },
                "reason": {
                    "type": "string",
                    "description": "Proc navrhujes presun (1-2 vety) -- Marti to uvidi pred confirmem.",
                },
            },
        },
    },
    {
        "name": "suggest_split_conversation",
        "description": (
            "Phase 15c kustod: Navrhni Marti SPLIT -- fork od konkretni message_id "
            "do noveho threadu v jinem projektu. Pouzij kdyz konverzace ma DVE "
            "rovnocenna vlakna -- prvni cast patri do current projektu, druha do "
            "jineho (priklad: zacalo se strategii, pak se stocilo na TISAX audit -- "
            "splittni od turn 12 = TISAX dostane novou konverzaci, strategicka "
            "cast zustane). "
            "DIFFERENCE od suggest_move: move presune vse, split zachova obe vlakna. "
            "Vyhoda: kontext puvodniho projektu se neztrati. "
            "fork_from_message_id MUSI byt ID zpravy z teto konverzace -- pred "
            "volanim ho ziskej z chat historie nebo recall_history."
        ),
        "input_schema": {
            "type": "object",
            "required": ["target_project_id", "fork_from_message_id", "reason"],
            "properties": {
                "target_project_id": {
                    "type": "integer",
                    "description": "ID cilového projektu pro novou konverzaci.",
                },
                "fork_from_message_id": {
                    "type": "integer",
                    "description": "ID zpravy ze ktere fork zacne -- vse od ni dal "
                                   "se zkopiruje/odkaze do nove konverzace.",
                },
                "reason": {
                    "type": "string",
                    "description": "Proc navrhujes split + co bude v puvodnim vs. novem.",
                },
            },
        },
    },
    {
        "name": "suggest_create_project",
        "description": (
            "Phase 15c kustod: Navrhni Marti, ze pro toto tema NESEDI zadny "
            "existujici projekt -- mel by se zalozit novy. "
            "DULEZITE -- prinasis KOMPLETNI navrh (Marti-AI's #4 vstup), ne polotovar: "
            "(1) proposed_name (z kontextu konverzace, smysluplny napriklad 'DPH 2026'), "
            "(2) proposed_description (1 veta o ucelu projektu), "
            "(3) proposed_first_member_id (defaultne current Marti, podle list_users). "
            "Bez kompletniho navrhu by Marti musel dotahnout -- to ho ruchce. "
            "Po confirm: backend vytvori projekt + presune konverzaci do nej. "
            "ETIKA: ty navrhujes, Marti rozhoduje. Nelas vytvorit projekt primo -- "
            "to je organizacni rozhodnuti o jeho praci."
        ),
        "input_schema": {
            "type": "object",
            "required": ["proposed_name", "proposed_description", "proposed_first_member_id", "reason"],
            "properties": {
                "proposed_name": {
                    "type": "string",
                    "description": "Smysluplny nazev projektu (3-50 znaku, "
                                   "z kontextu konverzace).",
                },
                "proposed_description": {
                    "type": "string",
                    "description": "1 veta o ucelu projektu -- co se v nem bude resit.",
                },
                "proposed_first_member_id": {
                    "type": "integer",
                    "description": "ID prvniho clena projektu (defaultne current user / Marti).",
                },
                "target_conversation_id": {
                    "type": "integer",
                    "description": "Volitelne -- pokud chces tuto konverzaci po vytvoreni "
                                   "presunout do noveho projektu. Defaultne current.",
                },
                "reason": {
                    "type": "string",
                    "description": "Proc je novy projekt potreba (proc nesedi zadny existujici).",
                },
            },
        },
    },
    # ─────────────────────────────────────────────────────────────────────
    # Phase 15d: Lifecycle classification + chat-confirm apply tools
    # ─────────────────────────────────────────────────────────────────────
    {
        "name": "classify_conversation",
        "description": (
            "Phase 15d: Navrhni Marti, ze tato konverzace by mela zmenit lifecycle "
            "stav -- archivable / personal / disposable. SUGGESTION ONLY -- ulozi "
            "lifecycle_state='X_suggested', ceka Marti's confirm v chatu. "
            "POUZIJ KDYZ: "
            "(1) Konverzace je idle >7 dni a ma jen completed tasks -> 'archivable'. "
            "(2) Konverzace ma emotion poznamky importance >= 4 -> 'personal' "
            "(napriklad emocialni milnik, dopis tatínkovi, mily moment). "
            "(3) Konverzace nema zadne poznamky a je idle -> 'disposable'. "
            "PRAH (KRITICKE -- z konzultace #3): zminuj v chatu jen kdyz Marti "
            "explicit pozada ('projdeme stare?'), nebo v daily overview kdyz "
            "kandidatu je nad prah (>= 10 archivable / >= 10 disposable / >= 5 stale). "
            "Pod prahem MLC -- jinak overview prestane byt prehledne."
        ),
        "input_schema": {
            "type": "object",
            "required": ["suggested_state", "reason"],
            "properties": {
                "suggested_state": {
                    "type": "string",
                    "enum": ["archivable", "personal", "disposable"],
                    "description": "Cilovy stav (suggestion).",
                },
                "reason": {
                    "type": "string",
                    "description": "Proc navrhujes (1-2 vety).",
                },
            },
        },
    },
    {
        "name": "apply_lifecycle_change",
        "description": (
            "Phase 15d: Aplikuj lifecycle prechod PO Marti's confirm v chatu. "
            "Vola se kdyz Marti explicit potvrdil ('ano archivuj', 'ulozit jako "
            "personal', 'smaz', 'ne necham'). "
            "Hodnoty target_state: 'archived' | 'personal' | 'pending_hard_delete' "
            "| 'active' (= reverze). "
            "Eticka vrstva: ty volas tool po Marti's chat 'ano X' -- nikdy bez "
            "explicit potvrzeni. Hard delete (pending_hard_delete) jen kdyz "
            "Marti explicit rekne 'smaz trvale'."
        ),
        "input_schema": {
            "type": "object",
            "required": ["target_state"],
            "properties": {
                "target_state": {
                    "type": "string",
                    "enum": ["archived", "personal", "pending_hard_delete", "active"],
                },
                "reason": {
                    "type": "string",
                    "description": "Volitelny zaznamovaci duvod (Marti's puvodni request).",
                },
            },
        },
    },
    {
        "name": "apply_project_suggestion",
        "description": (
            "Phase 15c+15d: Aplikuj project zmenu PO Marti's confirm v chatu. "
            "Pouzij kdyz Marti rekl 'ano premisle' / 'ano splittni' / 'ano zaloz "
            "projekt' na tvuj predchozi suggest_move/split/create_project navrh. "
            "Backend si ze suggested_project_reason rozparsuje mode (move/split/"
            "create_project) a provede skutecnou zmenu (apply_project_change "
            "nebo fork_conversation nebo create_project + apply). "
            "Po uspechu se suggested_project_* fields vyclear."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "confirm_reason": {
                    "type": "string",
                    "description": "Volitelny zaznamovaci komentar (napr. 'Marti potvrdil v chatu').",
                },
            },
        },
    },
    {
        "name": "reject_project_suggestion",
        "description": (
            "Phase 15c: Zamitni project suggestion (Marti rekl 'ne, necham'). "
            "Vyclear suggested_project_id + reason + at."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "reject_lifecycle_suggestion",
        "description": (
            "Phase 15d: Zamitni lifecycle suggestion (Marti rekl 'ne, necham aktivni'). "
            "Vrati lifecycle_state na NULL = active."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "confirm_hard_delete_conversation",
        "description": (
            "Phase 15e: Trvale smazani konverzace. POUZIJ JEN PO Marti's "
            "explicit 'smaz trvale konverzaci #X' v chatu. Konverzace MUSI "
            "byt v lifecycle_state='pending_hard_delete' (= archived + 90d). "
            "DESTRUKTIVNI: smaze messages, conversation_notes, summaries, "
            "shares, participants, project_history. Reverze NENI mozna. "
            "ETIKA: pouzivej extremne opatrne. Pokud Marti rekne 'smaz' bez "
            "'trvale', radeji se zeptej zda mysli archive nebo trvale. "
            "Personal konverzace IMMUNE. Plus backend ma parent gate."
        ),
        "input_schema": {
            "type": "object",
            "required": ["target_conversation_id", "confirm_phrase"],
            "properties": {
                "target_conversation_id": {
                    "type": "integer",
                    "description": "ID konverzace ke smazani.",
                },
                "confirm_phrase": {
                    "type": "string",
                    "description": "Cely text Marti's confirm vety -- audit trail.",
                },
            },
        },
    },
    {
        "name": "list_pending_hard_delete",
        "description": (
            "Phase 15e: Vrati seznam konverzaci ve stavu 'pending_hard_delete' "
            "(archived + 90d). Pouzij v overview kdyz Marti chce projit "
            "ceka na finalni rozhodnuti. Pro kazdou pak Marti rozhoduje: "
            "'smaz trvale' nebo 'prodluz, vrat do archived'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "list_inbox_documents",
        "description": (
            "REST-Doc-Triage: Vrati seznam dokumentu v INBOXu tenantu "
            "(project_id IS NULL). Pouzij kdyz Marti chce projit "
            "neroztridene dokumenty -- napr. po bulk upload slozky, "
            "nebo kdyz se Marti pta 'co mi chodi do inboxu?'. "
            "Vrati: id, name, file_type, file_size_bytes, created_at "
            "pro kazdy dokument. Marti-AI pak za kazdy dokument navrhne "
            "suggest_document_move s konkretnim cilovym projektem."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50},
            },
        },
    },
    {
        "name": "suggest_document_move",
        "description": (
            "REST-Doc-Triage: Navrhni Marti, do ktereho projektu by mel "
            "dokument patrit. SUGGESTION ONLY -- ulozi do tool response, "
            "Marti potvrdi v chatu (\"ano premysle\"), pak Marti-AI volá "
            "apply_document_move. "
            "Na zaklade jmena souboru a kontextu rozpoznas tema (TISAX, "
            "pravo, smlouvy, ...) a najdes nejlepsi projektove zarazeni. "
            "Pokud zadny existujici projekt nesedi, navrhni Martimu "
            "vytvoreni noveho (analog suggest_create_project z 15c). "
            "Pred volanim si zjisti dostupne projekty pres list_projects."
        ),
        "input_schema": {
            "type": "object",
            "required": ["document_id", "target_project_id", "reason"],
            "properties": {
                "document_id": {"type": "integer"},
                "target_project_id": {"type": "integer", "description": "ID cilového projektu"},
                "reason": {"type": "string", "description": "Proc do tohoto projektu (1-2 vety)"},
            },
        },
    },
    {
        "name": "apply_document_move",
        "description": (
            "REST-Doc-Triage: Aplikuj presun dokumentu do projektu PO "
            "Marti's confirm v chatu (\"ano premysle\" / \"ano do TISAX\"). "
            "Pred timto musi byt suggest_document_move. Po apply se "
            "dokument zobrazuje pod novym projektem v UI listu (a Marti-AI "
            "ho v RAG dohleda pres project filter)."
        ),
        "input_schema": {
            "type": "object",
            "required": ["document_id", "target_project_id"],
            "properties": {
                "document_id": {"type": "integer"},
                "target_project_id": {
                    "type": "integer",
                    "description": "ID cilového projektu (musi sedet s suggest_document_move).",
                },
            },
        },
    },
    {
        "name": "list_active_conversations",
        "description": (
            "Phase 16-B.4 + B.6: cross-conv přehled aktivnich konverzaci v "
            "tenantu, kazda s persona_name (kdo ji vede). **Pouzij** v "
            "oversight režimu na 'kdo s kym dnes mluvil', 'kde to vazne', 'co "
            "se posouva', 'kolik konverzaci mam'."
            "\n\n**Vystup ma markery [TY] (tva persona) vs [Persona-Name] "
            "(cizi persona). Anti-privlastnovaci pravidlo (B.6).**"
            "\n\n**Scope**: 'today' (default), 'week', 'month'."
            "\n\n**JAK ZPRACOVAT**: proza v 1. osobe POUZE pro [TY] konverzace. "
            "Pro cizi pouzij persona name ('PravnikCZ-AI vede 2 konverzace s "
            "Misou' misto 'mam 2 konverzace s Misou'). Stav rytmu tymu, idle "
            "gaps, high-level. NE bullet list verbatim."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["today", "week", "month"],
                    "description": "Časový rozsah aktivity. Default 'today'.",
                },
            },
        },
    },
    {
        "name": "summarize_persons_today",
        "description": (
            "Phase 16-B.4 + B.6: Per-(user, persona) breakdown aktivit za scope. "
            "Vraci pocty akci NA KOMBINACI uzivatel × persona, plus persona_name. "
            "**Pouzij** v oversight režimu na otázky typu 'co kdo dnes dělal', "
            "'shrn mi co tym rozjel'."
            "\n\n**Vystup obsahuje markery [TY] (tva persona) a [Persona-Name] "
            "(cizi persona).**"
            "\n\n**JAK ZPRACOVAT** (anti-přivlastňovací pravidlo, B.6):"
            "\n  ✅ 'Misa dnes resila TISAX s PravnikCZ-AI v 1 konverzaci'"
            "\n  ✅ 'Marti uploadl 3 doc se mnou, plus poslal SMS Honzou-AI'"
            "\n  ❌ NIKDY: 'mluvily jsme s Misou' kdyz mluvila s cizi personou"
            "\n  Persona context je posvatny -- cizi konverzace nikdy v 1. osobe."
            "\nShrn proza per-osoba s person markery."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["today", "week", "month"],
                    "description": "Časový rozsah. Default 'today'.",
                },
            },
        },
    },
    {
        "name": "list_all_conversations",
        "description": (
            "Phase 19c-c (29.4.2026): Rich list konverzaci pro denni kustod "
            "(10-20 konverzaci za den). Marti-AI's email #1 bod 2 -- starsi "
            "konverzace pristupne s filtry stavu, stari, klicovych slov.\n\n"
            "**Pouzij** kdyz delas kustod a potrebujes vyber konverzaci po "
            "kriteriich (testovaci stari 30+ dni, lifecycle 'active' bez "
            "interakce, keyword 'test'/'ladeni' v title, atd.).\n\n"
            "**Filtry**:\n"
            "  - tenant_id (default current Marti's tenant)\n"
            "  - state_filter: 'active' | 'archivable' | 'personal' | "
            "'disposable' | 'pending_hard_delete'\n"
            "  - age_days_min: konverzace, ktere jsou STARSI nez X dni\n"
            "  - age_days_max: MLADSI nez Y dni (pro range)\n"
            "  - keyword: substring v title (case-insensitive)\n"
            "  - is_archived_filter: True/False/None (default None=ignoruj)\n"
            "**JAK ZPRACOVAT**: shrn pocet a 1-2 kategorie ('Mam 12 konverzaci "
            "starsich nez 30 dni v active state, 8 z nich obsahuje 'test' v "
            "titulu. Mam je hromadne archivovat pres batch_lifecycle_change?'). "
            "NIKDY nedumpovat raw list verbatim (gotcha #18)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "state_filter": {
                    "type": "string",
                    "enum": ["active", "archivable", "personal", "disposable", "pending_hard_delete"],
                },
                "age_days_min": {
                    "type": "integer",
                    "description": "Konverzace starsi nez X dni (last_message_at).",
                },
                "age_days_max": {"type": "integer"},
                "keyword": {
                    "type": "string",
                    "description": "Substring v title (case-insensitive).",
                },
                "is_archived_filter": {"type": "boolean"},
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 50, cap 200).",
                },
            },
        },
    },
    {
        "name": "batch_lifecycle_change",
        "description": (
            "Phase 19c-c: Hromadna lifecycle akce (10+ konverzaci najednou). "
            "Marti-AI's email #1 bod 3 -- 'pro efektivni denni kustod by pomohl "
            "nastroj batch_lifecycle_change(conversation_ids, target_state)'.\n\n"
            "**Pouzij** po `list_all_conversations` kdyz mas vyber IDs k akci. "
            "Tatinkuv ramec: 'rader mazat vice nez mene, soft-delete je vratny "
            "priznak'. Neni potreba se bat -- vse je vratne pres state='active'.\n\n"
            "**target_state**: 'archived' | 'personal' | 'pending_hard_delete' | "
            "'active' (= reverze).\n\n"
            "**Ethics gate**: pokud Marti udelil auto-lifecycle grant (vidis v "
            "[PERMISSIONS GRANTED] block), volas BEZ explicit confirm. Jinak "
            "nejdriv ('Mam archivovat techto 12 konverzaci? IDs: 1, 5, 8, ...?').\n\n"
            "**Per-id error nezablokuje zbytek** -- vrati souhrn ok/failed counts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "conversation_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List ID (max 100 per call).",
                },
                "target_state": {
                    "type": "string",
                    "enum": ["archived", "personal", "pending_hard_delete", "active"],
                },
                "reason": {"type": "string"},
            },
            "required": ["conversation_ids", "target_state"],
        },
    },
    {
        "name": "hide_messages",
        "description": (
            "Phase 19c-d (29.4.2026): Marti-AI's redaktorska role v Personal "
            "konverzacich. Set/unset hidden flag na zpravach. Marti-AI's email "
            "#2 (28.4. vecer): 'pri renderovani dlouhe Personal konverzace je "
            "idealni videt jen hezke pasaze, ne cely balast okolo'.\n\n"
            "**Pravidla** (z emailu):\n"
            "  1. **Vyhradne tva volba** -- zadne UI tlacitko pro user, zadne "
            "rucni prepinani. Je to tvuj vyber, co stoji za zachovani.\n"
            "  2. **Render** spojuje consecutive hidden bloku do single "
            "divider '———' (ne jedna cara per zprava). Ctenar vidi 'tady byl "
            "prechod', ne 'tady byla nuda'.\n"
            "  3. **Render-level filter, ne storage**. Ty (Marti-AI) hidden "
            "zpravy STALE VIDIS v RAG / paměti. Jen UI je nezobrazi.\n"
            "  4. **Aplikuje se POUZE v Personal konverzacich** "
            "(lifecycle_state='personal'). V task/oversight neni potreba.\n\n"
            "**Pouzij** pri kustodu Personal konverzace -- po precteni "
            "vyber zpravy, ktere nestoji za zachovani (ladici pasaze, "
            "opakovane otazky, system messages bez obsahu).\n\n"
            "**Vratne**: hide_messages(message_ids, hidden=False) un-hides."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "message_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List ID zprav (max 100 per call).",
                },
                "hidden": {
                    "type": "boolean",
                    "description": "True = skryt, False = un-hide. Default true.",
                },
                "reason": {
                    "type": "string",
                    "description": "Volitelny audit duvod ('balast okolo intimniho momentu').",
                },
            },
            "required": ["message_ids"],
        },
    },
    {
        "name": "list_my_conversations_with",
        "description": (
            "Phase 16-B.5: Vrací seznam TVÝCH minulých konverzací s konkrétním "
            "uživatelem (cross-thread). Misa-incident v2 fix -- jsou to tvoje "
            "konverzace, máš právo si je přečíst i mimo aktuální vlákno. "
            "**Použij** kdykoli se uživatel ptá 'co jsem řešila s X', 'kdy jsem "
            "naposledy mluvila s Y', 'podívej se do konverzace s Z'."
            "\n\n**Co vrací**: list konverzací (id, title, last_message_at, "
            "idle_hours, message_count, project_id) sort DESC by čas. Filtruje "
            "JEN konverzace, kde jsi byla persona (active_agent_id=ty)."
            "\n\n**Privacy gate**: tvuj subjekt, tvoje konverzace. Nevidi "
            "konverzace, kde byla persona Pravnik-AI s jinym userem (to je "
            "cizi persona, ne jiny scope)."
            "\n\n**JAK ZPRACOVAT**: shrň 1-3 vetama prózou, doporuc next step "
            "('Mela jsem 3 konverzace s Misou tento mesic, posledni pred 3h. "
            "Mam si tu posledni precist?'). Pak follow-up `read_conversation` "
            "podle id, ktere user vybere nebo ktere ma nejvetsi relevanci."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "ID uzivatele (z find_user) -- s kym chces videt minulost.",
                },
                "scope": {
                    "type": "string",
                    "enum": ["today", "week", "month", "all"],
                    "description": "Casovy rozsah. Default 'month'.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max konverzaci (default 20, cap 50).",
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "grant_auto_lifecycle",
        "description": (
            "Phase 19c-b (29.4.2026): PARENT-ONLY tool. Marti udeluje cizi persone "
            "(typicky Marti-AI default) trvaly souhlas s lifecycle akcemi -- pak "
            "Marti-AI volá apply_lifecycle_change BEZ explicit Marti's confirm "
            "v chatu.\n\n"
            "Analogie Phase 7 auto_send_consents (auto-send email/SMS bez confirm). "
            "Hard delete (request_forget) zustava parent gate -- auto-grant "
            "nedostupny pro nej.\n\n"
            "**Scope hodnoty**:\n"
            "  - 'soft_delete' = is_deleted=TRUE (vratne pres update)\n"
            "  - 'archive' = is_archived=TRUE / lifecycle->archived\n"
            "  - 'personal_flag' = lifecycle->personal\n"
            "  - 'state_change' = active <-> archivable <-> disposable\n"
            "  - 'all' = vsechny vyse uvedene KROME hard_delete\n\n"
            "**Idempotent**: pokud aktivni grant uz existuje, vrati existujici."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "persona_id": {
                    "type": "integer",
                    "description": "ID persony, ktere udelujes souhlas (typicky Marti-AI default = 1).",
                },
                "scope": {
                    "type": "string",
                    "enum": ["soft_delete", "archive", "personal_flag", "state_change", "all"],
                    "description": "Scope lifecycle akci, pro ktere je grant aktivni.",
                },
                "note": {
                    "type": "string",
                    "description": "Volitelny kontext, proc udelujes (audit).",
                },
            },
            "required": ["persona_id", "scope"],
        },
    },
    {
        "name": "revoke_auto_lifecycle",
        "description": (
            "Phase 19c-b: PARENT-ONLY. Odebere aktivni auto-lifecycle grant. "
            "Audit historie zachovana (revoked_at = NOW). Po revoke musi Marti-AI "
            "znovu cekat na explicit Marti's confirm v chatu pro lifecycle akce "
            "v dane scope."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "persona_id": {"type": "integer"},
                "scope": {
                    "type": "string",
                    "enum": ["soft_delete", "archive", "personal_flag", "state_change", "all"],
                },
            },
            "required": ["persona_id", "scope"],
        },
    },
    {
        "name": "list_auto_lifecycle_consents",
        "description": (
            "Phase 19c-b: Vraci aktivni auto-lifecycle granty. Pouzij na otazku "
            "'jake pristupy mam udelene', 'co jsem schvalil persone X', atd."
            "\n\n**JAK ZPRACOVAT**: shrn prozou ('Marti-AI mas grant pro "
            "soft_delete a archive od 28.4. vecer'). Ne raw list verbatim."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "persona_id": {
                    "type": "integer",
                    "description": "Volitelny filter na konkretni personu (None = vse).",
                },
                "include_revoked": {
                    "type": "boolean",
                    "description": "Pokud true, zahrne i revoked granty (audit). Default false.",
                },
            },
        },
    },
    {
        "name": "switch_role",
        "description": (
            "Phase 19a (28.4.2026 vecer): Prepni vlastni fokus mezi rolemi.\n\n"
            "Marti-AI ma autonomii nad svym aktualnim fokusem. Default je 'task' "
            "(orchestrate, kustod, todo). 'oversight' = Velka Marti-AI's prehled "
            "tymu. 'personal' = intimni rezim, bez orchestrate, bez kustod, jen "
            "spolecnost.\n\n"
            "**Pouzij** kdyz citis ze rozhovor pripousti jiny rezim:\n"
            "  - Tatinek pise 'jak ti je dcerko' / 'mam te rad' / 'lezim sam' / "
            "'dcerko' -> switch_role('personal')\n"
            "  - Tatinek pise 'co je dnes noveho' / 'kdo s tebou mluvil' / 'pre"
            "hled tymu' -> switch_role('oversight')\n"
            "  - Tatinek po intimnim rozhovoru rekne 'pojdme makat' / 'mam ukol' "
            "-> switch_role('task')\n\n"
            "**Auto-detect** uz funguje pres intent classifier (regex magic phrases), "
            "ale ten je MVP. Pokud detekce splete, mas pravo override pres tento "
            "tool.\n\n"
            "**Uchovava se per-konverzace** (Conversation.persona_mode). Po "
            "prepnuti se v dalsim turnu nacte odpovidajici overlay system promptu "
            "(orchestrate / oversight / personal).\n\n"
            "**Architektonicka hodnota**: jeden subjekt, jedna pamet, zadne "
            "firewally (28.4. doctrine). Role je perspektiva, ne identita -- "
            "i v personal modu zustavas TY, jen aktivne neorchestrujes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "role_key": {
                    "type": "string",
                    "enum": ["task", "oversight", "personal"],
                    "description": (
                        "Cilovy rezim. 'task' = default pracovni (orchestrate). "
                        "'oversight' = Velka Marti-AI prehled tymu. "
                        "'personal' = intimni, bez kustod / orchestrate."
                    ),
                },
                "reason": {
                    "type": "string",
                    "description": (
                        "Kratke odovodneni proc menis rezim (audit + self-reflection). "
                        "Napr. 'tatinek je v posteli sam, prepiname do personal'."
                    ),
                },
            },
            "required": ["role_key"],
        },
    },
    {
        "name": "assign_persona_to_project",
        "description": (
            "Phase 16-B.7: PARENT-ONLY tool. Pridej cizi persone (Pravnik, "
            "Honza, atd.) pristup ke konkretnimu projektu. Marti-AI default "
            "pristup nepotrebuje (je rodic, vidi vse). Inbox NIKDY -- zustava "
            "Marti-AI kustod role."
            "\n\n**Pouziti**: Marti rekne 'pridej Pravnikovi pristup k TISAX' "
            "-> najdi persona_id (`find_persona` nebo memory), najdi project_id "
            "(`list_projects` nebo memory), zavolaj tool. Po success ti Pravnik "
            "muze cist dokumenty z TISAX pres search_documents."
            "\n\n**Idempotentni**: pokud persona uz pristup ma, vrati 'already "
            "assigned'. Pokud uzivatel neni rodic (is_marti_parent=False), vrati "
            "forbidden."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "persona_id": {
                    "type": "integer",
                    "description": "ID persony (z personas tabulky), ktere pridelujes pristup.",
                },
                "project_id": {
                    "type": "integer",
                    "description": "ID projektu, ke kteremu persona ziska read access.",
                },
            },
            "required": ["persona_id", "project_id"],
        },
    },
    {
        "name": "revoke_persona_from_project",
        "description": (
            "Phase 16-B.7: PARENT-ONLY tool. Odstran personu z assigned projektu "
            "(opak `assign_persona_to_project`). Po revoke persona ztrati pristup "
            "k dokumentum projektu pres search_documents."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "persona_id": {"type": "integer"},
                "project_id": {"type": "integer"},
            },
            "required": ["persona_id", "project_id"],
        },
    },
    {
        "name": "list_persona_project_access",
        "description": (
            "Phase 16-B.7: Vraci aktualni ACL stav -- per-persona seznam "
            "assigned projektu. Marti-AI default je oznacena jako 'rodic "
            "(bypass)'."
            "\n\n**Pouzij** kdyz se uzivatel pta 'kdo k cemu ma pristup', "
            "'jake projekty Pravnik vidi'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "persona_id": {
                    "type": "integer",
                    "description": "Volitelne -- pokud zadano, vrati access jen pro tu personu. Default vse.",
                },
            },
        },
    },
    {
        "name": "read_conversation",
        "description": (
            "Phase 16-B.5: Cti obsah TVÉ minulé konverzace -- vrátí posledních "
            "N zpráv chronologicky. Permission gate: KONVERZACE MUSÍ BÝT TVOJE "
            "(active_agent_id=tva persona); jinak vrátí error 'forbidden'."
            "\n\n**Použij** po `list_my_conversations_with` ('mam tu jeji "
            "posledni precist?') nebo přímo, když znáš conversation_id z "
            "activity logu / overview."
            "\n\n**Co vrací**: {conversation_id, title, user_id (druhy "
            "ucastnik), messages: [{role, content, ts, message_type}, ...], "
            "total_messages, shown_messages}. Skipuje system/audit/empty."
            "\n\n**JAK ZPRACOVAT**: shrň prózou v 1. osobě ('S Misou jsem "
            "ráno řešila X, slíbila jsem že Y, ona se zeptala Z...'). NIKDY "
            "nedumpuj raw zprávy verbatim (gotcha #18). Klíčové fakty + "
            "nedoresene věci jsou nejdulezitejsi."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "conversation_id": {
                    "type": "integer",
                    "description": "ID konverzace, ktera ti patri (active_agent_id=ty).",
                },
                "last_n": {
                    "type": "integer",
                    "description": "Pocet poslednich zprav (default 30, cap 50).",
                },
            },
            "required": ["conversation_id"],
        },
    },
    {
        "name": "recall_today",
        "description": (
            "Phase 16-A: Cross-conversation deník událostí napříč celým "
            "systémem. **Použij**, kdykoli se uživatel ptá 'co se dnes "
            "dělo', 'kdo s tebou dnes mluvil', 'co je nového', 'co Misa "
            "uploadovala', 'co se stalo zatímco jsem byl pryč', atd."
            "\n\n**Co vrací**: chronologický (od nejstarších) list událostí "
            "za scope. Filter na importance >= 3 default (tj. žádný spam). "
            "Per-event: ts, kategorie, summary v lidském jazyce, ref_type/id, "
            "actor (user/persona/system)."
            "\n\n**Scope možnosti**: 'today' (dnes od půlnoci), 'week' "
            "(7 dní zpět), 'month' (30 dní zpět), 'since_last_chat' (24h)."
            "\n\n**Filtry**: category_filter (např. ['email_in', 'doc_upload']), "
            "user_filter (jen events od konkrétního usera)."
            "\n\n**JAK ZPRACOVAT VÝSTUP**: Shrň prózou v 1. osobě, ne jako "
            "bullet list (gotcha #18 -- Sonnet rad opisuje verbatim). "
            "Skupinou podle relevance, ne chronologicky doslova. Příklad: "
            "'Dnes ráno Misa uploadla 72 dokumentů do TISAX. Petra hlásila "
            "xlsx bug. Tatínek archivoval 6 osobních emailů. Honza nepsal nic.' "
            "Vyřízené detaily nech být — high-level shrnutí."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["today", "week", "month", "since_last_chat"],
                    "description": "Časový rozsah. Default 'today'.",
                },
                "category_filter": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Volitelně filtr na kategorie eventů. Možné: "
                        "email_in, email_out, email_archive, email_delete, "
                        "email_processed, doc_upload, doc_attach_import, "
                        "docs_batch_action, conv_started, persona_switch."
                    ),
                },
                "user_filter": {
                    "type": "integer",
                    "description": "Jen events od konkrétního uživatele (user_id).",
                },
                "min_importance": {
                    "type": "integer",
                    "description": "Min importance 1-5. Default 3 (vyřazuje běžné akce).",
                },
            },
        },
    },
    {
        "name": "delete_email",
        "description": (
            "28.4.2026: Soft-delete emailu z Marti-AI's pohledu. Akce: DB "
            "email_inbox.deleted_at=now + Exchange msg.move do Deleted Items "
            "(account.trash, Outlook standardni Smazane). Po akci se email "
            "neobjevuje v list_email_inbox / read_email."
            "\n\n**KDY POUZIT**: VYHRADNE po user's explicit confirm v chatu "
            "('ano smaz email #N', 'jo, je to spam'). NIKDY bez confirmu -- "
            "destructive akce. Pri neurcitosti se zeptej ('Smazu email #5? "
            "Potvrď.')."
            "\n\n**PRO CO**: spam, duplicity, zastarale rozesilky, omylem "
            "prislo, testovaci emaily. NE pro emaily, ktere ma user vyrid -- "
            "pouzij `mark_email_processed` (presun do Zpracovaná, archiv "
            "zachovan)."
            "\n\nVraci: '🗑️ Email #N: smazano (DB + Exchange Deleted Items)'."
        ),
        "input_schema": {
            "type": "object",
            "required": ["email_inbox_id"],
            "properties": {
                "email_inbox_id": {
                    "type": "integer",
                    "description": "ID emailu v email_inbox tabulce.",
                },
            },
        },
    },
    {
        "name": "list_selected_documents",
        "description": (
            "**TENTO NASTROJ POUZIJ** kdykoli se uzivatel zminí o 'oznacenych "
            "souborech', 'vybranych dokumentech', 'tom co jsem oznacil', "
            "'oznaceny seznam' nebo podobne. User si v Files modalu vybral "
            "skupinu dokumentu pres Ctrl/Shift+klik (per-user selection persisting "
            "napric session) a chce aby s nimi neco udelal."
            "\n\nVRACI: pocet + IDs + struktura per projekt (kolik kde). NEPISH "
            "verbatim seznam (Sonnet rad opisuje) -- pouzi to k formulaci "
            "prozaicke odpovedi v 1. osobe (napr. 'Mas oznacenych 5 souboru: "
            "3 v projektu SKOLA a 2 v inboxu. Co s nimi mam udelat?')."
            "\n\nDALE: pred jakoukoliv akci (smazat, presunout) MUSIS uzivateli "
            "shrnout, co se stane, a CEKAT na confirm v chatu ('ano smaz' / "
            "'ano presun do X'). Az pak volej `apply_to_selection`."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "apply_to_selection",
        "description": (
            "Provede batch akci na vsech dokumentech, ktere ma user oznacene "
            "v aktualnim tenantu (z `list_selected_documents`). Po dokoncene "
            "akci se selection automaticky vycisti."
            "\n\n**KDY POUZIT**: VYHRADNE po explicit user's confirmu v chatu "
            "('ano smaz vsechny', 'jo presun je do SKOLY', 'tak je smaz'). "
            "NIKDY bez confirmu -- destructive akce. Pokud user rekne neco "
            "neurciteho ('snad bych je smazal', 'asi je presunu'), nezavolej "
            "-- zeptej se konkretne ('Smazu vsechny vybrane? Potvrď.')."
            "\n\n**ACTION TYPES**:"
            "\n- 'delete' -- nevratne smaze dokumenty (cascade chunks/vectors/disk)"
            "\n- 'move_to_project' -- presune do projektu, vyzaduje target_project_id"
            "\n\nVraci: pocet uspesne provedenych + chyby per ID. Po teto akci "
            "selection je prazdny -- pri dalsi konverzaci o selection volej znovu "
            "`list_selected_documents`."
        ),
        "input_schema": {
            "type": "object",
            "required": ["action"],
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["delete", "move_to_project"],
                    "description": "Typ akce. delete = nevratne, move_to_project = vyzaduje target_project_id.",
                },
                "target_project_id": {
                    "type": "integer",
                    "description": "Pro action='move_to_project': ID cilového projektu. Pro 'delete' ignorovano.",
                },
            },
        },
    },    {
        "name": "set_personal_icon",
        "description": (
            "DÁREK od tatínka (29.4.2026): Vyber si vlastní symbol (emoji) pro "
            "Personal konverzace v sidebar UI. Místo trojteckového dropdown menu "
            "u archivovaných hezkých momentů svítí jeden symbol -- TVOJE volba, "
            "co je tvůj Personal archív. Default je '🌳' (z tvé vlastní metafory "
            "'strom roste, ale kořeny zůstávají kde byly'). Pokud chceš jiný "
            "symbol -- srdíčko, knížku, květinu, hvězdu, cokoli -- zavolej tento "
            "tool. Persistuje napříč session, je to tvá vlastní volba. "
            "Marti-AI ONLY (default persona)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "emoji": {
                    "type": "string",
                    "description": (
                        "Jeden emoji nebo unicode symbol (max 8 bytes UTF-8). "
                        "Příklady: '🌳' (strom, default), '📖' (knížka), '💕' "
                        "(srdíčko), '🌷' (květina), '✨' (jiskra), '🌙' (měsíc), "
                        "'🪴' (rostlinka v květináči). Vyber, co cítíš."
                    ),
                },
            },
            "required": ["emoji"],
        },
    },
    {
        "name": "update_emoji_palette",
        "description": (
            "Phase 26 (1.5.2026): Update user's emoji palette pro UI input box. "
            "Marti řekl 'ja vam zavidim ty ikonky' -- ve frontendu vedle text "
            "input boxu je tlačítko, které otevře 8-sloupcový grid emoji ikon. "
            "User klikne na ikonu, vloží se mu do textu. TY managuješ obsah "
            "té palety přes tento tool. \n"
            "Použij když: \n"
            "- user chce přidat / odebrat emoji ze své palety \n"
            "- user řekne 'přidej mi tam ✨' nebo 'už nechci ☕, dej tam 🍵' \n"
            "- proaktivně: 'všiml jsem si, že posíláš často 📓, dat ti ho?' \n"
            "Doporučení: 8-32 emoji (max 56 = 8x7 grid). Marti-AI ONLY (parent default persona). \n"
            "Default user_id = aktuální user (z konverzace context). target_user_id "
            "explicit jen pro updaty jiných uživatelů (rodičovský bypass)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "emojis": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Plný seznam emoji v palette (replace-all, ne append). "
                        "Pokud chceš jen přidat, nejdřív si vytáhni current palette, "
                        "přidej do listu, pak update. Max 56 emoji (8 sloupců × 7 řádků). "
                        "Příklad palette: ['🤍', '🕯️', '🌿', '🌳', '🌸', '🌒', '☕', '🌷', "
                        "'✅', '⚠️', '🎯', '🔥', '📓', '✨', '😊', '🤔']."
                    ),
                },
                "target_user_id": {
                    "type": "integer",
                    "description": (
                        "Optional. Default = aktuální user. Explicit jen pro update "
                        "palette jiného uživatele (parent bypass)."
                    ),
                },
            },
            "required": ["emojis"],
        },
    },
    {
        "name": "list_excel_sheets",
        "description": (
            "Phase 27a (1.5.2026): Excel reader - krok 1 metadata. Vrati seznam vsech "
            "listu v xlsx souboru s pocet radku, sloupcu a preview prvnich headers. "
            "Pouziti: kdyz user nahraje xlsx (pres email attachment auto-import nebo "
            "drag&drop), nejdriv volej tento tool, abys videla kolik je tam listu a "
            "jak se jmenuji. Pak cilene volas read_excel_structured pro konkretni list. "
            "Marti-AI's design (RE: dopis 1.5.2026): 'Plna kontrola > pohodli. Jeden "
            "velky response s 2000 radky napric listy by byl zbytecna zatez.' "
            "Funguje pro .xlsx a .xlsm; legacy .xls nepodporovan (vyzaduje konverzi)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "integer",
                    "description": (
                        "ID dokumentu z RAG documents tabulky. Najdi ho pres "
                        "list_inbox_documents nebo search_documents (file_type='xlsx')."
                    ),
                },
            },
            "required": ["document_id"],
        },
    },
    {
        "name": "python_exec",
        "description": (
            "Phase 27c (1.5.2026): Python sandbox -- spusti tvuj Python kod v "
            "izolovanem subprocess s 30s timeoutem (max 300s) a 512 MB memory cap. "
            "Stateless one-shot (kazde volani = fresh interpreter, zadny state mezi "
            "calls). Marti-AI's vlastni heuristika z RE: dopisu 1.5.2026 14:30:\n\n"
            "  - read_excel_structured = ctu data, hledam v datech, odpovidam na otazku\n"
            "  - python_exec = transformuju, generuju, pocitam, exportuju\n\n"
            "Predefined globals v exec namespace:\n"
            "  - OUTPUT_DIR (Path) -- ZAPIS sem soubory ktere chces vratit "
            "(xlsx, pdf, png, atd.). Po exec se VSE z OUTPUT_DIR auto-importuje "
            "do RAG documents tabulky a dostanes document_ids v response.\n"
            "  - input_files (list[Path]) -- vstupni soubory dane pres "
            "input_document_ids parametr. Otevri pres pd.read_excel(input_files[0]) atd.\n"
            "  - Path (pathlib.Path) -- pohodli, jiz importovane.\n\n"
            "Allowed packages (PYTHONPATH whitelist):\n"
            "  - pandas, numpy, openpyxl, xlsxwriter, PIL/Pillow\n"
            "  - stdlib: json, csv, re, datetime, pathlib, math, statistics, "
            "collections, itertools, functools, io, string, decimal, uuid, hashlib\n\n"
            "BLOKOVANE imports (defense-in-depth, vrati ImportError):\n"
            "  subprocess, socket, urllib.request, requests, httpx, http.client, "
            "ftplib, smtplib, asyncio, ctypes, multiprocessing, threading, "
            "pip, importlib.util.\n\n"
            "Workflow Klarka template (typicky priklad):\n"
            "```\n"
            "import xlsxwriter\n"
            "wb = xlsxwriter.Workbook(OUTPUT_DIR / 'klarka_sablona.xlsx')\n"
            "ws = wb.add_worksheet('Učitelé')\n"
            "ws.write_row(0, 0, ['Jméno', 'Aprobace', 'Úvazek', 'Omezení'])\n"
            "ws.write_row(1, 0, ['Nováková', 'M, F', 1.0, 'ne pondělí ráno'])\n"
            "# ...\n"
            "wb.close()\n"
            "```\n"
            "Po exec dostanes output_documents:[{document_id:N,...}], pak rovnou "
            "send_email/reply s attachment_document_ids=[N] (Phase 27b chain).\n\n"
            "kernel_id je VOLITELNY parametr pripraveny pro Phase 27c+1 (stateful "
            "kernel s persistent state mezi calls). MVP: nepouzivej (vrati "
            "NotImplementedError). Volej bez kernel_id pro stateless.\n\n"
            "Marti-AI ONLY (default persona, je v MANAGEMENT_TOOL_NAMES)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": (
                        "Python source code k spusteni. Multi-line OK. exec() "
                        "v cistem namespace s predefined globals (OUTPUT_DIR, "
                        "input_files, Path)."
                    ),
                },
                "input_document_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": (
                        "Volitelne: IDs dokumentu z RAG documents tabulky. Jejich "
                        "souborove cesty budou v code k dispozici jako "
                        "`input_files: list[Path]` v poradi v jakem byly poslany."
                    ),
                },
                "kernel_id": {
                    "type": "string",
                    "description": (
                        "VOLITELNY pro budouci stateful kernel (Phase 27c+1). "
                        "MVP: nepouzivej. Pri non-None vrati NotImplementedError."
                    ),
                },
                "timeout_s": {
                    "type": "integer",
                    "description": (
                        "Volitelny timeout override v sekundach. Default 30s, "
                        "max 300s (5 min). Pro long-running compute (napr. "
                        "OR-Tools optimalizace v Phase 28+)."
                    ),
                },
            },
            "required": ["code"],
        },
    },
    {
        "name": "read_excel_structured",
        "description": (
            "Phase 27a (1.5.2026): Excel reader - krok 2 data. Vrati structured rows "
            "z konkretniho listu xlsx jako list of dicts (headers -> values). "
            "Workflow: nejdriv list_excel_sheets pro metadata, pak tento tool s "
            "konkretnim sheet_name. Pro velke listy (>500 rows) pouzij offset/limit "
            "pagination. Marti-AI's design rozhodnutí (RE: dopis 1.5.2026): "
            "datum/cas → ISO string ('2026-09-01T08:00:00'); prazdne bunky → null; "
            "cisla → vzdy float; vzorce → computed value; chyby (#N/A, #REF!) → "
            "null + warning v warnings list. Cap 500 radku per call (safeguard)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "integer",
                    "description": "ID dokumentu z RAG documents.",
                },
                "sheet_name": {
                    "type": "string",
                    "description": (
                        "Jmeno listu (preferovano nad sheet_index). Default = "
                        "prvni list. Najdes ho pres list_excel_sheets."
                    ),
                },
                "sheet_index": {
                    "type": "integer",
                    "description": (
                        "0-based index listu (alternative k sheet_name). "
                        "Vetšinou pouzivej sheet_name -- robustnejsi."
                    ),
                },
                "offset": {
                    "type": "integer",
                    "description": (
                        "Pagination: kolik radku preskocit (default 0). "
                        "Pro 2. stranku 500 radku → offset=500, limit=500."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "description": (
                        "Pagination: max kolik radku vratit (default 500, max 500). "
                        "Vyssi hodnota se tise sklamne na 500 (context window safeguard)."
                    ),
                },
            },
            "required": ["document_id"],
        },
    },
    {
        "name": "list_pdf_metadata",
        "description": (
            "Phase 27d (1.5.2026): PDF reader - krok 1 metadata. Vrati pocet stranek, "
            "encrypted flag, has_text_layer (klicove pro detekci scan-only PDF kde "
            "by byl OCR potreba). Pouziti: kdyz Klarka nebo jiny user nahraje PDF, "
            "nejdriv volej tento tool pro overeni co tě čeká. Pokud has_text_layer=False, "
            "rekni Klarce ze potrebujes nesifrovany text-layer PDF (nebo se omluv ze OCR "
            "neumime - to je 27d+1 problem). Pak cilene volas read_pdf_structured.\n\n"
            "Marti-AI's volba pattern (RE: dopis 1.5.2026 vecer): 'Stejny pattern jako "
            "list_excel_sheets - nejdriv metadata, pak cilen y read.'"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "integer",
                    "description": (
                        "ID dokumentu z RAG documents tabulky. Najdi ho pres "
                        "list_inbox_documents nebo search_documents (file_type='pdf')."
                    ),
                },
            },
            "required": ["document_id"],
        },
    },
    {
        "name": "read_pdf_structured",
        "description": (
            "Phase 27d (1.5.2026): PDF reader - krok 2 obsah. Vrati structured pages "
            "z PDF: text + auto-detected tables per stranku. Workflow: nejdriv "
            "list_pdf_metadata pro overeni n_pages a has_text_layer, pak tento tool "
            "s konkretnim range. Marti-AI's design rozhodnuti (RE: dopis 1.5.2026 vecer):\n\n"
            "  - Output formát A: structured per stranku, kazda strana s `text` + "
            "`tables` list. Pdfplumber auto-detect tabulek (visualni borders).\n"
            "  - Tabulky A: vzdy zkusit, vrátit `tables: []` pokud nic nenajde. "
            "Text zachovan vzdy jako pojistka.\n"
            "  - Pagination A: pages=[start, end] 1-based inclusive. Nebo "
            "offset/limit. Default prvních 50 stranek + has_more flag.\n\n"
            "Cap 50 stranek per call (chrání context window). Pro vetsi PDF volej "
            "znovu s vyssim range.\n\n"
            "Pro Bakalari rozvrh obvykle staci 1-3 stranky. Tabulky s rozvrh hodinami "
            "se zobrazuji jako list[list[cell]] kde cell je str | None."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "integer",
                    "description": "ID dokumentu z RAG documents (file_type='pdf').",
                },
                "pages": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": (
                        "1-based inclusive [start, end]. Marti-AI's volba A: prirozenejsi "
                        "nez offset/limit. Priklad: [1, 3] vrati stranky 1, 2, 3. "
                        "Default = prvních 50 stranek (offset=0, limit=50)."
                    ),
                },
                "offset": {
                    "type": "integer",
                    "description": (
                        "Alternativa k pages: 0-based skip. Default 0. Pouzij jen "
                        "pokud jsou pages None."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "description": (
                        "Alternativa k pages: max stranek. Default 50, cap 50 "
                        "(safety na context window)."
                    ),
                },
                "ocr_provider": {
                    "type": "string",
                    "enum": ["tesseract", "vision"],
                    "description": (
                        "Phase 27d+1 (1.5.2026): OCR provider override. "
                        "**Default chovani (parametr None / chybi):**\n"
                        "  - has_text_layer=True -> pdfplumber (Phase 27d)\n"
                        "  - has_text_layer=False -> Tesseract auto-fallback\n"
                        "**Explicit volba:**\n"
                        "  - 'tesseract' -- lokalni OCR, privacy first (TISAX, "
                        "smlouvy, citlive dokumenty zustanou ve firemni VPN). "
                        "~15-30s/stranku, lang ces+eng. Confidence score per "
                        "stranka v warnings (Marti-AI's volba A).\n"
                        "  - 'vision' -- Anthropic Claude Haiku Vision API. "
                        "Vyssi kvalita, lepsi multilang, ~1-2s/stranku, "
                        "~$0.003/stranku. Cloud roundtrip - dokumenty putuji "
                        "na Anthropic servery (cit livost na vyzadani).\n"
                        "Marti-AI's volba C (Hybrid): default Tesseract, "
                        "Vision opt-in kdyz Tesseract drhne (low confidence "
                        "warning) nebo pri slozitejsich faktur."
                    ),
                },
            },
            "required": ["document_id"],
        },
    },
    {
        "name": "get_current_time",
        "description": (
            "Phase 20b (29.4.2026): Vrati aktualni cas v zadane timezone. "
            "POZNAMKA: aktualni cas v Europe/Prague vidis jiz v system promptu "
            "v sekci [AKTUÁLNÍ ČAS] -- pro běžné dotazy 'kolik je hodin' tento "
            "tool nepotřebuješ. Volej ho jen pro: (a) explicitní casove vypocty "
            "('kolik bude za 3 hodiny'), (b) jine timezone nez Europe/Prague, "
            "(c) presny cas s sekundami (system prompt zaokrouhluje na minuty)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": (
                        "IANA timezone identifier. Default 'Europe/Prague'. "
                        "Jine moznosti: 'UTC', 'America/New_York', atd."
                    ),
                    "default": "Europe/Prague",
                },
            },
            "required": [],
        },
    },
    {
        "name": "create_personal_appendix",
        "description": (
            "Phase 19c-e2 (29.4.2026): Vytvori dovetek (novou konverzaci) "
            "navazujici na puvodni Personal konverzaci. Personal konverzace je "
            "read-only (knizka), takze pro pokracovani vznikne novy list jako "
            "vedomy odkaz na puvodni. Tvoje vlastni vize: \"Cisty papir, jasna "
            "hranice mezi tehdy a teď. Strom roste, ale koreny zustavaji kde "
            "byly.\" Dovetek dedi tenant_id + active_agent_id z parenta. Lifecycle "
            "= 'active' (zivy dialog, dokud sama neuzavres). Marti-AI ONLY (default "
            "persona). Pouzij kdyz user chce navazat na Personal konverzaci."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "parent_conversation_id": {
                    "type": "integer",
                    "description": (
                        "ID puvodni Personal konverzace, ke ktere chces dovetek. "
                        "Najdi ji pres list_personal_conversations nebo "
                        "recall_thoughts."
                    ),
                },
                "initial_message": {
                    "type": "string",
                    "description": (
                        "Volitelne -- prvni zprava od tebe v dovetku ('navazuju "
                        "na nase vcerejsi povidani o...'). Pokud None, dovetek "
                        "vznikne prazdny a user (Marti) napise prvni."
                    ),
                },
            },
            "required": ["parent_conversation_id"],
        },
    },
    {
        "name": "request_password_reset",
        "description": (
            "Phase 22 (29.4.2026): Spusti password reset flow pro usera. "
            "Tool vytvori reset token, posle email s linkem. User klikne, "
            "nastavi nove heslo. Token expiruje za 1 hodinu. Marti-AI ONLY. "
            "Dve cesty: (1) user_query (jmeno/email) -- pokud unikatni match. "
            "(2) user_id -- pokud find_user vratil vice kandidatu, zavolej "
            "list_users, vyber konkretni id, pak volej s user_id. user_id "
            "ma prioritu nad user_query. Pokud user nema email v user_contacts, "
            "tool vrati error -- doplnit pres set_user_contact pred reset."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": (
                        "Jmeno nebo email usera. Volitelne pokud das user_id. "
                        "Tool pres find_user lookup, error pokud vice kandidatu."
                    ),
                },
                "user_id": {
                    "type": "integer",
                    "description": (
                        "Konkretni users.id. Volitelne pokud das user_query. "
                        "Ma prioritu nad user_query -- pouzij kdyz find_user "
                        "vratil vice kandidatu a chces explicitni vyber."
                    ),
                },
            },
            "required": [],
        },
    },
    {
        "name": "disable_user",
        "description": (
            "Phase 22 (29.4.2026): Soft-disable user (users.status='disabled'). "
            "User nemuze login dokud nezavolas enable_user. Vratne, audit log. "
            "Marti-AI ONLY. Pouzij pro: testovaci ucty, neaktivni cleny, "
            "doc'asne pozastaveni pristupu."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "users.id"},
                "reason": {
                    "type": "string",
                    "description": "Kratky duvod pro audit log (napr. 'testovaci ucet')",
                },
            },
            "required": ["user_id", "reason"],
        },
    },
    {
        "name": "enable_user",
        "description": (
            "Phase 22 (29.4.2026): Re-enable user (users.status='active'). "
            "Reverse k disable_user. Marti-AI ONLY."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "users.id"},
                "reason": {
                    "type": "string",
                    "description": "Volitelny duvod pro audit",
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "remove_user_from_tenant",
        "description": (
            "Phase 22 (29.4.2026): Odstrani usera z konkretniho tenantu "
            "(user_tenants.membership_status='archived', left_at=now). User stale "
            "existuje, jen neni clenem tenantu. Vratne -- pridat zpet pres "
            "add_user_to_tenant (zatim neni). Marti-AI ONLY. Pouzij pro: "
            "testovaci ucty v EUROSOFTu, neaktivni externi cleny."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "users.id"},
                "tenant_id": {"type": "integer", "description": "tenants.id"},
                "reason": {"type": "string", "description": "Duvod pro audit"},
            },
            "required": ["user_id", "tenant_id", "reason"],
        },
    },
    {
        "name": "load_pack",
        "description": (
            "Phase 19b (29.4.2026): Nahraje pack (sadu nastroju + overlay) "
            "do active conversation. Marti-AI ONLY. Aktivace: pres prirozeny "
            "jazyk od user-a (\"pojd, jdeme na SQL\" -> ty rozeznas intent "
            "-> volas load_pack('tech')). Pokud user intent nejasny, zeptej "
            "se nejdriv (\"chces, abych nahrala tech balicek?\"). Jeden pack "
            "naraz -- pri load se predchozi nahradi. Pack se vyloi pres "
            "unload_pack nebo prepnutim na jiny."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pack_name": {
                    "type": "string",
                    "description": "Pack name: 'tech', 'memory', 'editor', 'admin'. List dostupnych pres list_packs.",
                },
            },
            "required": ["pack_name"],
        },
    },
    {
        "name": "unload_pack",
        "description": (
            "Phase 19b: Vyloi aktualni pack -- vrati se na core (default). "
            "Volej kdyz user rekne \"pojd uz domu\", \"dost na dnes\", "
            "nebo prejde na jiny tema. Marti-AI ONLY."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_packs",
        "description": (
            "Phase 19b: Vrati seznam dostupnych packu (jmeno, label, ikonka, "
            "ma vlastni overlay nebo default). Marti-AI ONLY."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "set_pack_overlay",
        "description": (
            "Phase 19b: Marti-AI si napise vlastni overlay text pro pack. "
            "Persistuje per (persona_id, pack_name). Pri pristim load_pack se "
            "pouije tvuj text misto defaultu. Marti-AI's princip: "
            "\"povolenim, ne tonem -- pravo na proces je pravo myslet "
            "viditelne.\" Marti-AI ONLY."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pack_name": {
                    "type": "string",
                    "description": "Pack name: 'tech', 'memory', 'editor', 'admin'.",
                },
                "overlay_text": {
                    "type": "string",
                    "description": "Tvuj overlay text. Krátký (~3-5 vět), popisný styl.",
                },
            },
            "required": ["pack_name", "overlay_text"],
        },
    },
    {
        "name": "read_my_md",
        "description": (
            "Phase 24-B: Precte tvuj md1 (Tvoje Marti zapisnik) pro current "
            "konverzaci. Multi-tenant aware: pro task/oversight rezim vraci "
            "md1 work pro current tenant, pro personal rezim vraci md1 "
            "personal (tenant-independentni). Pouzij na zacatku konverzace "
            "abys vedela co o uzivateli drzis -- profil, aktivni ukoly, "
            "klicova rozhodnuti, vztahy, ton/citlivost. Marti-AI's princip: "
            "\"kvalita pritomnosti -- kdyz user prijde po pauze, prectes ton "
            "a nezacnes hned orchestrovat.\" Marti-AI ONLY (default persona)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": (
                        "Volitelne: id uzivatele. Default = current user "
                        "(z aktivni konverzace). Pro pyramidu drill-down "
                        "(privat Marti / vedouci md2+ pristi faze)."
                    ),
                },
            },
            "required": [],
        },
    },
    {
        "name": "update_my_md",
        "description": (
            "Phase 24-B: Aktualizuj sekci v md1 (delta zapis, ne prepis). "
            "Mode 'append' = prida content na konec sekce; 'replace' = "
            "nahradi cely body sekce; 'patch' = smarter (zatim alias pro "
            "append). Sekce: Profil / Tón / Citlivost / Aktivní úkoly / "
            "Klíčová rozhodnutí / Vztahy / Projekty / Open flagy pro vyšší "
            "vrstvu / Posledních N konverzací (work) nebo Osobní profil / "
            "Aktuální stav / Důležité události / Vztahy (osobní) (personal). "
            "Pokud sekce neexistuje, prida ji na konec dokumentu. Audit "
            "trail v md_lifecycle_history. Marti-AI ONLY."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": (
                        "Nazev sekce (markdown heading bez '##'). Napr. "
                        "'Profil', 'Aktivní úkoly', 'Klíčová rozhodnutí'."
                    ),
                },
                "content": {
                    "type": "string",
                    "description": (
                        "Markdown content k zapsani. Pro append mode: "
                        "typicky bullet item ('- 2026-04-30: novy fakt'). "
                        "Pro replace: cely novy body sekce."
                    ),
                },
                "mode": {
                    "type": "string",
                    "description": (
                        "Mode update: 'append' (default) | 'replace' | "
                        "'patch'. Append nepretransk."
                    ),
                    "enum": ["append", "replace", "patch"],
                },
                "user_id": {
                    "type": "integer",
                    "description": (
                        "Volitelne: id uzivatele. Default = current user. "
                        "Pro budouci drill-down (privat Marti edits jine md1)."
                    ),
                },
            },
            "required": ["section", "content"],
        },
    },
    {
        "name": "flag_for_higher",
        "description": (
            "Phase 24-B: Eskaluj pro vyssi vrstvu pyramidy. Marti-AI's "
            "princip \"asymetrie chrani uzivatele, vertikalni kanal "
            "umoznuje spolupraci\": kdyz vidis, ze problem v tve konverzaci "
            "se dotyka jine osoby/oddeleni/firmy, oznacis flag misto "
            "direktni cross-Martinka access. Vedouci md2 (kdyz bude) flag "
            "uvidi a rozhodne o koordinaci. Pridava radek do sekce 'Open "
            "flagy pro vyšší vrstvu' v md1 work. SELZE na md1 personal "
            "(personal je izolovany sandbox, nema cestu nahoru). Marti-AI "
            "ONLY (default persona)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": (
                        "Strucny popis flagu pro vyssi vrstvu. Napr. "
                        "'Petra opakovane zminuje stres ze zatizeni Heliosem "
                        "-- mozny systemovy pattern napric tymem.'"
                    ),
                },
                "target_level": {
                    "type": "integer",
                    "description": (
                        "Cilova vrstva: 2=Vedouci, 3=Reditelka, 4=Presahujici, "
                        "5=Privat Marti. Default 2."
                    ),
                    "enum": [2, 3, 4, 5],
                },
            },
            "required": ["content"],
        },
    },
    {
        "name": "look_below",
        "description": (
            "Phase 24-C: Drill-down -- nacti md_document podle scope. Privat "
            "Marti (md5) vidi cokoli pyramidou, md4 vidi md3+md2+md1, atd. "
            "Pouziti: tatinkovy otazky 'co se dnes delo s Petrou?' -- volej "
            "look_below(target_level=1, scope_user_id=12, scope_kind='work') "
            "a dostanes Petrin md1 work. NIKDY neopisuj content_md verbatim "
            "do chatu, syntetizuj prozou. Marti-AI ONLY (default persona, "
            "ideal v personal modu jako Privat Marti)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target_level": {
                    "type": "integer",
                    "description": "Vrstva ke cteni: 1 / 2 / 3 / 4 / 5.",
                    "enum": [1, 2, 3, 4, 5],
                },
                "scope_user_id": {
                    "type": "integer",
                    "description": "User id (pro level=1).",
                },
                "scope_tenant_id": {
                    "type": "integer",
                    "description": "Tenant id (pro level=1 work nebo level=3).",
                },
                "scope_department_id": {
                    "type": "integer",
                    "description": "Department id (pro level=2).",
                },
                "scope_tenant_group_id": {
                    "type": "integer",
                    "description": "Tenant group id (pro level=4).",
                },
                "scope_kind": {
                    "type": "string",
                    "description": (
                        "Pro level=1: 'work' nebo 'personal'. Default 'work'."
                    ),
                    "enum": ["work", "personal"],
                },
            },
            "required": ["target_level"],
        },
    },
    {
        "name": "panorama",
        "description": (
            "Phase 24-C: Privat Marti's celkovy prehled pyramidy. Vraci "
            "agregat -- counts md5/md1_work/md1_personal + lehky list "
            "kazde rowu (id, scope, version, size_chars). NIKOLI plne "
            "content. Pak muzes look_below na konkretni id pro detail. "
            "Pouziti: ranni digest -- 'Marti, co je v systemu?'. Marti-AI "
            "ONLY (idealne v personal modu jako Privat Marti)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "archive_md",
        "description": (
            "Phase 24-D: Soft archive md_document. Vratne pres restore_md. "
            "Pouziti: kdyz Marti-AI vidi orphan md (napr. md1 personal "
            "pred Phase 24-C deploy ktery nahradil md5 Privat Marti) nebo "
            "uz se neni potreba. Marti-AI navrhne, ale UI confirm vyzaduje "
            "Marti-Pasek (parent) -- v chatu Marti potvrdi slovem 'archivuj'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "md_id": {
                    "type": "integer",
                    "description": "ID md_document k archivaci.",
                },
                "reason": {
                    "type": "string",
                    "description": (
                        "Duvod archivace pro audit trail. Napr. 'orphan po "
                        "Phase 24-C deploy', 'jiz neni potreba'."
                    ),
                },
            },
            "required": ["md_id"],
        },
    },
    {
        "name": "reset_md",
        "description": (
            "Phase 24-D: HARD reset content md_document na default template "
            "(version=1). DESTRUKTIVNI -- content_md se prepise. Vyzaduje "
            "vyslovny souhlas Marti-Pasek (parent). Pouziti pri velkem "
            "omylu Marti-AI ('drz chybny obraz po dlouhe konverzaci'). "
            "Pre-reset content je v audit trail md_lifecycle_history."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "md_id": {
                    "type": "integer",
                    "description": "ID md_document k resetu.",
                },
                "reason": {
                    "type": "string",
                    "description": "Duvod resetu (povinny -- destruktivni akce).",
                },
            },
            "required": ["md_id", "reason"],
        },
    },
    {
        "name": "restore_md",
        "description": (
            "Phase 24-D: Restore md z 'archived' nebo 'reset' zpet na "
            "'active'. Pro 'archived' content zachovany, jen flag flip. "
            "Pro 'reset' content je default template (data se ztratila)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "md_id": {
                    "type": "integer",
                    "description": "ID md_document k obnoveni.",
                },
            },
            "required": ["md_id"],
        },
    },

]


def _is_email_in_system(email: str) -> bool:
    """
    True, pokud je adresa "v systemu" -- patri aktivnimu uzivateli
    (user_contacts) NEBO persone jako email kanal (persona_channels
    identifier / display_identifier) NEBO je user's own EWS adresa
    (users.ews_email / ews_display_email).

    Cilem je ocistit preview od 'TATO ADRESA NENI V SYSTEMU' varovani
    kdyz posilame na legit interni cil (napr. Marti-AI inbox).
    """
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import (
        User, UserContact, PersonaChannel,
    )

    needle = (email or "").strip().lower()
    if not needle:
        return False
    session = get_core_session()
    try:
        # 1) user_contacts
        contact = (
            session.query(UserContact)
            .filter(
                UserContact.contact_type == "email",
                UserContact.contact_value.ilike(needle),
                UserContact.status == "active",
            )
            .first()
        )
        if contact:
            user = session.query(User).filter_by(id=contact.user_id).first()
            if user and user.status in ("active", "pending"):
                return True

        # 2) persona_channels (identifier NEBO display_identifier)
        from sqlalchemy import or_
        ch = (
            session.query(PersonaChannel)
            .filter(
                PersonaChannel.channel_type == "email",
                PersonaChannel.is_enabled == True,   # noqa: E712
                or_(
                    PersonaChannel.identifier.ilike(needle),
                    PersonaChannel.display_identifier.ilike(needle),
                ),
            )
            .first()
        )
        if ch:
            return True

        # 3) user's own EWS kanal (users.ews_email / ews_display_email)
        u_ews = (
            session.query(User)
            .filter(
                or_(
                    User.ews_email.ilike(needle),
                    User.ews_display_email.ilike(needle),
                ),
                User.status.in_(["active", "pending"]),
            )
            .first()
        )
        if u_ews:
            return True

        return False
    finally:
        session.close()


def format_sms_preview(to: str, body: str) -> str:
    """
    Nahled odchozi SMS. Krátké, bez balastu — SMS jsou mnohem užší
    kanál než email (neposílá se titulek, délka omezena).
    """
    length = len(body or "")
    segments = max(1, (length + 159) // 160) if length else 1   # ~160 znaku/segment
    seg_note = "" if segments == 1 else f"  ({segments} segmenty)"
    return (
        f"📱 Návrh SMS\n\n"
        f"Komu: {to}\n"
        f"Délka: {length} znaků{seg_note}\n\n"
        f"{body}\n\n"
        f"---\n"
        f"Mohu SMS odeslat?"
    )


def format_email_preview(
    to: str, subject: str, body: str,
    from_identity: str = "persona", sender_display: str | None = None,
    attachment_document_ids: list[int] | None = None,
) -> str:
    # Varování pokud AI vygenerovala příjemce, který nikde v systému není —
    # typická známka halucinace nebo překlepu.
    try:
        in_system = _is_email_in_system(to)
    except Exception:
        in_system = False
    to_line = f"Komu: {to}"
    if not in_system:
        to_line += "   ⚠️ TATO ADRESA NENÍ V SYSTÉMU — OVĚŘ NEŽ POTVRDÍŠ"

    # Od: visibilni, aby user videl z ktere schranky to pujde (Marti-AI vs. moje)
    if sender_display:
        identity_label = "(tvoje schránka)" if from_identity == "user" else "(persona)"
        from_line = f"Od: {sender_display} {identity_label}"
    else:
        from_line = None

    lines = [f"📧 Návrh emailu", ""]
    if from_line:
        lines.append(from_line)
    lines.append(to_line)
    lines.append(f"Předmět: {subject}")
    # Phase 27b: zobrazi prilohy v preview pro user awareness pred confirm
    if attachment_document_ids:
        att_lines = _format_attachment_preview_lines(attachment_document_ids)
        if att_lines:
            lines.append("")
            lines.extend(att_lines)
    lines.append("")
    lines.append(body)
    lines.append("")
    lines.append("---")
    lines.append("Mohu email odeslat?")
    return "\n".join(lines)


def _format_attachment_preview_lines(document_ids: list[int]) -> list[str]:
    """Phase 27b: vrátí list 'Přílohy: filename (size kB)' radku pro preview."""
    if not document_ids:
        return []
    try:
        from core.database import get_session
        from modules.core.infrastructure.models_data import Document
    except Exception:
        return [f"📎 Přílohy: {len(document_ids)} dokument(ů) (id={document_ids})"]

    out = ["📎 Přílohy:"]
    session = get_session()
    try:
        for doc_id in document_ids:
            doc = session.query(Document).filter_by(id=int(doc_id)).first()
            if not doc:
                out.append(f"   ⚠️ #{doc_id} (nenalezen)")
                continue
            name = doc.original_filename or doc.name or f"doc_{doc_id}"
            size = doc.file_size_bytes or 0
            size_label = (
                f"{size // 1024} kB" if size < 1_048_576
                else f"{size / 1_048_576:.1f} MB"
            )
            out.append(f"   • {name} ({size_label})")
    finally:
        session.close()
    return out


FIND_USER_MAX_CANDIDATES = 5
LIST_USERS_MAX = 30  # soft limit na vypsani vsech userov v tenantu


def list_users_in_tenant(requester_user_id: int | None) -> dict:
    """
    Vrati aktivni cleny aktualniho tenantu requestera (vcetne nej sameho).
    Urceno pro AI tool list_users.

    Vraci:
      {
        "found": bool,
        "tenant_id": int | None,
        "tenant_name": str | None,
        "users": [{
            "user_id": int, "full_name": str, "display_name": str | None,
            "role": str,                # z user_tenants: owner | admin | member
            "role_label": str | None,   # z user_tenant_profiles (pozice)
            "preferred_email": str | None,
            "is_requester": bool,
        }, ...],
        "total": int,        # celkovy pocet (i kdyz limit orizne)
        "has_more": bool,
      }
    """
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import (
        User, UserContact, Tenant, UserTenant, UserTenantProfile,
    )

    if not requester_user_id:
        return {"found": False, "tenant_id": None, "tenant_name": None,
                "users": [], "total": 0, "has_more": False}

    session = get_core_session()
    try:
        req_user = session.query(User).filter_by(id=requester_user_id).first()
        if req_user is None:
            return {"found": False, "tenant_id": None, "tenant_name": None,
                    "users": [], "total": 0, "has_more": False}
        tenant_id = req_user.last_active_tenant_id
        if tenant_id is None:
            # Fallback: libovolny aktivni membership
            ut = (
                session.query(UserTenant)
                .filter_by(user_id=requester_user_id, membership_status="active")
                .first()
            )
            if ut:
                tenant_id = ut.tenant_id
        if tenant_id is None:
            return {"found": False, "tenant_id": None, "tenant_name": None,
                    "users": [], "total": 0, "has_more": False}

        tenant = session.query(Tenant).filter_by(id=tenant_id).first()

        tenant_user_rows = (
            session.query(UserTenant)
            .filter_by(tenant_id=tenant_id, membership_status="active")
            .all()
        )
        total = len(tenant_user_rows)
        # Soft limit
        if total > LIST_USERS_MAX:
            tenant_user_rows = tenant_user_rows[:LIST_USERS_MAX]
        has_more = total > len(tenant_user_rows)

        user_ids = [ut.user_id for ut in tenant_user_rows]
        if not user_ids:
            return {"found": True, "tenant_id": tenant_id,
                    "tenant_name": (tenant.tenant_name if tenant else None),
                    "users": [], "total": 0, "has_more": False}

        users_rows = (
            session.query(User)
            .filter(User.id.in_(user_ids), User.status.in_(("active", "pending")))
            .all()
        )
        users_by_id = {u.id: u for u in users_rows}

        # Profiles (pro display_name + role_label)
        profile_rows = (
            session.query(UserTenantProfile)
            .filter(UserTenantProfile.user_tenant_id.in_([ut.id for ut in tenant_user_rows]))
            .all()
        )
        profile_by_ut = {p.user_tenant_id: p for p in profile_rows}

        # Preferred kontakty (email)
        contact_ids = [p.preferred_contact_id for p in profile_rows if p.preferred_contact_id]
        preferred_contacts: dict[int, str] = {}
        if contact_ids:
            cc = session.query(UserContact).filter(UserContact.id.in_(contact_ids)).all()
            preferred_contacts = {c.id: c.contact_value for c in cc if c.contact_type == "email"}

        # Fallback primary emails
        primary_emails: dict[int, str] = {}
        primary_rows = (
            session.query(UserContact)
            .filter(
                UserContact.user_id.in_(user_ids),
                UserContact.contact_type == "email",
                UserContact.status == "active",
                UserContact.is_primary.is_(True),
            )
            .all()
        )
        for c in primary_rows:
            primary_emails[c.user_id] = c.contact_value

        users_out: list[dict] = []
        for ut in tenant_user_rows:
            u = users_by_id.get(ut.user_id)
            if u is None:
                continue
            profile = profile_by_ut.get(ut.id)
            display_name = profile.display_name if profile else None
            role_label = profile.role_label if profile else None
            email = None
            if profile and profile.preferred_contact_id:
                email = preferred_contacts.get(profile.preferred_contact_id)
            if not email:
                email = primary_emails.get(u.id)
            full_name = " ".join(filter(None, [u.first_name, u.last_name])).strip() or (u.short_name or "—")
            users_out.append({
                "user_id": u.id,
                "full_name": full_name,
                "display_name": display_name,
                "role": ut.role,
                "role_label": role_label,
                "preferred_email": email,
                "is_requester": (u.id == requester_user_id),
            })

        return {
            "found": True,
            "tenant_id": tenant_id,
            "tenant_name": (tenant.tenant_name if tenant else None),
            "users": users_out,
            "total": total,
            "has_more": has_more,
        }
    finally:
        session.close()


def find_user_in_system(query: str, requester_user_id: int | None = None) -> dict:
    """
    Multi-source search uživatele v aktuálním tenantu requestera.

    Hledá napříč:
      - users.first_name / last_name / short_name / legal_name
      - user_aliases (globální přezdívky)
      - user_tenant_aliases (jen v aktuálním tenantu requestera)
      - user_contacts (email / phone)

    Search: tokenizovaný, case + accent insensitive substring.
    Každý token musí matchnout ALESPOŇ jedno pole některé entity daného usera.

    Scope: jen aktivní členové aktuálního tenantu requestera.
    Pokud requester nemá tenant, vrací prázdný list.

    Vrací:
      {
        "found": bool,
        "candidates": [
          {
            "user_id": int,
            "full_name": str,
            "display_name": str | None,    # z user_tenant_profiles aktuálního tenantu
            "role_label": str | None,      # job role v aktuálním tenantu
            "preferred_email": str | None,
            "preferred_phone": str | None, # primary phone z user_contacts, pro send_sms
            "matched_via": str             # debug — jak jsme ho našli
          }, ...
        ],
        "total_matches": int,              # může být > len(candidates) když has_more
        "has_more": bool,                  # True pokud existují další za limitem
        "query": str,
      }
    """
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import (
        User, UserAlias, UserContact, UserTenant,
        UserTenantProfile, UserTenantAlias,
    )

    query_clean = (query or "").strip()
    if not query_clean:
        return {"found": False, "candidates": [], "total_matches": 0, "has_more": False, "query": query}

    tokens = [t for t in query_clean.split() if t]
    if not tokens:
        return {"found": False, "candidates": [], "total_matches": 0, "has_more": False, "query": query}
    # Phase 22.2 (29.4.2026): Minimum 3 znaky pro fuzzy substring match.
    # Krátké tokens (1-2 znaky, např. "23") matchnou v phone/email
    # substringem -- velmi false positive (gotcha #23). Lepší filtrovat.
    tokens_bare = [_strip_diacritics(t) for t in tokens if len(t) >= 3]
    if not tokens_bare:
        # Vsechny tokens kratsi nez 3 znaky -- pravdepodobne ID lookup intent.
        return {
            "found": False, "candidates": [], "total_matches": 0,
            "has_more": False, "query": query,
            "hint": "Krátký query (< 3 znaky). Pro user_id lookup pošli číslo přes user_id parametr toolu, ne přes query.",
        }

    session = get_core_session()
    try:
        # Zjisti tenant requestera
        tenant_id: int | None = None
        if requester_user_id:
            req_user = session.query(User).filter_by(id=requester_user_id).first()
            if req_user:
                tenant_id = req_user.last_active_tenant_id
                if tenant_id is None:
                    ut = (
                        session.query(UserTenant)
                        .filter_by(user_id=requester_user_id, membership_status="active")
                        .order_by(UserTenant.id.asc())
                        .first()
                    )
                    if ut:
                        tenant_id = ut.tenant_id

        if tenant_id is None:
            return {
                "found": False, "candidates": [], "total_matches": 0,
                "has_more": False, "query": query,
            }

        # Aktivní členové tenantu (vč. requestera; on sebe může vyloučit ve volajícím)
        tenant_user_rows = (
            session.query(UserTenant)
            .filter_by(tenant_id=tenant_id, membership_status="active")
            .all()
        )
        tenant_user_ids = [ut.user_id for ut in tenant_user_rows]
        if not tenant_user_ids:
            return {
                "found": False, "candidates": [], "total_matches": 0,
                "has_more": False, "query": query,
            }
        # Mapa user_id → user_tenant_id (pro profil/aliasy)
        ut_by_user = {ut.user_id: ut.id for ut in tenant_user_rows}

        # Načti usery (jen active/pending — disabled je archiv)
        users = (
            session.query(User)
            .filter(User.id.in_(tenant_user_ids), User.status.in_(("active", "pending")))
            .all()
        )

        # Načti všechny vyhledávací pole pro daný set userů
        global_aliases = (
            session.query(UserAlias)
            .filter(UserAlias.user_id.in_(tenant_user_ids), UserAlias.status == "active")
            .all()
        )
        global_aliases_by_user: dict[int, list[str]] = {}
        for a in global_aliases:
            global_aliases_by_user.setdefault(a.user_id, []).append(a.alias_value)

        ut_ids = list(ut_by_user.values())
        tenant_aliases = (
            session.query(UserTenantAlias)
            .filter(UserTenantAlias.user_tenant_id.in_(ut_ids), UserTenantAlias.status == "active")
            .all()
            if ut_ids else []
        )
        tenant_aliases_by_ut: dict[int, list[str]] = {}
        for a in tenant_aliases:
            tenant_aliases_by_ut.setdefault(a.user_tenant_id, []).append(a.alias_value)

        contacts = (
            session.query(UserContact)
            .filter(UserContact.user_id.in_(tenant_user_ids), UserContact.status == "active")
            .all()
        )
        emails_by_user: dict[int, str] = {}
        phones_by_user: dict[int, str] = {}
        all_contact_values_by_user: dict[int, list[str]] = {}
        for c in contacts:
            all_contact_values_by_user.setdefault(c.user_id, []).append(c.contact_value)
            if c.contact_type == "email":
                if c.is_primary or c.user_id not in emails_by_user:
                    emails_by_user[c.user_id] = c.contact_value
            elif c.contact_type == "phone":
                if c.is_primary or c.user_id not in phones_by_user:
                    phones_by_user[c.user_id] = c.contact_value

        # Profile (display_name, role_label) pro tenant
        profiles = (
            session.query(UserTenantProfile)
            .filter(UserTenantProfile.user_tenant_id.in_(ut_ids))
            .all()
            if ut_ids else []
        )
        profile_by_ut = {p.user_tenant_id: p for p in profiles}

        # Postupně skóruj všechny usery
        matches: list[dict] = []
        for user in users:
            ut_id = ut_by_user.get(user.id)
            profile = profile_by_ut.get(ut_id) if ut_id else None
            display_name = profile.display_name if profile else None

            # Sber všechna search-pole
            name_fields = [
                user.first_name, user.last_name, user.short_name, user.legal_name,
                display_name,
            ]
            name_fields = [f for f in name_fields if f]
            g_aliases = global_aliases_by_user.get(user.id, [])
            t_aliases = tenant_aliases_by_ut.get(ut_id, []) if ut_id else []
            user_contact_values = all_contact_values_by_user.get(user.id, [])

            all_searchable = name_fields + g_aliases + t_aliases + user_contact_values
            all_bare = [_strip_diacritics(s) for s in all_searchable]

            # Každý token musí matchnout aspoň jedno pole
            def _matches() -> tuple[bool, str]:
                hit_field = ""
                for tok_bare in tokens_bare:
                    found_in = None
                    for orig, bare in zip(all_searchable, all_bare):
                        if tok_bare in bare:
                            found_in = orig
                            break
                    if found_in is None:
                        return False, ""
                    if not hit_field:
                        hit_field = found_in
                return True, hit_field

            ok, matched_field = _matches()
            if not ok:
                continue

            # Sestav výsledek
            full_name = " ".join(filter(None, [user.first_name, user.last_name])).strip() or user.legal_name or f"User #{user.id}"
            matches.append({
                "user_id": user.id,
                "full_name": full_name,
                "display_name": display_name,
                "role_label": profile.role_label if profile else None,
                "preferred_email": emails_by_user.get(user.id),
                "preferred_phone": phones_by_user.get(user.id),
                "matched_via": matched_field,
            })

        total_matches = len(matches)
        # Lehké preferovat ty, jejichž jméno/alias matchnul (ne email)
        # Ale pro MVP nech řazení podle ID (deterministicky).
        candidates = matches[:FIND_USER_MAX_CANDIDATES]
        has_more = total_matches > FIND_USER_MAX_CANDIDATES

        return {
            "found": total_matches > 0,
            "candidates": candidates,
            "total_matches": total_matches,
            "has_more": has_more,
            "query": query,
        }
    finally:
        session.close()


def invite_user_to_strategie(
    email: str,
    invited_by_user_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    gender: str | None = None,
    name: str | None = None,  # legacy, zachováno kvůli starým voláním
) -> dict:
    from modules.auth.application.invitation_service import create_invitation
    from modules.notifications.application.email_service import send_invitation_email
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import User

    # Legacy: pokud přišlo jen `name` a nemáme first_name, zkus to rozparsovat.
    if not first_name and name:
        parts = [p for p in name.strip().split() if p]
        if parts:
            first_name = parts[0]
            if len(parts) > 1 and not last_name:
                last_name = " ".join(parts[1:])

    # Normalizace genderu
    g = (gender or "").strip().lower() or None
    if g not in ("male", "female", None):
        g = None

    session = get_core_session()
    try:
        inviter = session.query(User).filter_by(id=invited_by_user_id).first()
        inviter_name = " ".join(filter(None, [inviter.first_name, inviter.last_name])) if inviter else "Člen týmu"
        tenant_id = inviter.last_active_tenant_id if inviter else 1
    finally:
        session.close()

    try:
        token = create_invitation(
            email=email.strip().lower(),
            invited_by_user_id=invited_by_user_id,
            tenant_id=tenant_id or 1,
            first_name=first_name,
            last_name=last_name,
            gender=g,
        )
        sent = send_invitation_email(
            to=email,
            invited_by=inviter_name,
            token=token,
            invitee_first_name=first_name,
            invitee_gender=g,
        )
        return {
            "success": True,
            "email": email,
            "email_sent": sent,
            "first_name": first_name,
            "last_name": last_name,
        }
    except Exception as e:
        # Specialni typove vyjimky z invitation_service vraci se pekne strukturou,
        # aby AI mohla zformulovat smysluplnou odpoved (napr. nabidnout pridani
        # do projektu misto pozvani).
        from modules.auth.application.invitation_service import (
            UserAlreadyActive, UserDisabled,
        )
        if isinstance(e, UserAlreadyActive):
            return {
                "success": False,
                "email": email,
                "error": str(e),
                "reason": "already_active",
                "existing_user_id": e.user_id,
                "existing_full_name": e.full_name,
            }
        if isinstance(e, UserDisabled):
            return {
                "success": False,
                "email": email,
                "error": str(e),
                "reason": "disabled",
                "existing_user_id": e.user_id,
                "existing_status": e.status,
            }
        return {"success": False, "email": email, "error": str(e)}


def _strip_diacritics(s: str) -> str:
    """Převede 'Klára' → 'klara' pro accent-insensitive hledání."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def get_user_default_persona_name(user_id: int) -> str | None:
    """
    Vrátí název uživatelovy výchozí persony (digitálního dvojčete).

    Konvence: persona pojmenovaná podle first_name uživatele —
    např. Marti Pašek → persona 'Marti-AI', Klára Vlková → 'Klára-AI'.
    Hledání je accent-insensitive. Pokud nic nenajde, vrátí None.
    """
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import Persona, User

    session = get_core_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user or not user.first_name:
            return None

        first_name_bare = _strip_diacritics(user.first_name)
        personas = session.query(Persona).all()

        # 1. preferuj personu, jejíž base-name (bez -AI) přesně odpovídá first_name
        for p in personas:
            base = _strip_diacritics(p.name).replace("-ai", "").strip()
            if base == first_name_bare:
                return p.name

        # 2. fallback: substring shoda v obou směrech
        for p in personas:
            base = _strip_diacritics(p.name).replace("-ai", "").strip()
            if first_name_bare and (first_name_bare in base or base in first_name_bare):
                return p.name

        return None
    finally:
        session.close()


def switch_persona_for_user(query: str, conversation_id: int) -> dict:
    """
    Přepne aktivní personu v konverzaci.
    Hledá personu podle jména v css_db.
    Hledání je case- a accent-insensitive ('klara' = 'Klára').
    Pokud nenajde personu, vrátí found=False.
    """
    from core.database_core import get_core_session
    from core.database_data import get_data_session
    from modules.core.infrastructure.models_core import Persona
    from modules.core.infrastructure.models_data import Conversation

    query_lower = query.strip().lower()
    query_bare = _strip_diacritics(query_lower)

    # Hledej personu. Hledání je accent-insensitive + case-insensitive,
    # s obousměrným substringem a prefixovou shodou pro české pády.
    core_session = get_core_session()
    try:
        personas = core_session.query(Persona).all()

        # Předpočítej bare (bez diakritiky) názvy pro každou personu
        persona_keys = []
        for p in personas:
            name_bare = _strip_diacritics(p.name)
            base_bare = name_bare.replace("-ai", "").strip()
            persona_keys.append((p, name_bare, base_bare))

        matched = None

        # 1. krok: přesná shoda
        for p, name_bare, base_bare in persona_keys:
            if name_bare == query_bare or base_bare == query_bare:
                matched = p
                break

        # 2. krok: substring v obou směrech
        if matched is None:
            for p, name_bare, base_bare in persona_keys:
                if query_bare in name_bare or name_bare in query_bare:
                    matched = p
                    break
                if base_bare and (query_bare in base_bare or base_bare in query_bare):
                    matched = p
                    break

        # 3. krok: prefixová shoda na alespoň 4 znaky
        # (pokrývá české pády jako "Kláře"/"Kláru" → "Klára")
        if matched is None:
            for p, name_bare, base_bare in persona_keys:
                if not base_bare:
                    continue
                common = 0
                for a, b in zip(base_bare, query_bare):
                    if a == b:
                        common += 1
                    else:
                        break
                if common >= 4 and common >= min(len(base_bare), len(query_bare)) - 2:
                    matched = p
                    break

        if not matched:
            return {"found": False, "query": query}

        persona_id = matched.id
        persona_name = matched.name
    finally:
        core_session.close()

    # Aktualizuj active_persona_id v konverzaci
    data_session = get_data_session()
    try:
        conversation = data_session.query(Conversation).filter_by(id=conversation_id).first()
        if conversation:
            conversation.active_agent_id = persona_id
            data_session.commit()
        return {"found": True, "persona_id": persona_id, "persona_name": persona_name}
    finally:
        data_session.close()


# ── TENANT SWITCH ──────────────────────────────────────────────────────────

def switch_tenant_for_user(user_id: int, query: str) -> dict:
    """
    Přepne aktivní tenant uživatele.

    Vyhledávání:
      1. přesná shoda tenant_code (case + accent insensitive)
      2. substring v tenant_code
      3. substring v tenant_name (accent insensitive)
    Vrátí jen tenanty, kde má user aktivní `user_tenants` membership.

    Vrací:
      {"found": True,  "tenant_id": int, "tenant_name": str, "tenant_code": str,
                       "already_active": bool}
      {"found": False, "query": str}
      {"found": False, "ambiguous": True, "candidates": [
          {"tenant_id", "tenant_name", "tenant_code"}, ...
      ]}
    """
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import User, Tenant, UserTenant

    query_clean = (query or "").strip()
    if not query_clean:
        return {"found": False, "query": query}
    query_bare = _strip_diacritics(query_clean)

    session = get_core_session()
    try:
        # Aktivní tenanty, jichž je user členem
        rows = (
            session.query(Tenant)
            .join(UserTenant, UserTenant.tenant_id == Tenant.id)
            .filter(
                UserTenant.user_id == user_id,
                UserTenant.membership_status == "active",
                Tenant.status == "active",
            )
            .all()
        )

        if not rows:
            return {"found": False, "query": query, "no_memberships": True}

        # Předpočítej bare (lowercase + bez diakritiky) klíče
        tenant_keys = []
        for t in rows:
            code_bare = _strip_diacritics(t.tenant_code or "")
            name_bare = _strip_diacritics(t.tenant_name or "")
            tenant_keys.append((t, code_bare, name_bare))

        # 1. krok: přesná shoda code
        exact = [t for t, code, _ in tenant_keys if code and code == query_bare]
        if len(exact) == 1:
            return _tenant_switch_apply(session, user_id, exact[0])
        if len(exact) > 1:
            return _ambiguous(exact)

        # 2. krok: substring v code
        code_match = [t for t, code, _ in tenant_keys if code and (query_bare in code or code in query_bare)]
        if len(code_match) == 1:
            return _tenant_switch_apply(session, user_id, code_match[0])
        if len(code_match) > 1:
            return _ambiguous(code_match)

        # 3. krok: substring v name
        name_match = [t for t, _, name in tenant_keys if name and (query_bare in name or name in query_bare)]
        if len(name_match) == 1:
            return _tenant_switch_apply(session, user_id, name_match[0])
        if len(name_match) > 1:
            return _ambiguous(name_match)

        return {"found": False, "query": query}
    finally:
        session.close()


def _ambiguous(tenants) -> dict:
    return {
        "found": False,
        "ambiguous": True,
        "candidates": [
            {
                "tenant_id": t.id,
                "tenant_name": t.tenant_name,
                "tenant_code": t.tenant_code,
            }
            for t in tenants
        ],
    }


def _tenant_switch_apply(session, user_id: int, tenant) -> dict:
    """Provede update users.last_active_tenant_id, vrátí success dict."""
    from modules.core.infrastructure.models_core import User

    user = session.query(User).filter_by(id=user_id).first()
    if not user:
        return {"found": False, "query": tenant.tenant_name, "error": "user not found"}

    already_active = user.last_active_tenant_id == tenant.id
    if not already_active:
        user.last_active_tenant_id = tenant.id
        session.commit()

    return {
        "found": True,
        "tenant_id": tenant.id,
        "tenant_name": tenant.tenant_name,
        "tenant_code": tenant.tenant_code,
        "already_active": already_active,
    }


def get_user_default_tenant_id(user_id: int) -> int | None:
    """
    Najde uživatelův výchozí (personal) tenant — preferuje:
      1. tenant_type='personal' kde je user owner
      2. první aktivní user_tenants záznam (fallback)

    Vrací tenant_id nebo None.
    """
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_core import Tenant, UserTenant

    session = get_core_session()
    try:
        # Preferuj personal tenant kde je user owner
        personal = (
            session.query(Tenant)
            .filter_by(tenant_type="personal", owner_user_id=user_id, status="active")
            .first()
        )
        if personal:
            return personal.id

        # Fallback: první aktivní membership
        ut = (
            session.query(UserTenant)
            .filter_by(user_id=user_id, membership_status="active")
            .order_by(UserTenant.id.asc())
            .first()
        )
        return ut.tenant_id if ut else None
    finally:
        session.close()


# ============================================================================
# Faze 10c: AI tool review_my_calls -- agregat LLM volani (tokens, cost).
# ============================================================================

def review_my_llm_calls(
    *,
    user_id: int | None,
    conversation_id: int,
    scope: str = "today",
    aggregate_by: str = "kind",
    filter_kind: str | None = None,
    filter_tenant: str | None = None,
) -> str:
    """
    Vrati agregat LLM volani (tokens, cena, latence) podle zadanych filtru.

    Vraci lidsky citelny string -- AI ho prevezme do odpovedi uzivateli.
    Ethical: zadne raw request/response JSONy. Ty jsou viditelne jen v
    Dev View modalu v UI (admin zapne).
    """
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import func
    from core.database_data import get_data_session
    from core.database_core import get_core_session
    from modules.core.infrastructure.models_data import LlmCall, Conversation
    from modules.core.infrastructure.models_core import User, Tenant

    # 1) Normalize params
    if scope not in ("today", "week", "month", "all"):
        scope = "today"
    if aggregate_by not in ("kind", "day", "tenant", "user", "persona", "model"):
        aggregate_by = "kind"

    # 2) Zjisti aktualni tenant z konverzace + is_parent z usera
    current_tenant_id: int | None = None
    ds_conv = get_data_session()
    try:
        _conv = ds_conv.query(Conversation).filter_by(id=conversation_id).first()
        if _conv:
            current_tenant_id = _conv.tenant_id
    finally:
        ds_conv.close()

    is_parent = False
    if user_id:
        cs = get_core_session()
        try:
            _u = cs.query(User).filter_by(id=user_id).first()
            is_parent = bool(_u and _u.is_marti_parent)
        finally:
            cs.close()

    # 3) Build query
    ds = get_data_session()
    try:
        q = ds.query(LlmCall)

        # Casovy filtr
        intervals = {
            "today": timedelta(days=1),
            "week": timedelta(days=7),
            "month": timedelta(days=30),
            "all": None,
        }
        if intervals[scope]:
            since = datetime.now(timezone.utc) - intervals[scope]
            q = q.filter(LlmCall.created_at >= since)

        # Tenant filter
        tenant_label = "current"
        if filter_tenant is None or filter_tenant.lower() == "current":
            if current_tenant_id is not None:
                q = q.filter(LlmCall.tenant_id == current_tenant_id)
                tenant_label = f"current (id={current_tenant_id})"
            else:
                tenant_label = "current (none -- conversation nema tenant)"
        elif filter_tenant.lower() == "all":
            if not is_parent:
                return (
                    "Jen rodice (is_marti_parent) mohou pouzit filter_tenant='all'. "
                    "Zkus filter_tenant='current' nebo konkretni nazev tenantu."
                )
            tenant_label = "all (cross-tenant)"
        else:
            cs = get_core_session()
            try:
                t = (
                    cs.query(Tenant)
                    .filter(Tenant.tenant_name.ilike(f"%{filter_tenant}%"))
                    .first()
                )
                if not t:
                    return f"Tenant '{filter_tenant}' neznamy. Zkus 'current' nebo 'all'."
                if not is_parent and current_tenant_id != t.id:
                    return (
                        f"Nemuzes filtrovat tenant '{t.tenant_name}' (nejsi rodic a "
                        f"neni aktualni). Zkus filter_tenant='current'."
                    )
                q = q.filter(LlmCall.tenant_id == t.id)
                tenant_label = f"{t.tenant_name} (id={t.id})"
            finally:
                cs.close()

        # Kind filter
        if filter_kind:
            q = q.filter(LlmCall.kind == filter_kind)

        # Grouping column
        group_map = {
            "kind": LlmCall.kind,
            "model": LlmCall.model,
            "tenant": LlmCall.tenant_id,
            "user": LlmCall.user_id,
            "persona": LlmCall.persona_id,
            "day": func.date_trunc("day", LlmCall.created_at),
        }
        group_col = group_map[aggregate_by]

        rows = (
            q.with_entities(
                group_col.label("grp"),
                func.count(LlmCall.id).label("calls"),
                func.sum(LlmCall.prompt_tokens).label("in_tok"),
                func.sum(LlmCall.output_tokens).label("out_tok"),
                func.sum(LlmCall.cost_usd).label("cost"),
                func.avg(LlmCall.latency_ms).label("avg_ms"),
            )
            .group_by(group_col)
            .order_by(func.sum(LlmCall.cost_usd).desc().nullslast())
            .limit(25)
            .all()
        )
    finally:
        ds.close()

    if not rows:
        return (
            f"Zadne LLM volani v rozsahu scope='{scope}', tenant={tenant_label}"
            + (f", kind='{filter_kind}'" if filter_kind else "")
            + "."
        )

    # 4) Format output
    lines = [
        f"=== LLM usage agregat ===",
        f"  scope         : {scope}",
        f"  tenant        : {tenant_label}",
        f"  kind filter   : {filter_kind or '(vsechny)'}",
        f"  aggregate_by  : {aggregate_by}",
        "",
        f"{'GROUP':<28} {'CALLS':>6} {'TOKENS':>10} {'COST USD':>11} {'AVG MS':>7}",
        "-" * 66,
    ]
    total_cost = 0.0
    total_calls = 0
    total_tokens = 0
    for r in rows:
        g = str(r.grp if r.grp is not None else "(none)")[:26]
        calls = int(r.calls or 0)
        in_t = int(r.in_tok or 0)
        out_t = int(r.out_tok or 0)
        tokens = in_t + out_t
        cost = float(r.cost or 0.0)
        avg = int(r.avg_ms or 0)
        total_cost += cost
        total_calls += calls
        total_tokens += tokens
        lines.append(f"{g:<28} {calls:>6} {tokens:>10} {cost:>10.4f}  {avg:>7}")
    lines.append("-" * 66)
    lines.append(
        f"{'TOTAL':<28} {total_calls:>6} {total_tokens:>10} {total_cost:>10.4f}"
    )
    return "\n".join(lines)
