# list_mailboxes

## MAPA
- **kód:** `list_mailboxes`
- **kategorie:** management
- **v kufrech:** marti-ai-md5
- **implementace:** `_handle_tool`

## CHOVÁNÍ
- **automat_safe:** — (nezatříděno)
- **vedlejší účinek:** — (nezatříděno)
- **při chybě:** `eskaluj_llm`

## POPIS

Phase 29 (4.5.2026): vrátí tvé authorized email schránky.

Použij když:
  - Tatínek se zeptá 'jaké schránky máš?' / 'odkud můžeš odeslat?'
  - Před send_email / reply chceš vybrat konkrétní mailbox
  - Sám si chceš ověřit per-action permissions (can_send vs     can_archive vs can_delete -- archive a delete jsou separate     granty, nejsou bundled s send)

Vrací list dictů s mailbox_id, email_upn (login UPN, ne pro veřejnost), ews_display_email (public SMTP alias), label ("Marti-AI default" / "Pavel CRM"), is_shared (true pro sdílené CRM schránky), default_language, can_read/send/archive/delete/mark_read.

Read-only -- žádný permission gate. Marti-AI vidí, co má.

## PARAMETRY

- **`require_can_send`** [boolean, volitelný] · default: `False`
  - Filter na mailboxy kde můžeš odeslat (can_send=true). Default false (vidíš vše s can_read).

