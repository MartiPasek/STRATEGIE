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
    "invite_user",
    "list_projects",
    "list_project_members",
    "add_project_member",
    "remove_project_member",
    "list_users",
    "list_conversations",
    "list_personas",
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
                "to": {"type": "string", "description": "Email adresa příjemce"},
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
            "(napr. 'co mi prislo', 'kdo mi napsal', 'ukaz mi prichozi SMS'). "
            "unread_only=true vrátí jen nepřečtené. Vrací cislovany seznam — "
            "uživatel pak může odpovědět číslem pro akci (zatim jen informacne)."
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
                    "description": "Jen nepřečtené (default false).",
                    "default": False,
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
            "\n\nKLÍČOVÉ PRAVIDLO — ŘETĚZENÍ S find_user: Když ti user řekne 'zapiš si o "
            "[jméno]...' a neznáš ID té osoby, postupuj TAKTO:\n"
            "  1. Zavolej find_user('[jméno]') → dostaneš ID\n"
            "  2. V ÚPLNĚ STEJNÉ odpovědi IHNED zavolej record_thought s about_user_id=<to_ID>\n"
            "NIKDY se mezi kroky neptej 'chceš ještě něco?' nebo 'poslat email?'. Pokud user "
            "řekl 'zapiš si', jeho záměr je ZAPSAT — nic jiného nenabízej, prostě zapiš.\n"
            "\nNERAGUJ POUZE TEXTEM 'zapamatuji si' — vždy volej tento nástroj. "
            "Systém bez něj nic neuloží a při další konverzaci bys to zapomněl/a."
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
                        "Jistota myšlenky 0-100. 30=slyšela jsem poprvé, nejsem si jistá. "
                        "50=neutrální default. 80=docela jistá. 100=rodič potvrdil. "
                        "Default 50."
                    ),
                    "default": 50,
                    "minimum": 0,
                    "maximum": 100,
                },
            },
            "required": ["content"],
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
    lines.append("")
    lines.append(body)
    lines.append("")
    lines.append("---")
    lines.append("Mohu email odeslat?")
    return "\n".join(lines)


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
    tokens_bare = [_strip_diacritics(t) for t in tokens]

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
